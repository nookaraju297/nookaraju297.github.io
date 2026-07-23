'''import tkinter as tk
from tkinter import messagebox
import random, sqlite3, datetime, hashlib
import pyttsx3

# --- Voice Engine ---
engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('volume', 1.0)

def speak(text):
    engine.say(text)
    engine.runAndWait()

# --- Database Setup ---
conn = sqlite3.connect("banking.db")
cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS users (
    phone TEXT PRIMARY KEY,
    password TEXT
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS accounts (
    phone TEXT,
    account_number TEXT,
    balance INTEGER,
    PRIMARY KEY(phone, account_number)
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS transactions (
    phone TEXT,
    account_number TEXT,
    action TEXT,
    amount INTEGER,
    balance INTEGER,
    timestamp TEXT
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS login_history (
    phone TEXT,
    timestamp TEXT
)""")

conn.commit()

current_user = None
otp_code = None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- User Functions ---
def register_user():
    phone = entry_phone.get()
    password = entry_pass.get()
    if not phone or not password:
        messagebox.showerror("Error", "Phone number and password required.")
        return
    try:
        cur.execute("INSERT INTO users VALUES (?, ?)", (phone, hash_password(password)))
        conn.commit()
        messagebox.showinfo("Success", f"User {phone} registered!")
        speak(f"User with phone {phone} registered successfully")
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "User already exists.")

def send_otp():
    global otp_code
    phone = entry_phone.get()
    password = entry_pass.get()
    cur.execute("SELECT password FROM users WHERE phone=?", (phone,))
    row = cur.fetchone()
    if not row:
        messagebox.showerror("Error", "User does not exist.")
        return
    if row[0] != hash_password(password):
        messagebox.showerror("Error", "Incorrect password.")
        return
    otp_code = str(random.randint(1000, 9999))
    messagebox.showinfo("OTP Sent", f"Your OTP is {otp_code} (demo mode)")
    speak("OTP has been generated, please enter it")

def verify_otp():
    global current_user
    entered = entry_otp.get()
    if entered == otp_code:
        current_user = entry_phone.get()
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("INSERT INTO login_history VALUES (?, ?)", (current_user, ts))
        conn.commit()
        messagebox.showinfo("Welcome", f"Logged in as {current_user}")
        speak(f"Welcome user {current_user}")
        show_dashboard()
    else:
        messagebox.showerror("Error", "Invalid OTP")
        speak("Invalid OTP, please try again")

# --- Banking Functions ---
def create_account():
    acc = entry_acc.get()
    try:
        bal = int(entry_bal.get())
    except ValueError:
        messagebox.showerror("Error", "Balance must be a number")
        return
    try:
        cur.execute("INSERT INTO accounts VALUES (?, ?, ?)", (current_user, acc, bal))
        conn.commit()
        log_transaction(acc, "Create", bal, bal)
        messagebox.showinfo("Success", f"Account {acc} created with balance {bal}.")
        speak(f"Account {acc} created with balance {bal}")
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Account already exists.")

def deposit():
    acc = entry_acc.get()
    amt = int(entry_amt.get())
    cur.execute("SELECT balance FROM accounts WHERE phone=? AND account_number=?", (current_user, acc))
    row = cur.fetchone()
    if not row:
        messagebox.showerror("Error", "Account does not exist.")
        return
    new_bal = row[0] + amt
    cur.execute("UPDATE accounts SET balance=? WHERE phone=? AND account_number=?", (new_bal, current_user, acc))
    conn.commit()
    log_transaction(acc, "Deposit", amt, new_bal)
    messagebox.showinfo("Success", f"Deposited {amt}. New balance: {new_bal}.")
    speak(f"Deposited {amt}. New balance {new_bal}")

def withdraw():
    acc = entry_acc.get()
    amt = int(entry_amt.get())
    cur.execute("SELECT balance FROM accounts WHERE phone=? AND account_number=?", (current_user, acc))
    row = cur.fetchone()
    if not row:
        messagebox.showerror("Error", "Account does not exist.")
        return
    if row[0] < amt:
        messagebox.showerror("Error", "Insufficient funds.")
        return
    new_bal = row[0] - amt
    cur.execute("UPDATE accounts SET balance=? WHERE phone=? AND account_number=?", (new_bal, current_user, acc))
    conn.commit()
    log_transaction(acc, "Withdraw", amt, new_bal)
    messagebox.showinfo("Success", f"Withdrew {amt}. New balance: {new_bal}.")
    speak(f"Withdrew {amt}. New balance {new_bal}")

def check_balance():
    acc = entry_acc.get()
    cur.execute("SELECT balance FROM accounts WHERE phone=? AND account_number=?", (current_user, acc))
    row = cur.fetchone()
    if not row:
        messagebox.showerror("Error", "Account does not exist.")
    else:
        messagebox.showinfo("Balance", f"Balance for {acc}: {row[0]}")
        speak(f"Balance for account {acc} is {row[0]}")

def log_transaction(acc, action, amt, bal):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?)", (current_user, acc, action, amt, bal, ts))
    conn.commit()
    update_history()

def update_history():
    history_list.delete(0, tk.END)
    cur.execute("SELECT action, amount, balance, timestamp FROM transactions WHERE phone=? ORDER BY timestamp DESC LIMIT 10", (current_user,))
    for row in cur.fetchall():
        history_list.insert(tk.END, f"{row[3]} - {row[0]} {row[1]} (Bal: {row[2]})")

# --- GUI Setup ---
root = tk.Tk()
root.title("📱 Secure Banking App with OTP")
root.geometry("600x600")
root.config(bg="#121212")

frame_login = tk.Frame(root, bg="#121212")
frame_login.pack(fill="both", expand=True)

tk.Label(frame_login, text="Phone Number:", fg="white", bg="#121212").pack(pady=5)
entry_phone = tk.Entry(frame_login)
entry_phone.pack()

tk.Label(frame_login, text="Password:", fg="white", bg="#121212").pack(pady=5)
entry_pass = tk.Entry(frame_login, show="*")
entry_pass.pack()

tk.Button(frame_login, text="Register", command=register_user, bg="#00adb5", fg="white").pack(pady=5)
tk.Button(frame_login, text="Send OTP", command=send_otp, bg="#00adb5", fg="white").pack(pady=5)

tk.Label(frame_login, text="Enter OTP:", fg="white", bg="#121212").pack(pady=5)
entry_otp = tk.Entry(frame_login)
entry_otp.pack()

tk.Button(frame_login, text="Verify OTP", command=verify_otp, bg="#00adb5", fg="white").pack(pady=5)

frame_dash = tk.Frame(root, bg="#121212")

def show_dashboard():
    frame_login.pack_forget()
    frame_dash.pack(fill="both", expand=True)

    tk.Label(frame_dash, text="💳 Banking Dashboard", font=("Arial", 16, "bold"), fg="#00ffcc", bg="#121212").pack(pady=10)

    global entry_acc, entry_bal, entry_amt, history_list
    tk.Label(frame_dash, text="Account Number:", fg="white", bg="#121212").pack()
    entry_acc = tk.Entry(frame_dash)
    entry_acc.pack(pady=5)

    tk.Label(frame_dash, text="Initial Balance:", fg="white", bg="#121212").pack()
    entry_bal = tk.Entry(frame_dash)
    entry_bal.pack(pady=5)

    tk.Label(frame_dash, text="Amount:", fg="white", bg="#121212").pack()
    entry_amt = tk.Entry(frame_dash)
    entry_amt.pack(pady=5)
    root.mainloop()'''
    
