import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import sqlite3
import serial
import threading
import time

# ===============================
# Configuration
# ===============================
SERIAL_PORT = 'COM3'  # <-- Change to your Arduino's port (e.g., COM4, /dev/ttyUSB0, etc.)
BAUD_RATE = 9600

# ===============================
# Database Setup
# ===============================
def create_tables():
    """
    Create necessary tables if they don't exist, including a default admin user.
    """
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()

    # Users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        role TEXT DEFAULT 'User'
    )
    """)

    # Access Logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS access_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT NOT NULL
    )
    """)

    # Stock
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 0
    )
    """)

    # Stock Logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stock_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        change INTEGER NOT NULL,
        user_name TEXT NOT NULL,
        user_uid TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Default admin user
    default_admin_uid = "63:19:CE:12"  # Change if your Master Card has a different UID
    cursor.execute("SELECT * FROM users WHERE uid = ?", (default_admin_uid,))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (uid, name, role) VALUES (?, ?, ?)",
            (default_admin_uid, "Default Admin", "Admin")
        )
        print(f"[INFO] Default admin UID {default_admin_uid} added to the database.")

    conn.commit()
    conn.close()

create_tables()

# ===============================
# Attempt Serial Connection
# ===============================
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    print("[INFO] Serial connection established.")
except Exception as e:
    ser = None
    print(f"[ERROR] Could not open serial port {SERIAL_PORT}: {e}")

# ===============================
# Top-Level App Class
# ===============================
class RFIDApp(tk.Tk):
    """
    Main Application Window
    """
    def __init__(self):
        super().__init__()
        self.title("RFID + Stock Management")
        self.geometry("600x400")

        # State
        self.current_user_role = None
        self.current_user_name = None
        self.current_user_uid = None

        # Frames
        self.login_frame = LoginFrame(self)
        self.main_frame = MainFrame(self)

        # Show the login frame first
        self.show_login_frame()

        # Start a serial-reading thread if we have a valid serial connection
        if ser:
            self.serial_thread = threading.Thread(target=self.read_serial_data, daemon=True)
            self.serial_thread.start()

    def show_login_frame(self):
        """
        Show the login frame, hide the main frame.
        """
        self.main_frame.pack_forget()
        self.login_frame.pack(fill="both", expand=True)

    def show_main_frame(self):
        """
        Show the main frame (post-login), hide the login frame.
        """
        self.login_frame.pack_forget()
        self.main_frame.pack(fill="both", expand=True)
        self.main_frame.update_greeting()

    def process_uid(self, uid):
        """
        Called by read_serial_data when we see "Scanned UID: xxx".
        Checks the DB for that UID. Grants or denies access.
        Also writes "GRANTED" or "DENIED" to Arduino so it can display properly.
        """
        conn = sqlite3.connect("inventory.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE uid = ?", (uid,))
        user = cursor.fetchone()

        if user:
            # user = (id, uid, name, role)
            status = "Granted"
            cursor.execute("INSERT INTO access_logs (uid, status) VALUES (?, ?)", (uid, status))
            conn.commit()

            # Let Arduino know -> show "Access Granted"
            if ser:
                ser.write(b"GRANTED\n")

            self.current_user_role = user[3]  # e.g., "Admin" or "User"
            self.current_user_name = user[2]  # e.g., "Default Admin" or "John"
            self.current_user_uid = user[1]   # e.g., "63:19:CE:12"

            print(f"[INFO] Access Granted for UID: {uid}")
            # Switch to main frame
            self.show_main_frame()

        else:
            status = "Denied"
            cursor.execute("INSERT INTO access_logs (uid, status) VALUES (?, ?)", (uid, status))
            conn.commit()

            # Let Arduino know -> show "Access Denied"
            if ser:
                ser.write(b"DENIED\n")

            print(f"[WARN] Access Denied for UID: {uid}")
            # Show a message box on the login frame
            messagebox.showwarning("Access Denied", f"UID: {uid}\nAccess Denied. Please try again.")

        conn.close()

    def read_serial_data(self):
        """
        Continuously read from the serial port in a background thread.
        Looks for lines starting with 'Scanned UID:'.
        """
        print("[INFO] Listening for Arduino logs...")
        buffer = ""

        while True:
            # If the app was closed, break
            if not self.winfo_exists():
                break

            try:
                if ser and ser.in_waiting > 0:
                    char = ser.read().decode('utf-8', errors='replace')
                    if char == '\n':
                        line = buffer.strip()
                        buffer = ""
                        if line.startswith("Scanned UID:"):
                            # e.g. "Scanned UID: 63:19:CE:12"
                            uid = line.split(": ", 1)[1].strip()
                            # Process UID in the main thread
                            self.after(0, self.process_uid, uid)
                        else:
                            # Just print other messages from Arduino
                            print(f"[Arduino] {line}")
                    else:
                        buffer += char
            except Exception as e:
                print(f"[ERROR] Reading serial: {e}")
                break
            time.sleep(0.01)  # Slight pause to free CPU

# ===============================
# Login Frame
# ===============================
class LoginFrame(tk.Frame):
    """
    Frame that instructs the user to scan their RFID card.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        label = tk.Label(self, text="Please Scan your RFID card...", font=("Helvetica", 16))
        label.pack(pady=50)

