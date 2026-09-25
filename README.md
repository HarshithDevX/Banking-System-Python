# Apex Banking System - Full-Stack Web & Core Engine

A portfolio-quality full-stack banking application built with **Python**, **Flask**, **SQLite**, and modern **HTML5/CSS3/JavaScript**.

This project modernizes a classic console-based banking simulation into a responsive, secure, and production-ready web application while preserving the original core logic for evaluation and reference.

---

## Architecture Overview

```text
Banking-System/
│
├── app.py                  # Flask Application Controller & Route Handlers
├── database.py             # SQLite Persistence Layer & Banking Operations Engine
├── banking_system.py       # Original Console Application (Preserved for Reference)
├── requirements.txt        # Python Dependencies
├── render.yaml             # Render Cloud Deployment Blueprint
├── README.md               # Comprehensive Project Documentation
├── .gitignore              # Git Ignore Rules
├── .env.example            # Environment Configuration Template
│
├── templates/              # Jinja2 Reusable HTML5 Templates
│   ├── base.html           # Master Layout (Navigation, Flash Stack, Responsive Shell)
│   ├── login.html          # Authentication Portal
│   ├── register.html       # Account Registration with 6-digit Acc Auto-Generation
│   ├── register_success.html # Registration Confirmation with Generated Account ID
│   ├── dashboard.html      # Account Dashboard (Balance Card, Quick Actions, Recent Txns)
│   ├── deposit.html        # Fund Ingestion with Preset Amount Chips
│   ├── withdraw.html       # Cash Withdrawal with Balance Verification
│   ├── transfer.html       # Atomic Inter-Account Fund Transfer
│   ├── transactions.html   # Full Statement Ledger with Print Support
│   └── change_pin.html     # PIN Modification with Verification & Hashing
│
├── static/
│   ├── css/
│   │   └── style.css       # Clean, Executive Banking Theme (Responsive, No Framework Bloat)
│   └── js/
│       └── script.js       # Client Interactivity (Auto-dismiss Alerts, Presets, Validation)
│
└── database/
    └── banking.db          # Auto-Generated SQLite Database (Git Ignored)
```

---

## Core Features

- **Automated Account Provisioning**: Generates unique, non-colliding 6-digit account numbers automatically upon registration.
- **Secure PIN Encryption**: PINs are never stored in plain text. Hashed using `werkzeug.security` (`generate_password_hash`, `check_password_hash`).
- **Session-Based Authentication**: Protected banking routes guarded by `@login_required` decorators and HTTP-only session cookies.
- **Real-Time Financial Dashboard**:
  - Total available balance card with currency formatting (₹).
  - Linked phone number and account verification status.
  - Quick action links to all banking operations.
  - Recent transaction ledger (last 5 entries).
- **Deposit Operations**: Instant balance credits with positive amount validation and timestamped ledger records.
- **Withdrawal Engine**: Verifies sufficient available funds, rejects overdrafts, updates balance atomically.
- **Inter-Account Transfers**:
  - Atomic database transactions ensure sender is debited and receiver is credited simultaneously.
  - Prevents transfers to self or non-existent accounts.
  - Creates dual ledger entries for both parties.
- **Audit Ledger & Statement**:
  - Chronological transaction log (newest first).
  - Categorized badges for Credit, Debit, and Transfers.
  - Built-in statement printing capability.
- **PIN Management**: Allows users to change their secret PIN after confirming their current PIN.
- **Dual Mode**:
  - **Web Application**: Run `python app.py` for the modern browser UI.
  - **Console Application**: Run `python banking_system.py` for the terminal CLI.

---

## Security & Reliability Design

1. **Password/PIN Hashing**: Implements cryptographic salted hashing (`scrypt` / `pbkdf2:sha256`) via Werkzeug. Plaintext PINs are never persisted or exposed.
2. **Session Security**: Server-side session authentication prevents unauthorized access to protected routes (`/dashboard`, `/deposit`, `/withdraw`, `/transfer`, `/transactions`, `/change_pin`).
3. **Transaction Atomicity**: Transfers and balance updates execute in SQLite transactions with rollback on failure to prevent data inconsistencies.
4. **Input Sanitization & Defense**:
   - Negative, zero, and malformed amount prevention.
   - Enforced 10-digit numeric phone format with uniqueness check.
   - Enforced 4-digit numeric PIN format.
   - Enforced 6-digit numeric Account Number format.
5. **No Raw Tracebacks**: Custom error handlers for 404 and 500 status codes prevent leaking stack traces or raw database errors to end users.

---

## Database Schema

### `accounts` Table
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Internal record identifier |
| `account_number` | TEXT | UNIQUE NOT NULL | Unique 6-digit banking ID |
| `name` | TEXT | NOT NULL | Account holder full name |
| `phone` | TEXT | UNIQUE NOT NULL | 10-digit mobile number |
| `pin` | TEXT | NOT NULL | Cryptographically hashed PIN |
| `balance` | REAL | NOT NULL DEFAULT 0.0 CHECK(balance >= 0) | Available funds in ₹ |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Account creation date & time |

### `transactions` Table
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique transaction reference ID |
| `account_number` | TEXT | NOT NULL | Associated account number |
| `transaction_type` | TEXT | NOT NULL | Deposit, Withdrawal, Transfer Sent, Transfer Received |
| `amount` | REAL | NOT NULL | Transaction value |
| `description` | TEXT | NOT NULL | Transaction remarks & counterpart details |
| `created_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Timestamp of execution |

---

## Technology Stack

- **Backend**: Python 3.10+ / Flask
- **Database**: SQLite3 (Native Python module, zero external setup)
- **Security**: Werkzeug Security (`generate_password_hash`, `check_password_hash`)
- **Frontend**: Semantic HTML5, Vanilla CSS3 (Custom design system), Vanilla JavaScript (ES6)
- **Templating**: Jinja2 (Reusable component layouts, filters, flash alerts)

---

## Setup & Execution

### 1. Prerequisites
- Python 3.10+ installed
- SQLite3 (standard with Python)

### 2. Local Installation
Clone or navigate to the project directory and install the required dependencies:
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
The application reads its cryptographic secret key and debug settings from environment variables.
A safe template is provided in `.env.example`.

Copy `.env.example` to `.env` or export the environment variable:
```bash
# On Linux / macOS / Bash:
export SECRET_KEY="your-random-production-secret-key"

# On Windows PowerShell:
$env:SECRET_KEY="your-random-production-secret-key"
```

> [!NOTE]
> If `SECRET_KEY` is not provided, the application defaults to a development fallback key for local convenience. Always configure a secure, unique `SECRET_KEY` in production environments.

### 4. Run Locally (Development Server)
```bash
python app.py
```
Open your browser and navigate to:
```text
http://127.0.0.1:5000
```

### 5. Production Run (WSGI Server)
For production deployments (e.g., Linux PaaS, VPS, or cloud hosts such as Render, Railway, or Heroku), execute using the Gunicorn WSGI server:
```bash
gunicorn app:app
```
The application automatically creates the SQLite database schema on startup if it does not already exist.

### 6. Render Deployment
The application includes a `render.yaml` blueprint configuration for automated deployment as a Render Web Service.

- **Runtime**: Python
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`
- **Environment Variable**: `SECRET_KEY` (configured with auto-generation in `render.yaml`)

> [!NOTE]
> **Demo deployment note**: The free hosting environment uses an ephemeral filesystem, so the local SQLite database is intended for demonstration purposes. For permanent production data persistence, a managed database or persistent storage should be configured.

### 7. Original Console Application
To execute the original terminal-based banking simulation for evaluation or reference:
```bash
python banking_system.py
```