'''import tkinter as tk
import random

root = tk.Tk()
root.title("📱 OTP Login Demo")
root.geometry("300x250")
root.config(bg="#121212")

otp_code = None

def send_otp():
    global otp_code
    otp_code = str(random.randint(1000, 9999))
    label_info.config(text=f"OTP sent (demo): {otp_code}")

def verify_otp():
    entered = entry_otp.get()
    if entered == otp_code:
        label_info.config(text="✅ Login Successful")
    else:
        label_info.config(text="❌ Invalid OTP")

tk.Label(root, text="Phone Number:", fg="white", bg="#121212").pack(pady=5)
entry_phone = tk.Entry(root)
entry_phone.pack()

tk.Label(root, text="Password:", fg="white", bg="#121212").pack(pady=5)
entry_pass = tk.Entry(root, show="*")
entry_pass.pack()

tk.Button(root, text="Send OTP", command=send_otp, bg="#00adb5", fg="white").pack(pady=10)

tk.Label(root, text="Enter OTP:", fg="white", bg="#121212").pack(pady=5)
entry_otp = tk.Entry(root)
entry_otp.pack()

tk.Button(root, text="Verify OTP", command=verify_otp, bg="#00adb5", fg="white").pack(pady=10)

label_info = tk.Label(root, text="", fg="yellow", bg="#121212")
label_info.pack(pady=10)

root.mainloop()'''