# ===============================
# Main Frame
# ===============================
class MainFrame(tk.Frame):
    """
    Frame for logged-in users (Admin or normal).
    Shows buttons for user mgmt (if Admin) and stock mgmt.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        self.greeting_label = tk.Label(self, text="Welcome!", font=("Helvetica", 16))
        self.greeting_label.pack(pady=10)

        # Admin-only button
        self.manage_users_btn = tk.Button(self, text="Manage Users", command=self.open_user_manager)
        self.manage_users_btn.pack(pady=5)

        # Stock management
        self.manage_stock_btn = tk.Button(self, text="Manage Stock", command=self.open_stock_manager)
        self.manage_stock_btn.pack(pady=5)

        # Logout
        logout_btn = tk.Button(self, text="Logout", command=self.logout)
        logout_btn.pack(pady=20)

        # Exit
        exit_btn = tk.Button(self, text="Exit Application", command=parent.destroy)
        exit_btn.pack(pady=5)

    def update_greeting(self):
        """
        Called each time we show the main frame to greet the user properly.
        Shows or hides the 'Manage Users' button depending on role.
        """
        role = self.parent.current_user_role
        name = self.parent.current_user_name
        if role and name:
            self.greeting_label.config(text=f"Welcome, {role} - {name}!")
        else:
            self.greeting_label.config(text="Welcome!")

        # Show "Manage Users" only if Admin
        if role == "Admin":
            self.manage_users_btn.pack(pady=5)
        else:
            self.manage_users_btn.pack_forget()

    def open_user_manager(self):
        """
        Open the user manager window (Toplevel).
        """
        UserManager(self)

    def open_stock_manager(self):
        """
        Open the stock manager window (Toplevel).
        """
        StockManager(self, 
                     self.parent.current_user_role, 
                     self.parent.current_user_name, 
                     self.parent.current_user_uid)

    def logout(self):
        """
        Clear user info and switch back to login frame.
        """
        self.parent.current_user_role = None
        self.parent.current_user_name = None
        self.parent.current_user_uid = None
        self.parent.show_login_frame()

# ===============================
# User Manager Window
# ===============================
class UserManager(tk.Toplevel):
    """
    Allows Admin to view, add, and delete users.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.title("User Manager")
        self.geometry("500x400")
        self.conn = sqlite3.connect("inventory.db")
        self.cursor = self.conn.cursor()

        tk.Label(self, text="User Manager", font=("Helvetica", 16, "bold")).pack(pady=10)

        # Treeview
        self.tree = ttk.Treeview(self, columns=("UID", "Name", "Role"), show='headings')
        self.tree.heading("UID", text="UID")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Role", text="Role")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="Add User", command=self.add_user).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Delete User", command=self.delete_user).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Refresh", command=self.refresh_user_list).pack(side=tk.LEFT, padx=5)

        self.refresh_user_list()

    def refresh_user_list(self):
        """
        Clear and reload the user list from DB.
        """
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.cursor.execute("SELECT uid, name, role FROM users")
        users = self.cursor.fetchall()
        for u in users:
            self.tree.insert("", tk.END, values=(u[0], u[1], u[2]))

    def add_user(self):
        """
        Prompt for new user data and insert into DB.
        """
        uid = simpledialog.askstring("New User", "Enter RFID UID (e.g. 63:19:CE:12):")
        if not uid:
            return
        name = simpledialog.askstring("New User", "Enter User Name:")
        if not name:
            return
        role = simpledialog.askstring("New User", "Enter Role (Admin/User):", initialvalue="User")
        if not role:
            role = "User"

        try:
            self.cursor.execute("INSERT INTO users (uid, name, role) VALUES (?, ?, ?)", (uid, name, role))
            self.conn.commit()
            messagebox.showinfo("Success", f"User '{name}' added.")
        except sqlite3.IntegrityError:
            messagebox.showwarning("Error", f"UID {uid} already exists.")
        self.refresh_user_list()

    def delete_user(self):
        """
        Delete the selected user from DB (careful not to delete your own admin).
        """
        selection = self.tree.selection()
        if not selection:
            return
        uid = self.tree.item(selection[0], "values")[0]
        confirm = messagebox.askyesno("Confirm Deletion", f"Delete user with UID: {uid}?")
        if confirm:
            self.cursor.execute("DELETE FROM users WHERE uid = ?", (uid,))
            self.conn.commit()
            self.refresh_user_list()

