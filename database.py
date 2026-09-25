"""
Apex Core Banking System - Database Layer
Handles SQLite persistence, schema initialization, secure PIN hashing verification,
and atomic ACID transactions for deposits, withdrawals, and inter-account transfers.
"""

import os
import sqlite3
import random
from werkzeug.security import generate_password_hash, check_password_hash

# Base directory and SQLite database path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "database")
DB_PATH = os.path.join(DB_DIR, "banking.db")


def get_db():
    """Establish and return a connection to the SQLite database."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """
    Initialize the database schema if tables do not exist.
    Creates clean tables with integrity constraints and indexes.
    No hard-coded demo credentials or seed accounts are inserted.
    """
    os.makedirs(DB_DIR, exist_ok=True)
    conn = get_db()
    cursor = conn.cursor()

    # Accounts table: Enforces unique account numbers, unique phone numbers, and non-negative balances
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_number TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            pin TEXT NOT NULL,
            balance REAL NOT NULL DEFAULT 0.0 CHECK(balance >= 0.0),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Transactions table: Enforces cascade foreign key constraint to accounts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_number TEXT NOT NULL,
            transaction_type TEXT NOT NULL,
            amount REAL NOT NULL CHECK(amount > 0.0),
            description TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (account_number) REFERENCES accounts(account_number) ON DELETE CASCADE
        )
    """)

    # Performance and integrity indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_accounts_account_number ON accounts(account_number)")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_accounts_phone ON accounts(phone)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_account_number ON transactions(account_number)")

    conn.commit()
    conn.close()


def generate_unique_account_number():
    """Generate a unique 6-digit account number with guaranteed uniqueness."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        while True:
            acc_num = str(random.randint(100000, 999999))
            cursor.execute("SELECT 1 FROM accounts WHERE account_number = ?", (acc_num,))
            if not cursor.fetchone():
                return acc_num
    finally:
        conn.close()


def get_account_by_phone(phone):
    """Retrieve an account record by 10-digit phone number."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM accounts WHERE phone = ?", (str(phone).strip(),))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_account_by_number(account_number):
    """Retrieve an account record by 6-digit account number."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM accounts WHERE account_number = ?", (str(account_number).strip(),))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create_account(name, phone, pin):
    """
    Create a new bank account with securely hashed PIN.
    Enforces phone uniqueness and returns (account_number, error_message).
    """
    phone_clean = str(phone).strip()
    name_clean = str(name).strip()

    # Pre-check for phone number uniqueness
    if get_account_by_phone(phone_clean):
        return None, "An account with this phone number is already registered."

    acc_num = generate_unique_account_number()
    hashed_pin = generate_password_hash(pin)

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO accounts (account_number, name, phone, pin, balance)
            VALUES (?, ?, ?, ?, 0.0)
            """,
            (acc_num, name_clean, phone_clean, hashed_pin)
        )
        conn.commit()
        return acc_num, None
    except sqlite3.IntegrityError as e:
        conn.rollback()
        if "phone" in str(e).lower():
            return None, "An account with this phone number is already registered."
        return None, "Account creation failed due to a database constraint."
    except sqlite3.Error as e:
        conn.rollback()
        return None, f"Database error: {str(e)}"
    finally:
        conn.close()


def authenticate_user(account_number, pin):
    """
    Authenticate a user by account number and plain PIN against the stored hash.
    Returns account dict if authentication succeeds, None otherwise.
    Plaintext PIN comparison is strictly rejected.
    """
    account = get_account_by_number(account_number)
    if not account:
        return None

    stored_pin = account["pin"]
    # Strictly verify cryptographic hash
    if check_password_hash(stored_pin, str(pin).strip()):
        return account
    return None


def deposit_money(account_number, amount, description="Cash Deposit"):
    """
    Deposit funds into an account and record the transaction.
    Returns (success: bool, message: str, new_balance: float or None).
    """
    try:
        amount = round(float(amount), 2)
    except (ValueError, TypeError):
        return False, "Invalid amount value.", None

    if amount <= 0:
        return False, "Deposit amount must be greater than zero.", None

    if amount > 10000000.0:
        return False, "Deposit amount exceeds the maximum single transaction limit of ₹1,00,00,000.", None

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT balance FROM accounts WHERE account_number = ?", (account_number,))
        row = cursor.fetchone()
        if not row:
            return False, "Account not found.", None

        new_balance = round(row["balance"] + amount, 2)
        cursor.execute(
            "UPDATE accounts SET balance = ? WHERE account_number = ?",
            (new_balance, account_number)
        )
        cursor.execute(
            """
            INSERT INTO transactions (account_number, transaction_type, amount, description)
            VALUES (?, 'Deposit', ?, ?)
            """,
            (account_number, amount, description.strip() or "Cash Deposit")
        )
        conn.commit()
        return True, f"₹{amount:,.2f} deposited successfully!", new_balance
    except sqlite3.Error as e:
        conn.rollback()
        return False, "Database error during deposit.", None
    finally:
        conn.close()