'''import tkinter as tk
from tkinter import messagebox
import random, sqlite3, datetime, hashlib
import pyttsx3

# --- Voice Engine ---
engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('volume', 1.0)

def speak(text):
    engine.say(text)
    engine.runAndWait()

# --- Database Setup ---
conn = sqlite3.connect("banking.db")
cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS users (
    phone TEXT PRIMARY KEY,
    password TEXT
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS accounts (
    phone TEXT,
    account_number TEXT,
    balance INTEGER,
    PRIMARY KEY(phone, account_number)
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS transactions (
    phone TEXT,
    account_number TEXT,
    action TEXT,
    amount INTEGER,
    balance INTEGER,
    timestamp TEXT
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS login_history (
    phone TEXT,
    timestamp TEXT
)""")

conn.commit()

current_user = None
otp_code = None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- User Functions ---
def register_user():
    phone = entry_phone.get()
    password = entry_pass.get()
    if not phone or not password:
        messagebox.showerror("Error", "Phone number and password required.")
        return
    try:
        cur.execute("INSERT INTO users VALUES (?, ?)", (phone, hash_password(password)))
        conn.commit()
        messagebox.showinfo("Success", f"User {phone} registered!")
        speak(f"User with phone {phone} registered successfully")
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "User already exists.")

def send_otp():
    global otp_code
    phone = entry_phone.get()
    password = entry_pass.get()
    cur.execute("SELECT password FROM users WHERE phone=?", (phone,))
    row = cur.fetchone()
    if not row:
        messagebox.showerror("Error", "User does not exist.")
        return
    if row[0] != hash_password(password):
        messagebox.showerror("Error", "Incorrect password.")
        return
    otp_code = str(random.randint(1000, 9999))
    messagebox.showinfo("OTP Sent", f"Your OTP is {otp_code} (demo mode)")
    speak("OTP has been generated, please enter it")

def verify_otp():
    global current_user
    entered = entry_otp.get()
    if entered == otp_code:
        current_user = entry_phone.get()
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("INSERT INTO login_history VALUES (?, ?)", (current_user, ts))
        conn.commit()
        messagebox.showinfo("Welcome", f"Logged in as {current_user}")
        speak(f"Welcome user {current_user}")
        show_dashboard()
    else:
        messagebox.showerror("Error", "Invalid OTP")
        speak("Invalid OTP, please try again")

# --- Banking Functions ---
def create_account():
    acc = entry_acc.get()
    try:
        bal = int(entry_bal.get())
    except ValueError:
        messagebox.showerror("Error", "Balance must be a number")
        return
    try:
        cur.execute("INSERT INTO accounts VALUES (?, ?, ?)", (current_user, acc, bal))
        conn.commit()
        log_transaction(acc, "Create", bal, bal)
        messagebox.showinfo("Success", f"Account {acc} created with balance {bal}.")
        speak(f"Account {acc} created with balance {bal}")
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Account already exists.")

def deposit():
    acc = entry_acc.get()
    try:
        amt = int(entry_amt.get())
    except ValueError:
        messagebox.showerror("Error", "Amount must be a number")
        return
    cur.execute("SELECT balance FROM accounts WHERE phone=? AND account_number=?", (current_user, acc))
    row = cur.fetchone()
    if not row:
        messagebox.showerror("Error", "Account does not exist.")
        return
    new_bal = row[0] + amt
    cur.execute("UPDATE accounts SET balance=? WHERE phone=? AND account_number=?", (new_bal, current_user, acc))
    conn.commit()
    log_transaction(acc, "Deposit", amt, new_bal)
    messagebox.showinfo("Success", f"Deposited {amt}. New balance: {new_bal}.")
    speak(f"Deposited {amt}. New balance {new_bal}")

def withdraw():
    acc = entry_acc.get()
    try:
        amt = int(entry_amt.get())
    except ValueError:
        messagebox.showerror("Error", "Amount must be a number")
        return
    cur.execute("SELECT balance FROM accounts WHERE phone=? AND account_number=?", (current_user, acc))
    row = cur.fetchone()
    if not row:
        messagebox.showerror("Error", "Account does not exist.")
        return
    if row[0] < amt:
        messagebox.showerror("Error", "Insufficient funds.")
        return
    new_bal = row[0] - amt
    cur.execute("UPDATE accounts SET balance=? WHERE phone=? AND account_number=?", (new_bal, current_user, acc))
    conn.commit()
    log_transaction(acc, "Withdraw", amt, new_bal)
    messagebox.showinfo("Success", f"Withdrew {amt}. New balance: {new_bal}.")
    speak(f"Withdrew {amt}. New balance {new_bal}")

def check_balance():
    acc = entry_acc.get()
    cur.execute("SELECT balance FROM accounts WHERE phone=? AND account_number=?", (current_user, acc))
    row = cur.fetchone()
    if not row:
        messagebox.showerror("Error", "Account does not exist.")
    else:
        messagebox.showinfo("Balance", f"Balance for {acc}: {row[0]}")
        speak(f"Balance for account {acc} is {row[0]}")

def log_transaction(acc, action, amt, bal):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?)", (current_user, acc, action, amt, bal, ts))
    conn.commit()
    update_history()

def update_history():
    history_list.delete(0, tk.END)
    cur.execute("SELECT action, amount, balance, timestamp FROM transactions WHERE phone=? ORDER BY timestamp DESC LIMIT 10", (current_user,))
    for row in cur.fetchall():
        history_list.insert(tk.END, f"{row[3]} - {row[0]} {row[1]} (Bal: {row[2]})")

# --- GUI Setup ---
root = tk.Tk()
root.title("📱 Secure Banking App with OTP")
root.geometry("600x600")
root.config(bg="#121212")

frame_login = tk.Frame(root, bg="#121212")
frame_login.pack(fill="both", expand=True)

tk.Label(frame_login, text="Phone Number:", fg="white", bg="#121212").pack(pady=5)
entry_phone = tk.Entry(frame_login)
entry_phone.pack()

tk.Label(frame_login, text="Password:", fg="white", bg="#121212").pack(pady=5)
entry_pass = tk.Entry(frame_login, show="*")
entry_pass.pack()

tk.Button(frame_login, text="Register", command=register_user, bg="#00adb5", fg="white").pack(pady=5)
tk.Button(frame_login, text="Send OTP", command=send_otp, bg="#00adb5", fg="white").pack(pady=5)

tk.Label(frame_login, text="Enter OTP:", fg="white", bg="#121212").pack(pady=5)
entry_otp = tk.Entry(frame_login)
entry_otp.pack()

tk.Button(frame_login, text="Verify OTP", command=verify_otp, bg="#00adb5", fg="white").pack(pady=5)

frame_dash = tk.Frame(root, bg="#121212")

def show_dashboard():
    frame_login.pack_forget()
    frame_dash.pack(fill="both", expand=True)

    tk.Label(frame_dash, text="💳 Banking Dashboard", font=("Arial", 16, "bold"), fg="#00ffcc", bg="#121212").pack(pady=10)

    global entry_acc, entry_bal, entry_amt, history_list
    tk.Label(frame_dash, text="Account Number:", fg="white", bg="#121212").pack()
    entry_acc = tk.Entry(frame_dash)
    entry_acc.pack(pady=5)

    tk.Label(frame_dash, text="Initial Balance:", fg="white", bg="#121212").pack()
    entry_bal = tk.Entry(frame_dash)
    entry_bal.pack(pady=5)
    tk.Label(frame_dash, text="Amount:", fg="white", bg="#121212").pack()
    entry_amt = tk.Entry(frame_dash)
    entry_amt.pack(pady=5)

    tk.Button(frame_dash, text="Create Account", command=create_account, bg="#00adb5", fg="white").pack(pady=5)
    tk.Button(frame_dash, text="Deposit", command=deposit, bg="#00adb5", fg="white").pack(pady=5)
    tk.Button(frame_dash, text="Withdraw", command=withdraw, bg="#00adb5", fg="white").pack(pady=5)
    tk.Button(frame_dash, text="Check Balance", command=check_balance, bg="#00adb5", fg="white").pack(pady=5)

    tk.Label(frame_dash, text="📜 Transaction History", fg="#ff00ff", bg="#121212").pack(pady=5)
    history_list = tk.Listbox(frame_dash, width=60, height=10, bg="#1a1a2e", fg="white")
    history_list.pack(pady=5)

    tk.Button(frame_dash, text="Logout", command=lambda: logout(), bg="#ff5722", fg="white").pack(pady=10)

def logout():
    global current_user
    current_user = None
    frame_dash.pack_forget()
    frame_login.pack(fill="both", expand=True)
    speak("Logged out successfully")

# 👇 THIS IS THE FINAL LINE
root.mainloop()'''

