# Banking System - Mini Project
# A menu-driven Python application simulating bank operations

import random
from datetime import datetime

# In-memory dictionary to store all bank accounts
# Key: Account Number (String)
# Value: Dictionary containing account details and transaction history
accounts = {}


def create_account():
    print("\n---------------------------------")
    print("       CREATE NEW ACCOUNT        ")
    print("---------------------------------")
    
    name = input("Enter account holder name: ").strip()
    if not name:
        print("Error: Name cannot be empty.")
        return

    phone = input("Enter 10-digit phone number: ").strip()
    if len(phone) != 10 or not phone.isdigit():
        print("Error: Phone number must be exactly 10 digits.")
        return

    pin = input("Create a 4-digit secret PIN: ").strip()
    if len(pin) != 4 or not pin.isdigit():
        print("Error: PIN must be exactly 4 digits.")
        return

    # Generate a unique 6-digit account number using random module
    acc_num = str(random.randint(100000, 999999))
    while acc_num in accounts:
        acc_num = str(random.randint(100000, 999999))

    # Store account information in the dictionary
    accounts[acc_num] = {
        "name": name,
        "phone": phone,
        "pin": pin,
        "balance": 0.0,
        "transactions": []
    }

    print("\n>>> Account created successfully! <<<")
    print(f"Account Holder : {name}")
    print(f"Account Number : {acc_num}")
    print("Please keep your Account Number and PIN safe for login.")


def login():
    print("\n---------------------------------")
    print("             LOGIN               ")
    print("---------------------------------")
    
    acc_num = input("Enter your Account Number: ").strip()
    pin = input("Enter your 4-digit PIN: ").strip()

    # Check if the account number exists
    if acc_num not in accounts:
        print("Error: Account number not found!")
        return None

    # Check if the entered PIN matches the stored PIN
    if accounts[acc_num]["pin"] != pin:
        print("Error: Incorrect PIN!")
        return None

    print(f"\nLogin successful! Welcome, {accounts[acc_num]['name']}!")
    return acc_num


def check_balance(acc_num):
    print("\n---------------------------------")
    print("         CHECK BALANCE           ")
    print("---------------------------------")
    current_balance = accounts[acc_num]["balance"]
    print(f"Account Holder  : {accounts[acc_num]['name']}")
    print(f"Account Number  : {acc_num}")
    print(f"Current Balance : Rs. {current_balance:.2f}")


def deposit(acc_num):
    print("\n---------------------------------")
    print("         DEPOSIT MONEY           ")
    print("---------------------------------")
    try:
        amount = float(input("Enter amount to deposit: Rs. "))
    except ValueError:
        print("Error: Invalid amount! Please enter numbers only.")
        return

    # Check that deposit amount is positive
    if amount <= 0:
        print("Error: Deposit amount must be greater than zero.")
        return

    # Add to balance
    accounts[acc_num]["balance"] += amount
    
    # Record transaction with date and time
    now = datetime.now().strftime("%d-%m-%Y %H:%M")
    record = f"Deposit - Rs. {amount:.2f} - {now}"
    accounts[acc_num]["transactions"].append(record)

    print(f"Success: Rs. {amount:.2f} deposited successfully!")
    print(f"Updated Balance: Rs. {accounts[acc_num]['balance']:.2f}")


def withdraw(acc_num):
    print("\n---------------------------------")
    print("         WITHDRAW MONEY          ")
    print("---------------------------------")
    try:
        amount = float(input("Enter amount to withdraw: Rs. "))
    except ValueError:
        print("Error: Invalid amount! Please enter numbers only.")
        return

    # Check that withdrawal amount is positive
    if amount <= 0:
        print("Error: Withdrawal amount must be greater than zero.")
        return

    # Check for sufficient balance
    if amount > accounts[acc_num]["balance"]:
        print("Error: Insufficient balance!")
        print(f"Your current balance is: Rs. {accounts[acc_num]['balance']:.2f}")
        return

    # Deduct amount from balance
    accounts[acc_num]["balance"] -= amount

    # Record transaction with date and time
    now = datetime.now().strftime("%d-%m-%Y %H:%M")
    record = f"Withdrawal - Rs. {amount:.2f} - {now}"
    accounts[acc_num]["transactions"].append(record)

    print(f"Success: Rs. {amount:.2f} withdrawn successfully!")
    print(f"Remaining Balance: Rs. {accounts[acc_num]['balance']:.2f}")