# ===============================
# Stock Manager Window
# ===============================
class StockManager(tk.Toplevel):
    """
    Allows a user (Admin or normal) to manage stock (add items, update quantities).
    Logs each change in stock_logs.
    """
    def __init__(self, parent, role, user_name, user_uid):
        super().__init__(parent)
        self.title("Stock Manager")
        self.geometry("600x400")
        self.role = role
        self.user_name = user_name
        self.user_uid = user_uid

        self.conn = sqlite3.connect("inventory.db")
        self.cursor = self.conn.cursor()

        tk.Label(self, text="Stock Manager", font=("Helvetica", 16, "bold")).pack(pady=10)

        # Treeview
        self.tree = ttk.Treeview(self, columns=("Name", "Quantity"), show='headings')
        self.tree.heading("Name", text="Name")
        self.tree.heading("Quantity", text="Quantity")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Add Item", command=self.add_item).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Update Quantity", command=self.update_quantity).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Refresh", command=self.refresh_stock_list).pack(side=tk.LEFT, padx=5)

        self.refresh_stock_list()

    def refresh_stock_list(self):
        """
        Refresh the TreeView with current stock items.
        """
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.cursor.execute("SELECT name, quantity FROM stock")
        items = self.cursor.fetchall()
        for i in items:
            self.tree.insert("", tk.END, values=(i[0], i[1]))

    def add_item(self):
        """
        Prompt for a new stock item's name and initial quantity.
        """
        item_name = simpledialog.askstring("New Item", "Enter Item Name:")
        if not item_name:
            return

        try:
            initial_quantity = int(simpledialog.askstring("New Item", "Enter Initial Quantity:", initialvalue="0"))
        except (ValueError, TypeError):
            initial_quantity = 0

        # Insert into DB
        self.cursor.execute("INSERT INTO stock (name, quantity) VALUES (?, ?)", (item_name, initial_quantity))
        self.conn.commit()

        # Log the addition
        self.cursor.execute("""
            INSERT INTO stock_logs (name, change, user_name, user_uid) 
            VALUES (?, ?, ?, ?)
        """, (item_name, initial_quantity, self.user_name, self.user_uid))
        self.conn.commit()

        messagebox.showinfo("Success", f"Added '{item_name}' with quantity {initial_quantity}.")
        self.refresh_stock_list()

    def update_quantity(self):
        """
        Prompt user to update the quantity of a selected item.
        """
        selection = self.tree.selection()
        if not selection:
            return
        item_name = self.tree.item(selection[0], "values")[0]
        current_qty = int(self.tree.item(selection[0], "values")[1])

        try:
            new_qty_str = simpledialog.askstring("Update Quantity", 
                                                 f"Enter new quantity for '{item_name}':",
                                                 initialvalue=str(current_qty))
            if new_qty_str is None:
                return
            new_quantity = int(new_qty_str)
        except ValueError:
            return

        change_amount = new_quantity - current_qty

        # Update stock
        self.cursor.execute("UPDATE stock SET quantity = ? WHERE name = ?", (new_quantity, item_name))
        self.conn.commit()

        # Log the change
        self.cursor.execute("""
            INSERT INTO stock_logs (name, change, user_name, user_uid)
            VALUES (?, ?, ?, ?)
        """, (item_name, change_amount, self.user_name, self.user_uid))
        self.conn.commit()

        messagebox.showinfo("Success", f"'{item_name}' quantity updated to {new_quantity}.")
        self.refresh_stock_list()

# ===============================
# Main Entry
# ===============================
if __name__ == "__main__":
    app = RFIDApp()
    app.mainloop()