import tkinter as tk
from tkinter import messagebox
import random, sqlite3, datetime, hashlib
import pyttsx3

# --- Voice Engine ---
engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('volume', 1.0)

def speak(text):
    engine.say(text)
    engine.runAndWait()

# --- Database Setup ---
conn = sqlite3.connect("c:/tkinter_practice/banking.db")
cur = conn.cursor()
# Reset users table to avoid schema errors
cur.execute("DROP TABLE IF EXISTS users")
cur.execute("""CREATE TABLE users (
    phone TEXT PRIMARY KEY,
    password TEXT
)""")
conn.commit()


cur.execute("""CREATE TABLE IF NOT EXISTS users (
    phone TEXT PRIMARY KEY,
    password TEXT
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS accounts (
    phone TEXT,
    account_number TEXT,
    balance INTEGER,
    PRIMARY KEY(phone, account_number)
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS transactions (
    phone TEXT,
    account_number TEXT,
    action TEXT,
    amount INTEGER,
    balance INTEGER,
    timestamp TEXT
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS login_history (
    phone TEXT,
    timestamp TEXT
)""")

conn.commit()

current_user = None
otp_code = None

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- User Functions ---
def register_user():
    phone = entry_phone.get()
    password = entry_pass.get()
    if not phone or not password:
        messagebox.showerror("Error", "Phone number and password required.")
        return
    try:
        cur.execute("INSERT INTO users VALUES (?, ?)", (phone, hash_password(password)))
        conn.commit()
        messagebox.showinfo("Success", f"User {phone} registered!")
        speak(f"User with phone {phone} registered successfully")
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "User already exists.")

