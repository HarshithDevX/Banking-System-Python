# Banking System - Mini Project

## Project Description
The Banking System is a simple Python console application that simulates fundamental banking operations. It provides a menu-driven interface allowing users to create accounts, log in securely using an account number and a 4-digit PIN, check balances, deposit money, withdraw funds, transfer money between accounts, view timestamped transaction history, and change their PIN.

This project was developed as a college Python mini project to demonstrate how fundamental programming concepts combine into a practical, real-world application.

---

## Features
- **Create Account**: Register an account with your name, 10-digit phone number, and a 4-digit PIN. The system automatically generates a unique 6-digit account number.
- **Login**: Access your account securely using your unique account number and PIN.
- **Check Balance**: View your current account balance anytime.
- **Deposit**: Deposit money into your account, updating the balance and recording the transaction.
- **Withdraw**: Withdraw money with automatic validation to prevent negative balances or overdrafts.
- **Transfer**: Transfer money securely between two accounts with real-time balance updates on both sides.
- **Transaction History**: View a complete chronological log of all deposits, withdrawals, and transfers with date and time stamps.
- **Change PIN**: Update your secret PIN by verifying your existing PIN and confirming the new PIN.
- **Logout**: Safely log out of your account session and return to the main menu.
- **Exit**: Exit the program cleanly from the main menu.

---

## Python Concepts Used
- **Variables & Data Types**: Strings, integers, floats, booleans.
- **Conditional Statements**: `if`, `elif`, `else` for input validation and menu routing.
- **Loops**: `while` loops for interactive menus and `for` loops for displaying transaction logs.
- **Functions**: Clean, modular functions for each banking operation (`create_account`, `login`, `deposit`, `withdraw`, etc.).
- **Data Structures**:
  - **Dictionaries**: In-memory storage for user accounts and their attributes (`accounts = {}`).
  - **Lists**: Ordered collection for storing transaction history strings.
- **String Operations**: Formatted f-strings, `.strip()`, `.isdigit()`, and `len()`.
- **Modules**:
  - `random`: Used to generate unique 6-digit bank account numbers (`random.randint`).
  - `datetime`: Used to record the exact date and time of every transaction (`datetime.now()`).

---

## How to Run

1. Open your terminal or command prompt.
2. Navigate to the project folder:
   ```bash
   cd Banking-System
   ```
3. Run the Python file:
   ```bash
   python banking_system.py
   ```

---

## Example Flow

1. **Main Menu**: Choose `1` to create an account.
   - Enter Name: `Rahul Sharma`
   - Enter Phone: `9876543210`
   - Create PIN: `1234`
   - System outputs: `Your Account Number is: 104523`
2. **Main Menu**: Choose `2` to log in.
   - Enter Account Number: `104523`
   - Enter PIN: `1234`
   - System logs you into the **Account Menu**.
3. **Account Menu**: Choose `2` to deposit money.
   - Enter amount: `5000`
   - New Balance: `Rs. 5000.00`
4. **Account Menu**: Choose `3` to withdraw money.
   - Enter amount: `1500`
   - Remaining Balance: `Rs. 3500.00`
5. **Account Menu**: Choose `5` to view transaction history.
   - Shows deposit and withdrawal records with timestamps.
6. **Account Menu**: Choose `7` to log out.
   - Returns safely to the Main Menu.
7. **Main Menu**: Choose `3` to exit.