def transfer(acc_num):
    print("\n---------------------------------")
    print("         TRANSFER MONEY          ")
    print("---------------------------------")
    receiver_acc = input("Enter receiver's Account Number: ").strip()

    # Sender and receiver cannot be the same account
    if receiver_acc == acc_num:
        print("Error: You cannot transfer money to your own account.")
        return

    # Check if receiver account exists
    if receiver_acc not in accounts:
        print("Error: Receiver account number does not exist!")
        return

    try:
        amount = float(input("Enter amount to transfer: Rs. "))
    except ValueError:
        print("Error: Invalid amount! Please enter numbers only.")
        return

    # Check that transfer amount is positive
    if amount <= 0:
        print("Error: Transfer amount must be greater than zero.")
        return

    # Check if sender has enough balance
    if amount > accounts[acc_num]["balance"]:
        print("Error: Insufficient balance for this transfer!")
        print(f"Your current balance is: Rs. {accounts[acc_num]['balance']:.2f}")
        return

    # Deduct from sender and add to receiver
    accounts[acc_num]["balance"] -= amount
    accounts[receiver_acc]["balance"] += amount

    # Record transactions in both accounts with date and time
    now = datetime.now().strftime("%d-%m-%Y %H:%M")
    sender_record = f"Transfer to {receiver_acc} - Rs. {amount:.2f} - {now}"
    receiver_record = f"Transfer from {acc_num} - Rs. {amount:.2f} - {now}"

    accounts[acc_num]["transactions"].append(sender_record)
    accounts[receiver_acc]["transactions"].append(receiver_record)

    print(f"Success: Rs. {amount:.2f} transferred to Account {receiver_acc} ({accounts[receiver_acc]['name']})!")
    print(f"Your Remaining Balance: Rs. {accounts[acc_num]['balance']:.2f}")


def view_transaction_history(acc_num):
    print("\n---------------------------------")
    print("      TRANSACTION HISTORY        ")
    print("---------------------------------")
    history = accounts[acc_num]["transactions"]

    if not history:
        print("No transactions found.")
    else:
        for index, txn in enumerate(history, 1):
            print(f"{index}. {txn}")


def change_pin(acc_num):
    print("\n---------------------------------")
    print("           CHANGE PIN            ")
    print("---------------------------------")
    old_pin = input("Enter your current PIN: ").strip()

    # Verify old PIN
    if old_pin != accounts[acc_num]["pin"]:
        print("Error: Incorrect current PIN! PIN change cancelled.")
        return

    new_pin = input("Enter new 4-digit PIN: ").strip()
    if len(new_pin) != 4 or not new_pin.isdigit():
        print("Error: New PIN must be exactly 4 digits.")
        return

    confirm_pin = input("Confirm new 4-digit PIN: ").strip()
    if new_pin != confirm_pin:
        print("Error: New PIN and Confirm PIN do not match!")
        return

    # Update PIN
    accounts[acc_num]["pin"] = new_pin
    print("Success: PIN changed successfully! Please use your new PIN next time.")


def account_menu(acc_num):
    while True:
        print("\n=================================")
        print("          ACCOUNT MENU           ")
        print("=================================")
        print("1. Check Balance")
        print("2. Deposit")
        print("3. Withdraw")
        print("4. Transfer")
        print("5. Transaction History")
        print("6. Change PIN")
        print("7. Logout")
        print("=================================")

        choice = input("Enter your choice (1-7): ").strip()

        if choice == "1":
            check_balance(acc_num)
        elif choice == "2":
            deposit(acc_num)
        elif choice == "3":
            withdraw(acc_num)
        elif choice == "4":
            transfer(acc_num)
        elif choice == "5":
            view_transaction_history(acc_num)
        elif choice == "6":
            change_pin(acc_num)
        elif choice == "7":
            print(f"\nLogged out successfully. Returning to Main Menu...")
            break
        else:
            print("Invalid choice! Please enter a number between 1 and 7.")


def main_menu():
    while True:
        print("\n=================================")
        print("         BANKING SYSTEM          ")
        print("=================================")
        print("1. Create Account")
        print("2. Login")
        print("3. Exit")
        print("=================================")

        choice = input("Enter your choice (1-3): ").strip()

        if choice == "1":
            create_account()
        elif choice == "2":
            logged_in_acc = login()
            if logged_in_acc:
                account_menu(logged_in_acc)
        elif choice == "3":
            print("\nThank you for using our Banking System. Goodbye!")
            break
        else:
            print("Invalid choice! Please enter 1, 2, or 3.")


if __name__ == "__main__":
    main_menu()