def send_otp():
    global otp_code
    phone = entry_phone.get()
    password = entry_pass.get()
    cur.execute("SELECT password FROM users WHERE phone=?", (phone,))
    row = cur.fetchone()
    if not row:
        messagebox.showerror("Error", "User does not exist.")
        return
    if row[0] != hash_password(password):
        messagebox.showerror("Error", "Incorrect password.")
        return
    otp_code = str(random.randint(1000, 9999))
    # Show OTP directly in GUI
    label_otp_display.config(text=f"Your OTP (demo): {otp_code}")
    speak("OTP has been generated, please enter it")

def verify_otp():
    global current_user
    entered = entry_otp.get()
    if entered == otp_code:
        current_user = entry_phone.get()
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("INSERT INTO login_history VALUES (?, ?)", (current_user, ts))
        conn.commit()
        messagebox.showinfo("Welcome", f"Logged in as {current_user}")
        speak(f"Welcome user {current_user}")
        show_dashboard()
    else:
        messagebox.showerror("Error", "Invalid OTP")
        speak("Invalid OTP, please try again")

# --- Banking Functions ---
def create_account():
    acc = entry_acc.get()
    try:
        bal = int(entry_bal.get())
    except ValueError:
        messagebox.showerror("Error", "Balance must be a number")
        return
    try:
        cur.execute("INSERT INTO accounts VALUES (?, ?, ?)", (current_user, acc, bal))
        conn.commit()
        log_transaction(acc, "Create", bal, bal)
        messagebox.showinfo("Success", f"Account {acc} created with balance {bal}.")
        speak(f"Account {acc} created with balance {bal}")
    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "Account already exists.")

