import hashlib
import hmac
import json
import os
import sys
import tkinter as tk
from tkinter import messagebox

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PASSWORD_FILE = os.path.join(BASE_DIR, "admin.json")
MAX_ATTEMPTS = 3


def make_hash(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000).hex()


def password_exists():
    return os.path.exists(PASSWORD_FILE)


def save_password(password):
    salt = os.urandom(16)
    with open(PASSWORD_FILE, "w") as f:
        json.dump({"salt": salt.hex(), "hash": make_hash(password, salt)}, f)


def check_password(password):
    try:
        with open(PASSWORD_FILE, "r") as f:
            saved = json.load(f)
        salt = bytes.fromhex(saved["salt"])
        return hmac.compare_digest(make_hash(password, salt), saved["hash"])
    except (OSError, ValueError, KeyError):
        return False


logged_in = False
attempts = 0
first_time = not password_exists()

root = tk.Tk()
root.title("Login")
root.geometry("340x260")
root.resizable(False, False)

frame = tk.Frame(root, padx=20, pady=20)
frame.pack(fill="both", expand=True)

title = "Create Password" if first_time else "Login"
tk.Label(frame, text=title, font=("Arial", 16, "bold")).pack(pady=(0, 12))

tk.Label(frame, text="Password:").pack(anchor="w")
password_entry = tk.Entry(frame, show="*", width=30)
password_entry.pack(pady=(0, 8))
password_entry.focus()

confirm_entry = None
if first_time:
    tk.Label(frame, text="Confirm password:").pack(anchor="w")
    confirm_entry = tk.Entry(frame, show="*", width=30)
    confirm_entry.pack(pady=(0, 8))


def submit(event=None):
    global logged_in, attempts
    password = password_entry.get()

    if first_time:
        if len(password) < 4:
            messagebox.showerror("Error", "Password must be at least 4 characters")
            return
        if password != confirm_entry.get():
            messagebox.showerror("Error", "Passwords do not match")
            return
        save_password(password)
        messagebox.showinfo("Done", "Password created successfully!")
        logged_in = True
        root.destroy()
        return

    if check_password(password):
        logged_in = True
        root.destroy()
    else:
        attempts += 1
        password_entry.delete(0, "end")
        left = MAX_ATTEMPTS - attempts
        if left <= 0:
            messagebox.showerror("Error", "Too many wrong attempts. Closing.")
            root.destroy()
        else:
            messagebox.showerror("Error", f"Wrong password. {left} attempt(s) left.")


button_text = "Create Password" if first_time else "Login"
tk.Button(frame, text=button_text, width=20, command=submit).pack(pady=8)
root.bind("<Return>", submit)

root.mainloop()

if logged_in:
    import gui