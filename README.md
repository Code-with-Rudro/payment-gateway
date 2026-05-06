# 🚀 Razorpay Payment Gateway Integration using FastAPI

A secure and production-ready Payment Gateway API built using FastAPI and Razorpay.  
This project demonstrates how to integrate Razorpay payments, verify payment authenticity using HMAC SHA256 signature validation, and handle webhooks securely.

---

# 📌 Features

✅ Razorpay Payment Gateway Integration  
✅ Create Payment Orders  
✅ Secure Payment Verification  
✅ HMAC SHA256 Signature Authentication  
✅ Razorpay Webhook Support  
✅ Payment Details Fetch API  
✅ FastAPI Backend  
✅ CORS Middleware Support  
✅ Environment Variable Configuration  
✅ Structured Logging System  

---

# 🛠️ Tech Stack

- Python
- FastAPI
- Razorpay API
- Uvicorn
- Pydantic
- python-dotenv
- HMAC SHA256 Authentication

---

# 📂 Project Structure

```bash
payment-gateway/
│
├── main.py
├── .env
├── requirements.txt
└── README.md
```

---

# ⚙️ Installation

## 1️⃣ Clone the Repository

```bash
git clone https://github.com/Code-with-Rudro/payment-gateway.git
```

---

## 2️⃣ Navigate to Project Directory

```bash
cd payment-gateway
```

---

## 3️⃣ Create Virtual Environment

```bash
python -m venv venv
```

---

## 4️⃣ Activate Virtual Environment

### Windows

```bash
venv\Scripts\activate
```

### Linux/Mac

```bash
source venv/bin/activate
```

---

## 5️⃣ Install Dependencies

```bash
pip install fastapi uvicorn razorpay python-dotenv
```

---

# 🔑 Environment Variables

Create a `.env` file in the root directory and add:

```env
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxx
RAZORPAY_KEY_SECRET=xxxxxxxxxxxxxxxx
```

---

# ▶️ Run the Application

```bash
uvicorn main:app --reload --port 8000
```

Server will start on:

```bash
http://127.0.0.1:8000
```

---

# 📡 API Endpoints

---

## 🏠 Health Check

### GET `/`

Returns API status.

### Response

```json
{
  "message": "Razorpay Payment API is running 🚀"
}
```

---

## 💳 Create Payment Order

### POST `/create-order`

Creates a Razorpay payment order.

### Request Body

```json
{
  "amount": 499,
  "currency": "INR",
  "receipt": "receipt_001",
  "notes": {
    "user": "Rudra"
  }
}
```

### Response

```json
{
  "order_id": "order_xxxxx",
  "amount": 49900,
  "currency": "INR",
  "status": "created"
}
```

---

## ✅ Verify Payment

### POST `/verify-payment`

Verifies Razorpay payment signature securely using HMAC SHA256.

### Request Body

```json
{
  "razorpay_order_id": "order_xxxx",
  "razorpay_payment_id": "pay_xxxx",
  "razorpay_signature": "signature_here"
}
```

### Response

```json
{
  "status": "success",
  "message": "Payment verified and captured successfully"
}
```

---

## 🔔 Razorpay Webhook

### POST `/webhook`

Handles Razorpay webhook events securely.

Supported events:

- payment.captured
- payment.failed
- refund.created

---

## 📄 Fetch Payment Details

### GET `/payment/{payment_id}`

Fetch complete payment information.

### Example

```bash
GET /payment/pay_xxxxx
```

---

# 🔒 Security Features

- HMAC SHA256 Signature Verification
- Secure Payment Authentication
- Webhook Signature Validation
- Fraud Prevention Validation
- Environment Variable Protection

---

# 💳 Payment Flow

1. Frontend requests order creation
2. Backend creates Razorpay order
3. Razorpay Checkout opens
4. User completes payment
5. Frontend sends payment details
6. Backend verifies payment signature
7. Payment is authenticated successfully

---

# 📸 Future Improvements

- User Authentication
- Database Integration
- Payment History Dashboard
- Subscription Billing
- Email Notifications
- Admin Dashboard

---

# 🤝 Contributing

Contributions are welcome.  
Feel free to fork this repository and submit pull requests.

---

# 📄 License

This project is licensed under the MIT License.

---

# 👨‍💻 Developer

Developed by **Rudra Prasad Panigrahi**

GitHub: https://github.com/Code-with-Rudro

---