def deposit():
    acc = entry_acc.get()
    try:
        amt = int(entry_amt.get())
    except ValueError:
        messagebox.showerror("Error", "Amount must be a number")
        return
    cur.execute("SELECT balance FROM accounts WHERE phone=? AND account_number=?", (current_user, acc))
    row = cur.fetchone()
    if not row:
        messagebox.showerror("Error", "Account does not exist.")
        return
    new_bal = row[0] + amt
    cur.execute("UPDATE accounts SET balance=? WHERE phone=? AND account_number=?", (new_bal, current_user, acc))
    conn.commit()
    log_transaction(acc, "Deposit", amt, new_bal)
    messagebox.showinfo("Success", f"Deposited {amt}. New balance: {new_bal}.")
    speak(f"Deposited {amt}. New balance {new_bal}")

def withdraw():
    acc = entry_acc.get()
    try:
        amt = int(entry_amt.get())
    except ValueError:
        messagebox.showerror("Error", "Amount must be a number")
        return
    cur.execute("SELECT balance FROM accounts WHERE phone=? AND account_number=?", (current_user, acc))
    row = cur.fetchone()
    if not row:
        messagebox.showerror("Error", "Account does not exist.")
        return
    if row[0] < amt:
        messagebox.showerror("Error", "Insufficient funds.")
        return
    new_bal = row[0] - amt
    cur.execute("UPDATE accounts SET balance=? WHERE phone=? AND account_number=?", (new_bal, current_user, acc))
    conn.commit()
    log_transaction(acc, "Withdraw", amt, new_bal)
    messagebox.showinfo("Success", f"Withdrew {amt}. New balance: {new_bal}.")
    speak(f"Withdrew {amt}. New balance {new_bal}")

def check_balance():
    acc = entry_acc.get()
    cur.execute("SELECT balance FROM accounts WHERE phone=? AND account_number=?", (current_user, acc))
    row = cur.fetchone()
    if not row:
        messagebox.showerror("Error", "Account does not exist.")
    else:
        messagebox.showinfo("Balance", f"Balance for {acc}: {row[0]}")
        speak(f"Balance for account {acc} is {row[0]}")
def view_login_history():
    history_list.delete(0, tk.END)
    cur.execute("SELECT timestamp FROM login_history WHERE phone=? ORDER BY timestamp DESC", (current_user,))
    rows = cur.fetchall()
    if not rows:
        history_list.insert(tk.END, "No login history found.")
    else:
        for row in rows:
            history_list.insert(tk.END, f"Login at {row[0]}")
    speak("Showing your login history")

def view_activity_feed():
    history_list.delete(0, tk.END)

    # Show login history first
    cur.execute("SELECT timestamp FROM login_history WHERE phone=? ORDER BY timestamp DESC", (current_user,))
    logins = cur.fetchall()
    if logins:
        history_list.insert(tk.END, "=== Login History ===")
        for row in logins:
            history_list.insert(tk.END, f"Login at {row[0]}")
    else:
        history_list.insert(tk.END, "No login history found.")

    # Show transaction history next
    cur.execute("SELECT action, amount, balance, timestamp FROM transactions WHERE phone=? ORDER BY timestamp DESC", (current_user,))
    txns = cur.fetchall()
    if txns:
        history_list.insert(tk.END, "=== Transaction History ===")
        for row in txns:
            history_list.insert(tk.END, f"{row[3]} - {row[0]} {row[1]} (Bal: {row[2]})")
    else:
        history_list.insert(tk.END, "No transactions found.")

    speak("Showing your combined activity feed")

