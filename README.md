# Payment Gateway Backend (PayU & Easebuzz)

## Project Overview

This project is a Django REST Framework based payment gateway backend that integrates multiple payment providers and provides secure payment processing APIs.

### Supported Payment Gateways

* PayU Payment Gateway
* Easebuzz Payment Gateway

### Key Features

* Payment initiation APIs
* Secure hash generation and validation
* Payment success/failure callback handling
* Transaction status tracking
* PostgreSQL database integration
* PDF receipt generation
* Transaction history storage
* Input sanitization and validation
* Environment-based configuration

---

## Environment Setup

### 1. Create and Activate Virtual Environment

#### Windows

```bash
python -m venv venv
.\venv\Scripts\activate
```

#### Linux / Mac

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 2. Install Dependencies

Install all required packages:

```bash
pip install -r requirements.txt
```

If requirements.txt is not available:

```bash


```

---

### 3. Install Additional Packages

PDF Receipt Generation:

```bash
pip install reportlab
```

---

## Database Setup

This project uses PostgreSQL.

Create database:

```sql
CREATE DATABASE payment_gateway;
```

---

## Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## Start Development Server

```bash
python manage.py runserver
```

Default URL:

```text
http://127.0.0.1:8000/
```

---

## Test API

Health Check Endpoint:

```http
GET /api/test/
```

Expected Response:

```json
{
    "message": "Payment API is working ✅"
}
```

---

## Project Structure

```text
Payment/
│
├── App/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── Payment/
│   ├── models/
│   ├── serializers/
│   ├── views/
│   ├── urls/
│   └── utils/
│
├── media/
├── requirements.txt
├── manage.py
└── README.md
```

---

## Environment Variables

Create a `.env` file and configure:

```env
SECRET_KEY=your_secret_key
DEBUG=True

DB_NAME=payment_gateway
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432

# Frontend URL
FRONTEND_URL=http://localhost:5173

# PayU
PAYU_KEY=xxxxxxxx
PAYU_SALT=xxxxxxxx
PAYU_URL=https://test.payu.in
PAYU_SUCCESS_URL=http://127.0.0.1:8000/api/payment/success/
PAYU_FAILURE_URL=http://127.0.0.1:8000/api/payment/failure/
PAYU_MIN_AMOUNT=30

# Easebuzz
EASEBUZZ_ENV=test
EASEBUZZ_MERCHANT_KEY=xxxxxxxx
EASEBUZZ_SALT=xxxxxxxx
EASEBUZZ_TEST_URL=https://testpay.easebuzz.in
EASEBUZZ_PROD_URL=https://pay.easebuzz.in
EASEBUZZ_CALLBACK_URL=http://127.0.0.1:8000/api/easebuzz_callback/
EASEBUZZ_MIN_AMOUNT=30
```

---

## Payment Flow

### Step 1

Frontend submits customer details:

* Loan Account Number
* Customer Name
* City
* Email
* Mobile Number
* Amount

### Step 2

User clicks:

```text
Process To Pay
```

### Step 3

Frontend displays available payment options:

```text
PayU
Easebuzz
```

### Step 4

Selected gateway API generates payment URL.

### Step 5

User completes payment.

### Step 6

Gateway calls backend callback URL.

### Step 7

Backend:

* Verifies hash
* Updates transaction status
* Stores payment details
* Redirects to frontend success/failure page

### Step 8

User downloads PDF receipt.

---

## Receipt Download

Receipt API:

```http
GET /api/receipt/<txnid>/
```

Features:

* Transaction ID
* Loan Account Number
* Customer Name
* Amount
* Gateway Name
* Payment Status
* Date & Time
* PDF Download

---

## Security Features

* SHA512 Hash Validation
* Callback Verification
* Input Sanitization
* Email Validation
* Mobile Number Validation
* Transaction ID Validation
* Environment Variable Protection
* SQL Injection Protection (ORM)
* XSS Prevention via Sanitizer

---

## Useful Commands

```bash
python manage.py makemigrations

python manage.py migrate

python manage.py createsuperuser

python manage.py runserver

pip freeze > requirements.txt
```

---

## API Endpoints

### Test API

```http
GET /api/test/
```

### PayU Payment

```http
POST /api/payment/
```

### Easebuzz Payment

```http
POST /api/easebuzz_payment/
```

### Receipt Download

```http
GET /api/receipt/<txnid>/
```

---

## Notes

* Keep `.env` file private.
* Never commit production credentials.
* Use HTTPS in production.
* Update callback URLs before deployment.

---

## Copyright

© 2026 All Rights Reserved

Developed for Berar Finance Limited.