def withdraw_money(account_number, amount, description="Cash Withdrawal"):
    """
    Withdraw funds from an account after verifying available balance.
    Returns (success: bool, message: str, new_balance: float or None).
    """
    try:
        amount = round(float(amount), 2)
    except (ValueError, TypeError):
        return False, "Invalid amount value.", None

    if amount <= 0:
        return False, "Withdrawal amount must be greater than zero.", None

    if amount > 10000000.0:
        return False, "Withdrawal amount exceeds the maximum single transaction limit of ₹1,00,00,000.", None

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT balance FROM accounts WHERE account_number = ?", (account_number,))
        row = cursor.fetchone()
        if not row:
            return False, "Account not found.", None

        current_balance = row["balance"]
        if amount > current_balance:
            return False, f"Insufficient balance! Available balance is ₹{current_balance:,.2f}", None

        new_balance = round(current_balance - amount, 2)
        cursor.execute(
            "UPDATE accounts SET balance = ? WHERE account_number = ?",
            (new_balance, account_number)
        )
        cursor.execute(
            """
            INSERT INTO transactions (account_number, transaction_type, amount, description)
            VALUES (?, 'Withdrawal', ?, ?)
            """,
            (account_number, amount, description.strip() or "Cash Withdrawal")
        )
        conn.commit()
        return True, f"₹{amount:,.2f} withdrawn successfully!", new_balance
    except sqlite3.Error as e:
        conn.rollback()
        return False, "Database error during withdrawal.", None
    finally:
        conn.close()


def transfer_money(sender_acc, receiver_acc, amount, custom_note=None):
    """
    Transfer funds between two accounts atomically.
    Creates transaction logs for both sender and receiver.
    Returns (success: bool, message: str, sender_new_balance: float or None).
    """
    sender_acc = str(sender_acc).strip()
    receiver_acc = str(receiver_acc).strip()

    if sender_acc == receiver_acc:
        return False, "You cannot transfer money to your own account.", None

    try:
        amount = round(float(amount), 2)
    except (ValueError, TypeError):
        return False, "Invalid amount value.", None

    if amount <= 0:
        return False, "Transfer amount must be greater than zero.", None

    if amount > 10000000.0:
        return False, "Transfer amount exceeds the maximum single transaction limit of ₹1,00,00,000.", None

    conn = get_db()
    cursor = conn.cursor()
    try:
        # Check sender account and balance
        cursor.execute("SELECT balance, name FROM accounts WHERE account_number = ?", (sender_acc,))
        sender_row = cursor.fetchone()
        if not sender_row:
            return False, "Sender account not found.", None

        sender_balance = sender_row["balance"]
        sender_name = sender_row["name"]

        if amount > sender_balance:
            return False, f"Insufficient balance! Your current balance is ₹{sender_balance:,.2f}", None

        # Check receiver account
        cursor.execute("SELECT balance, name FROM accounts WHERE account_number = ?", (receiver_acc,))
        receiver_row = cursor.fetchone()
        if not receiver_row:
            return False, f"Receiver account #{receiver_acc} does not exist.", None

        receiver_balance = receiver_row["balance"]
        receiver_name = receiver_row["name"]

        # Atomic balance updates
        sender_new_balance = round(sender_balance - amount, 2)
        receiver_new_balance = round(receiver_balance + amount, 2)

        cursor.execute("UPDATE accounts SET balance = ? WHERE account_number = ?", (sender_new_balance, sender_acc))
        cursor.execute("UPDATE accounts SET balance = ? WHERE account_number = ?", (receiver_new_balance, receiver_acc))

        # Transaction records for both accounts
        note_text = custom_note.strip() if custom_note and custom_note.strip() else ""
        note_suffix = f" - Note: {note_text}" if note_text else ""
        sender_desc = f"Transfer to {receiver_acc} ({receiver_name}){note_suffix}"
        receiver_desc = f"Transfer from {sender_acc} ({sender_name}){note_suffix}"

        cursor.execute(
            """
            INSERT INTO transactions (account_number, transaction_type, amount, description)
            VALUES (?, 'Transfer Sent', ?, ?)
            """,
            (sender_acc, amount, sender_desc)
        )
        cursor.execute(
            """
            INSERT INTO transactions (account_number, transaction_type, amount, description)
            VALUES (?, 'Transfer Received', ?, ?)
            """,
            (receiver_acc, amount, receiver_desc)
        )

        conn.commit()
        return True, f"₹{amount:,.2f} successfully transferred to {receiver_name} (Acc: {receiver_acc})!", sender_new_balance
    except sqlite3.Error as e:
        conn.rollback()
        return False, "Database transaction failed during fund transfer.", None
    finally:
        conn.close()


def get_transactions(account_number, limit=None):
    """Fetch transaction history for an account, sorted latest first."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        query = "SELECT * FROM transactions WHERE account_number = ? ORDER BY id DESC"
        params = [str(account_number).strip()]

        if limit and isinstance(limit, int):
            query += " LIMIT ?"
            params.append(limit)

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def change_pin(account_number, current_pin, new_pin):
    """
    Verify current PIN and update account with hashed new PIN.
    Returns (success: bool, message: str).
    """
    account = get_account_by_number(account_number)
    if not account:
        return False, "Account not found."

    stored_pin = account["pin"]
    # Strictly verify cryptographic hash of current PIN
    if not check_password_hash(stored_pin, str(current_pin).strip()):
        return False, "Incorrect current PIN! PIN change cancelled."

    if current_pin == new_pin:
        return False, "New PIN cannot be identical to current PIN."

    hashed_new_pin = generate_password_hash(new_pin)

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE accounts SET pin = ? WHERE account_number = ?", (hashed_new_pin, account_number))
        conn.commit()
        return True, "PIN changed successfully! Please use your new PIN next time."
    except sqlite3.Error:
        conn.rollback()
        return False, "Failed to update PIN due to a database error."
    finally:
        conn.close()
