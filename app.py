"""
Apex Core Banking System - Web Application Controller
Flask application providing secure user authentication, core banking operations
(deposits, withdrawals, fund transfers), ledger statements, and security PIN management.
"""

import os
import re
from functools import wraps
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    abort
)
import database

# ---------------------------------------------------------------------------
# Simple .env file loader for environment variables (Zero external dependencies)
# ---------------------------------------------------------------------------
def _load_env_file():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.isfile(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        os.environ.setdefault(key.strip(), val.strip().strip("'\""))
        except Exception:
            pass

_load_env_file()

# Initialize Flask application
app = Flask(__name__)

# Security & Session Configuration
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "dev-insecure-apex-bank-key-change-in-prod-2026"
)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Auto-initialize SQLite database schema on startup or WSGI import
database.init_db()


@app.after_request
def add_security_headers(response):
    """
    Add security headers to prevent caching of sensitive banking data
    and ensure protected pages cannot be accessed via browser back-forward cache after logout.
    """
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


def login_required(f):
    """
    Decorator to protect routes requiring authentication.
    Redirects unauthenticated users to the login page.
    Also validates that the session user still exists in the database.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        account_number = session.get("account_number")
        if not account_number:
            flash("Please sign in to access your banking dashboard.", "warning")
            return redirect(url_for("login"))

        # Verify account existence in the database
        account = database.get_account_by_number(account_number)
        if not account:
            session.clear()
            flash("Your session is invalid or expired. Please sign in again.", "danger")
            return redirect(url_for("login"))

        return f(*args, **kwargs)
    return decorated_function


def parse_and_validate_amount(amount_raw, max_balance=None):
    """
    Validate monetary input.
    Returns (valid: bool, amount: float or None, error_message: str or None).
    """
    if not amount_raw or not amount_raw.strip():
        return False, None, "Please enter an amount."

    try:
        cleaned = amount_raw.strip()
        if not re.match(r"^\d+(\.\d{1,2})?$", cleaned):
            return False, None, "Please enter a valid amount with up to 2 decimal places (e.g. 500 or 1250.50)."

        amount = round(float(cleaned), 2)
    except (ValueError, TypeError):
        return False, None, "Invalid amount format. Please enter a valid number."

    if amount <= 0:
        return False, None, "Amount must be greater than zero."

    if amount > 10000000.0:
        return False, None, "Amount exceeds the single transaction limit of ₹1,00,00,000."

    if max_balance is not None and amount > max_balance:
        return False, None, f"Insufficient balance! Available balance is ₹{max_balance:,.2f}."

    return True, amount, None


# ---------------------------------------------------------------------------
# Authentication Routes (Login, Register, Logout)
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Root route: Redirect to dashboard if logged in, otherwise to login."""
    if session.get("account_number"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Sign in page and credential verification.
    Enforces strict 6-digit account and 4-digit PIN format.
    Displays generic error on failure to prevent user enumeration.
    """
    # Only redirect active sessions on GET requests; POST must authenticate submitted credentials
    if request.method == "GET" and session.get("account_number"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        # Clear any prior session state before authenticating new credentials
        session.clear()
        account_number = request.form.get("account_number", "").strip()
        pin = request.form.get("pin", "").strip()

        # Strict input validations
        if not account_number or not pin:
            flash("Please enter both your Account Number and PIN.", "danger")
            return render_template("login.html", active_page="login")

        if len(account_number) != 6 or not account_number.isdigit():
            flash("Invalid account number or PIN.", "danger")
            return render_template("login.html", active_page="login")

        if len(pin) != 4 or not pin.isdigit():
            flash("Invalid account number or PIN.", "danger")
            return render_template("login.html", active_page="login")

        # Authenticate against SQLite via secure cryptographic hash
        account = database.authenticate_user(account_number, pin)
        if not account:
            # Generic error prevents account existence leakage
            flash("Invalid account number or PIN.", "danger")
            return render_template("login.html", active_page="login")

        # Create session
        session.clear()
        session["account_number"] = account["account_number"]
        session["name"] = account["name"]

        flash(f"Welcome back, {account['name']}!", "success")
        return redirect(url_for("dashboard"))

    return render_template("login.html", active_page="login")


@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Account registration page.
    Validates name, unique 10-digit phone, matching 4-digit PIN,
    and automatically generates a unique 6-digit account number.
    """
    if session.get("account_number"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        pin = request.form.get("pin", "").strip()
        confirm_pin = request.form.get("confirm_pin", "").strip()

        # Name validation
        if not name:
            flash("Full Name is required.", "danger")
            return render_template("register.html", active_page="register")

        if len(name) < 2 or len(name) > 60:
            flash("Full Name must be between 2 and 60 characters.", "danger")
            return render_template("register.html", active_page="register")

        if not re.match(r"^[A-Za-z\s\.\'-]+$", name):
            flash("Full Name can only contain letters, spaces, dots, and hyphens.", "danger")
            return render_template("register.html", active_page="register")

        # Phone validation (exactly 10 digits, numeric)
        if len(phone) != 10 or not phone.isdigit():
            flash("Phone number must be exactly 10 digits.", "danger")
            return render_template("register.html", active_page="register")

        # PIN validation (exactly 4 digits, numeric)
        if len(pin) != 4 or not pin.isdigit():
            flash("Secret PIN must be exactly 4 digits.", "danger")
            return render_template("register.html", active_page="register")

        if pin != confirm_pin:
            flash("PIN and Confirm PIN do not match.", "danger")
            return render_template("register.html", active_page="register")

        # Create account in SQLite database with hashed PIN and phone uniqueness check
        new_account_number, err = database.create_account(name, phone, pin)
        if err or not new_account_number:
            flash(err or "An error occurred while creating your account. Please try again.", "danger")
            return render_template("register.html", active_page="register")

        # Clear any prior session state to isolate the new account completely
        session.clear()
        session["registered_acc"] = new_account_number
        session["registered_name"] = name

        # Immediately render dedicated registration success view
        return render_template(
            "register_success.html",
            account_number=new_account_number,
            name=name,
            active_page="register"
        )

    return render_template("register.html", active_page="register")


@app.route("/register-success")
def register_success():
    """Fallback registration confirmation page."""
    acc = session.get("registered_acc")
    name = session.get("registered_name", "Valued Customer")
    if not acc:
        return redirect(url_for("login"))
    return render_template(
        "register_success.html",
        account_number=acc,
        name=name,
        active_page="register"
    )


@app.route("/logout")
def logout():
    """Clear session and log the user out cleanly."""
    session.clear()
    flash("You have been signed out successfully. Thank you for using Apex Core Banking System.", "info")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Core Banking Operations (Dashboard, Deposit, Withdraw, Transfer, History)
# ---------------------------------------------------------------------------

@app.route("/dashboard")
@login_required
def dashboard():
    """
    Main user banking dashboard showing available balance,
    account metadata, and the last 5 transactions.
    """
    acc_num = session["account_number"]
    account = database.get_account_by_number(acc_num)
    recent_transactions = database.get_transactions(acc_num, limit=5)

    return render_template(
        "dashboard.html",
        account=account,
        recent_transactions=recent_transactions,
        active_page="dashboard"
    )


@app.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():
    """Deposit money into the current logged-in account."""
    acc_num = session["account_number"]
    account = database.get_account_by_number(acc_num)

    if request.method == "POST":
        amount_raw = request.form.get("amount", "")
        description = request.form.get("description", "").strip() or "Cash Deposit"

        # Sanitize description
        if len(description) > 100:
            description = description[:100]

        valid, amount, error_msg = parse_and_validate_amount(amount_raw)
        if not valid:
            flash(error_msg, "danger")
            return render_template("deposit.html", account=account, active_page="deposit")

        success, message, new_bal = database.deposit_money(acc_num, amount, description)
        if success:
            flash(message, "success")
            return redirect(url_for("dashboard"))
        else:
            flash(message, "danger")
            return render_template("deposit.html", account=account, active_page="deposit")

    return render_template("deposit.html", account=account, active_page="deposit")


@app.route("/withdraw", methods=["GET", "POST"])
@login_required
def withdraw():
    """Withdraw cash from the current logged-in account with balance verification."""
    acc_num = session["account_number"]
    account = database.get_account_by_number(acc_num)

    if request.method == "POST":
        amount_raw = request.form.get("amount", "")
        description = request.form.get("description", "").strip() or "Cash Withdrawal"

        if len(description) > 100:
            description = description[:100]

        valid, amount, error_msg = parse_and_validate_amount(amount_raw, max_balance=account["balance"])
        if not valid:
            flash(error_msg, "danger")
            return render_template("withdraw.html", account=account, active_page="withdraw")

        success, message, new_bal = database.withdraw_money(acc_num, amount, description)
        if success:
            flash(message, "success")
            return redirect(url_for("dashboard"))
        else:
            flash(message, "danger")
            return render_template("withdraw.html", account=account, active_page="withdraw")

    return render_template("withdraw.html", account=account, active_page="withdraw")


@app.route("/transfer", methods=["GET", "POST"])
@login_required
def transfer():
    """Transfer funds to another verified account."""
    acc_num = session["account_number"]
    account = database.get_account_by_number(acc_num)

    if request.method == "POST":
        receiver_acc = request.form.get("receiver_acc", "").strip()
        amount_raw = request.form.get("amount", "")
        custom_note = request.form.get("custom_note", "").strip()

        if len(custom_note) > 100:
            custom_note = custom_note[:100]

        if not receiver_acc:
            flash("Please enter the beneficiary account number.", "danger")
            return render_template("transfer.html", account=account, active_page="transfer")

        if len(receiver_acc) != 6 or not receiver_acc.isdigit():
            flash("Beneficiary account number must be exactly 6 digits.", "danger")
            return render_template("transfer.html", account=account, active_page="transfer")

        if receiver_acc == acc_num:
            flash("You cannot transfer money to your own account.", "danger")
            return render_template("transfer.html", account=account, active_page="transfer")

        valid, amount, error_msg = parse_and_validate_amount(amount_raw, max_balance=account["balance"])
        if not valid:
            flash(error_msg, "danger")
            return render_template("transfer.html", account=account, active_page="transfer")

        success, message, new_bal = database.transfer_money(acc_num, receiver_acc, amount, custom_note)
        if success:
            flash(message, "success")
            return redirect(url_for("dashboard"))
        else:
            flash(message, "danger")
            return render_template("transfer.html", account=account, active_page="transfer")

    return render_template("transfer.html", account=account, active_page="transfer")


@app.route("/transactions")
@login_required
def transactions():
    """View full chronological statement of all transactions."""
    acc_num = session["account_number"]
    account = database.get_account_by_number(acc_num)
    all_transactions = database.get_transactions(acc_num)

    return render_template(
        "transactions.html",
        account=account,
        transactions=all_transactions,
        active_page="transactions"
    )


@app.route("/change_pin", methods=["GET", "POST"])
@login_required
def change_pin():
    """Change secret 4-digit PIN after verifying the current PIN."""
    acc_num = session["account_number"]
    account = database.get_account_by_number(acc_num)

    if request.method == "POST":
        current_pin = request.form.get("current_pin", "").strip()
        new_pin = request.form.get("new_pin", "").strip()
        confirm_pin = request.form.get("confirm_pin", "").strip()

        if not current_pin or not new_pin or not confirm_pin:
            flash("Please fill in all PIN fields.", "danger")
            return render_template("change_pin.html", account=account, active_page="change_pin")

        if len(current_pin) != 4 or not current_pin.isdigit():
            flash("Current PIN must be exactly 4 digits.", "danger")
            return render_template("change_pin.html", account=account, active_page="change_pin")

        if len(new_pin) != 4 or not new_pin.isdigit():
            flash("New PIN must be exactly 4 digits.", "danger")
            return render_template("change_pin.html", account=account, active_page="change_pin")

        if new_pin != confirm_pin:
            flash("New PIN and Confirm PIN do not match.", "danger")
            return render_template("change_pin.html", account=account, active_page="change_pin")

        if current_pin == new_pin:
            flash("New PIN cannot be identical to current PIN.", "danger")
            return render_template("change_pin.html", account=account, active_page="change_pin")

        success, message = database.change_pin(acc_num, current_pin, new_pin)
        if success:
            flash(message, "success")
            return redirect(url_for("dashboard"))
        else:
            flash(message, "danger")
            return render_template("change_pin.html", account=account, active_page="change_pin")

    return render_template("change_pin.html", account=account, active_page="change_pin")


# ---------------------------------------------------------------------------
# Error Handlers
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found_error(error):
    """Graceful 404 handler avoiding raw tracebacks."""
    flash("The requested resource was not found.", "warning")
    if session.get("account_number"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.errorhandler(500)
def internal_error(error):
    """Graceful 500 handler avoiding raw tracebacks."""
    flash("An unexpected server error occurred. Please try again.", "danger")
    if session.get("account_number"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Application Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Start local development server (debug defaults to False for security)
    debug_mode = os.environ.get("FLASK_DEBUG", "False").lower() in ("true", "1", "yes")
    app.run(host="127.0.0.1", port=5000, debug=debug_mode)