def log_transaction(acc, action, amt, bal):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?)", (current_user, acc, action, amt, bal, ts))
    conn.commit()
    update_history()

def update_history():
    history_list.delete(0, tk.END)
    cur.execute("SELECT action, amount, balance, timestamp FROM transactions WHERE phone=? ORDER BY timestamp DESC LIMIT 10", (current_user,))
    for row in cur.fetchall():
        history_list.insert(tk.END, f"{row[3]} - {row[0]} {row[1]} (Bal: {row[2]})")

# --- GUI Setup ---
root = tk.Tk()
root.title("📱 Secure Banking App with OTP")
root.geometry("600x600")
root.config(bg="#121212")

frame_login = tk.Frame(root, bg="#121212")
frame_login.pack(fill="both", expand=True)

tk.Label(frame_login, text="Phone Number:", fg="white", bg="#121212").pack(pady=5)
entry_phone = tk.Entry(frame_login)
entry_phone.pack()

tk.Label(frame_login, text="Password:", fg="white", bg="#121212").pack(pady=5)
entry_pass = tk.Entry(frame_login, show="*")
entry_pass.pack()

tk.Button(frame_login, text="Register", command=register_user, bg="#00adb5", fg="white").pack(pady=5)
tk.Button(frame_login, text="Send OTP", command=send_otp, bg="#00adb5", fg="white").pack(pady=5)

tk.Label(frame_login, text="Enter OTP:", fg="white", bg="#121212").pack(pady=5)
entry_otp = tk.Entry(frame_login)
entry_otp.pack()

tk.Button(frame_login, text="Verify OTP", command=verify_otp, bg="#00adb5", fg="white").pack(pady=5)

# Label to show OTP directly
label_otp_display = tk.Label(frame_login, text="", fg="yellow", bg="#121212", font=("Arial", 12))
label_otp_display.pack(pady=5)

frame_dash = tk.Frame(root, bg="#121212")

def show_dashboard():
    frame_login.pack_forget()
    frame_dash.pack(fill="both", expand=True)

    tk.Label(frame_dash, text="💳 Banking Dashboard", font=("Arial", 16, "bold"), fg="#00ffcc", bg="#121212").pack(pady=10)

    global entry_acc, entry_bal, entry_amt, history_list
    tk.Label(frame_dash, text="Account Number:", fg="white", bg="#121212").pack()
    entry_acc = tk.Entry(frame_dash)
    entry_acc.pack(pady=5)

    tk.Label(frame_dash, text="Initial Balance:", fg="white", bg="#121212").pack()
    entry_bal = tk.Entry(frame_dash)
    entry_bal.pack(pady=5)

    tk.Label(frame_dash, text="Amount:", fg="white", bg="#121212").pack()
    entry_amt = tk.Entry(frame_dash)
    entry_amt.pack(pady=5)

    tk.Button(frame_dash, text="Create Account", command=create_account, bg="#00adb5", fg="white").pack(pady=5)
    tk.Button(frame_dash, text="Deposit", command=deposit, bg="#00adb5", fg="white").pack(pady=5)
    tk.Button(frame_dash, text="Withdraw", command=withdraw, bg="#00adb5", fg="white").pack(pady=5)
    tk.Button(frame_dash, text="Check Balance", command=check_balance, bg="#00adb5", fg="white").pack(pady=5)
    tk.Button(frame_dash, text="View Login History", command=view_login_history, bg="#00adb5", fg="white").pack(pady=5)
    tk.Button(frame_dash, text="View Activity Feed", command=view_activity_feed, bg="#00adb5", fg="white").pack(pady=5)



    tk.Label(frame_dash, text="📜 Transaction History", fg="#ff00ff", bg="#121212").pack(pady=5)
    history_list = tk.Listbox(frame_dash, width=60, height=10, bg="#1a1a2e", fg="white")
    history_list.pack(pady=5)

    tk.Button(frame_dash, text="Logout", command=logout, bg="#ff5722", fg="white").pack(pady=10)

def logout():
    global current_user
    current_user = None
    frame_dash.pack_forget()
    frame_login.pack(fill="both", expand=True)
    speak("Logged out successfully")

# --- Run the App ---
root.mainloop()





    



