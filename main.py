"""
FastAPI + Razorpay Payment Integration Backend
===============================================
Install dependencies:
    pip install fastapi uvicorn razorpay python-dotenv

Create a .env file:
    RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxx
    RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxxxxxxxxxxxx

Run:
    uvicorn main:app --reload --port 8000
"""

import hmac
import hashlib
import logging
from datetime import datetime

import razorpay
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os

# ─────────────────────────────────────────────
# Config & Setup
# ─────────────────────────────────────────────
load_dotenv()

RAZORPAY_KEY_ID     = os.getenv("RAZORPAY_KEY_ID", "YOUR_RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "YOUR_RAZORPAY_KEY_SECRET")

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

app = FastAPI(
    title="Razorpay Payment API",
    description="Secure payment integration using Razorpay",
    version="1.0.0"
)

# Allow your frontend origin (update in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Replace with ["http://127.0.0.1:5500"] etc. in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# Pydantic Schemas
# ─────────────────────────────────────────────
class CreateOrderRequest(BaseModel):
    amount: int = Field(..., gt=0, description="Amount in INR (e.g., 499 for ₹499)")
    currency: str = Field(default="INR", max_length=3)
    receipt: str = Field(default="receipt_001", max_length=40)
    notes: dict = Field(default_factory=dict)


class CreateOrderResponse(BaseModel):
    order_id: str
    amount: int
    currency: str
    receipt: str
    status: str
    razorpay_key_id: str


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class VerifyPaymentResponse(BaseModel):
    status: str
    message: str
    payment_id: str
    order_id: str


class WebhookPayload(BaseModel):
    event: str
    payload: dict


# ─────────────────────────────────────────────
# Helper: Verify Razorpay HMAC Signature
# ─────────────────────────────────────────────
def verify_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """
    Razorpay signs: HMAC-SHA256(order_id + "|" + payment_id, key_secret)
    """
    message = f"{order_id}|{payment_id}".encode()
    secret  = RAZORPAY_KEY_SECRET.encode()
    expected = hmac.new(secret, message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    return {"message": "Razorpay Payment API is running 🚀", "time": datetime.utcnow().isoformat()}


@app.post("/create-order", response_model=CreateOrderResponse, tags=["Payment"])
async def create_order(payload: CreateOrderRequest):
    """
    Step 1 — Create a Razorpay order.
    The frontend calls this endpoint to get an order_id before opening checkout.
    Amount is in INR (paise not required here; converted internally to paise).
    """
    try:
        amount_in_paise = payload.amount * 100  # Razorpay expects paise

        order_data = {
            "amount":   amount_in_paise,
            "currency": payload.currency,
            "receipt":  payload.receipt,
            "notes":    payload.notes,
            "payment_capture": 1  # Auto-capture
        }

        order = client.order.create(data=order_data)
        logger.info(f"Order created: {order['id']} | ₹{payload.amount}")

        return CreateOrderResponse(
            order_id=order["id"],
            amount=order["amount"],
            currency=order["currency"],
            receipt=order["receipt"],
            status=order["status"],
            razorpay_key_id=RAZORPAY_KEY_ID,  # Send key_id to frontend (safe)
        )

    except razorpay.errors.BadRequestError as e:
        logger.error(f"Razorpay BadRequest: {e}")
        raise HTTPException(status_code=400, detail=f"Razorpay error: {str(e)}")
    except Exception as e:
        logger.error(f"Create order failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create payment order")


@app.post("/verify-payment", response_model=VerifyPaymentResponse, tags=["Payment"])
async def verify_payment(payload: VerifyPaymentRequest):
    """
    Step 2 — Verify payment after Razorpay checkout success.
    The frontend sends back the 3 tokens from Razorpay's handler callback.
    We validate the HMAC signature to confirm the payment is authentic.
    """
    logger.info(f"Verifying payment: {payload.razorpay_payment_id}")

    is_valid = verify_signature(
        order_id=payload.razorpay_order_id,
        payment_id=payload.razorpay_payment_id,
        signature=payload.razorpay_signature
    )

    if not is_valid:
        logger.warning(f"Signature mismatch for order {payload.razorpay_order_id}")
        raise HTTPException(status_code=400, detail="Invalid payment signature — possible fraud attempt")

    # Optional: Fetch payment details from Razorpay for extra validation
    try:
        payment_details = client.payment.fetch(payload.razorpay_payment_id)
        logger.info(f"Payment verified ✓ | ID: {payment_details['id']} | Status: {payment_details['status']}")

        if payment_details["status"] != "captured":
            raise HTTPException(status_code=402, detail=f"Payment not captured. Status: {payment_details['status']}")

    except razorpay.errors.BadRequestError as e:
        raise HTTPException(status_code=400, detail=f"Could not fetch payment: {str(e)}")

    # ✅ At this point — payment is verified and captured.
    # TODO: Update your database, activate subscription, send email, etc.

    return VerifyPaymentResponse(
        status="success",
        message="Payment verified and captured successfully",
        payment_id=payload.razorpay_payment_id,
        order_id=payload.razorpay_order_id,
    )


@app.post("/webhook", tags=["Webhook"])
async def razorpay_webhook(request: Request):
    """
    Optional — Razorpay Webhook endpoint.
    Configure this URL in your Razorpay Dashboard → Webhooks.
    Handles async events like payment.captured, refund.created, etc.
    """
    body      = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    # Validate webhook signature
    expected = hmac.new(
        RAZORPAY_KEY_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        logger.warning("Webhook: Invalid signature")
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    import json
    event_data = json.loads(body)
    event_type = event_data.get("event")
    logger.info(f"Webhook received: {event_type}")

    # Handle events
    if event_type == "payment.captured":
        payment = event_data["payload"]["payment"]["entity"]
        logger.info(f"Webhook: Payment captured | {payment['id']} | ₹{payment['amount'] // 100}")
        # TODO: Update DB, activate subscription, etc.

    elif event_type == "payment.failed":
        payment = event_data["payload"]["payment"]["entity"]
        logger.error(f"Webhook: Payment failed | {payment['id']}")
        # TODO: Notify user, retry logic, etc.

    elif event_type == "refund.created":
        refund = event_data["payload"]["refund"]["entity"]
        logger.info(f"Webhook: Refund created | {refund['id']} | ₹{refund['amount'] // 100}")
        # TODO: Update DB, notify user, etc.

    return {"status": "ok"}


@app.get("/payment/{payment_id}", tags=["Payment"])
async def get_payment_details(payment_id: str):
    """
    Fetch full details of a payment (for admin/dashboard use).
    """
    try:
        payment = client.payment.fetch(payment_id)
        return {
            "id":       payment["id"],
            "order_id": payment["order_id"],
            "amount":   payment["amount"] / 100,
            "currency": payment["currency"],
            "status":   payment["status"],
            "method":   payment["method"],
            "email":    payment.get("email"),
            "contact":  payment.get("contact"),
            "captured": payment["captured"],
            "created_at": datetime.utcfromtimestamp(payment["created_at"]).isoformat()
        }
    except razorpay.errors.BadRequestError as e:
        raise HTTPException(status_code=404, detail=f"Payment not found: {str(e)}")


# ─────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
