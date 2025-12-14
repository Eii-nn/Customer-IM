import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import sqlite3
import os

class TransactionManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Salay Glass - Transaction Management System")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        
        # Database setup
        self.db_path = "transactions.db"
        self.init_database()
        
        # Create UI
        self.create_ui()
        
    def init_database(self):
        """Initialize SQLite database and create transactions table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                order_description TEXT NOT NULL,
                price REAL NOT NULL,
                downpayment REAL NOT NULL,
                balance REAL NOT NULL,
                transaction_date TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_ui(self):
        """Create the main user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Checkout Transaction Management", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # Search section at the top
        search_frame = ttk.LabelFrame(main_frame, text="Search Transactions", padding="10")
        search_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)
        
        ttk.Label(search_frame, text="Search by Customer Name:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, width=40, textvariable=self.search_var)
        self.search_entry.grid(row=0, column=1, pady=5, padx=5, sticky=(tk.W, tk.E))
        self.search_var.trace('w', self.search_transactions)
        
        ttk.Button(search_frame, text="View All", 
                  command=self.view_all_transactions).grid(row=0, column=2, padx=5)
        
        # Left side - Transaction Form
        form_frame = ttk.LabelFrame(main_frame, text="New Transaction", padding="10")
        form_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N), padx=(0, 10))
        
        # Form fields
        ttk.Label(form_frame, text="Customer Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.customer_name = ttk.Entry(form_frame, width=30)
        self.customer_name.grid(row=0, column=1, pady=5, padx=5)
        
        ttk.Label(form_frame, text="Order Description:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.order_description = tk.Text(form_frame, width=30, height=4)
        self.order_description.grid(row=1, column=1, pady=5, padx=5)
        
        ttk.Label(form_frame, text="Price (₱):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.price_var = tk.StringVar()
        self.price_entry = ttk.Entry(form_frame, width=30, textvariable=self.price_var)
        self.price_entry.grid(row=2, column=1, pady=5, padx=5)
        self.price_var.trace('w', self.calculate_balance)
        
        ttk.Label(form_frame, text="Downpayment (₱):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.downpayment_var = tk.StringVar()
        self.downpayment_entry = ttk.Entry(form_frame, width=30, textvariable=self.downpayment_var)
        self.downpayment_entry.grid(row=3, column=1, pady=5, padx=5)
        self.downpayment_var.trace('w', self.calculate_balance)
        
        ttk.Label(form_frame, text="Balance (₱):").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.balance_var = tk.StringVar(value="0.00")
        self.balance_label = ttk.Label(form_frame, textvariable=self.balance_var, 
                                      font=("Arial", 10, "bold"), foreground="blue")
        self.balance_label.grid(row=4, column=1, sticky=tk.W, pady=5, padx=5)
        
        ttk.Label(form_frame, text="Transaction Date:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.date_entry = ttk.Entry(form_frame, width=30, textvariable=self.date_var)
        self.date_entry.grid(row=5, column=1, pady=5, padx=5)
        
        # Buttons
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=15)
        
        ttk.Button(button_frame, text="Save Transaction", 
                  command=self.save_transaction).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear Form", 
                  command=self.clear_form).pack(side=tk.LEFT, padx=5)
        
        # Transactions display area
        display_frame = ttk.LabelFrame(main_frame, text="Transaction Records", padding="10")
        display_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        display_frame.columnconfigure(0, weight=1)
        display_frame.rowconfigure(0, weight=1)
        
        # Treeview for displaying transactions
        columns = ("ID", "Date", "Customer", "Order", "Price", "Downpayment", "Balance")
        self.tree = ttk.Treeview(display_frame, columns=columns, show="headings", height=15)
        
        # Configure column headings and widths
        self.tree.heading("ID", text="ID")
        self.tree.heading("Date", text="Date")
        self.tree.heading("Customer", text="Customer Name")
        self.tree.heading("Order", text="Order Description")
        self.tree.heading("Price", text="Price (₱)")
        self.tree.heading("Downpayment", text="Downpayment (₱)")
        self.tree.heading("Balance", text="Balance (₱)")
        
        self.tree.column("ID", width=50)
        self.tree.column("Date", width=100)
        self.tree.column("Customer", width=150)
        self.tree.column("Order", width=200)
        self.tree.column("Price", width=100)
        self.tree.column("Downpayment", width=120)
        self.tree.column("Balance", width=100)
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(display_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Load all transactions on startup
        self.view_all_transactions()
    
    def calculate_balance(self, *args):
        """Automatically calculate balance when price or downpayment changes"""
        try:
            price = float(self.price_var.get() or 0)
            downpayment = float(self.downpayment_var.get() or 0)
            balance = price - downpayment
            self.balance_var.set(f"{balance:.2f}")
        except ValueError:
            self.balance_var.set("0.00")
    
    def clear_form(self):
        """Clear all form fields"""
        self.customer_name.delete(0, tk.END)
        self.order_description.delete("1.0", tk.END)
        self.price_var.set("")
        self.downpayment_var.set("")
        self.balance_var.set("0.00")
        self.date_var.set(datetime.now().strftime("%Y-%m-%d"))
    
    def save_transaction(self):
        """Save transaction to database"""
        # Validate inputs
        customer = self.customer_name.get().strip()
        order_desc = self.order_description.get("1.0", tk.END).strip()
        
        if not customer:
            messagebox.showerror("Error", "Please enter customer name")
            return
        
        if not order_desc:
            messagebox.showerror("Error", "Please enter order description")
            return
        
        try:
            price = float(self.price_var.get() or 0)
            downpayment = float(self.downpayment_var.get() or 0)
            balance = price - downpayment
            transaction_date = self.date_var.get().strip()
            
            if price <= 0:
                messagebox.showerror("Error", "Price must be greater than 0")
                return
            
            if downpayment < 0:
                messagebox.showerror("Error", "Downpayment cannot be negative")
                return
            
            if not transaction_date:
                transaction_date = datetime.now().strftime("%Y-%m-%d")
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values for price and downpayment")
            return
        
        # Save to database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO transactions 
                (customer_name, order_description, price, downpayment, balance, transaction_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (customer, order_desc, price, downpayment, balance, transaction_date, 
                  datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Success", "Transaction saved successfully!")
            self.clear_form()
            self.view_all_transactions()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save transaction: {str(e)}")
    
    def search_transactions(self, *args):
        """Search transactions by customer name"""
        search_term = self.search_var.get().strip().lower()
        
        if not search_term:
            self.view_all_transactions()
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, transaction_date, customer_name, order_description, 
                       price, downpayment, balance
                FROM transactions
                WHERE LOWER(customer_name) LIKE ?
                ORDER BY created_at DESC
            ''', (f"%{search_term}%",))
            
            results = cursor.fetchall()
            conn.close()
            
            self.display_transactions(results)
            
        except Exception as e:
            messagebox.showerror("Error", f"Search failed: {str(e)}")
    
    def view_all_transactions(self):
        """Load and display all transactions"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, transaction_date, customer_name, order_description, 
                       price, downpayment, balance
                FROM transactions
                ORDER BY created_at DESC
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            self.display_transactions(results)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load transactions: {str(e)}")
    
    def display_transactions(self, transactions):
        """Display transactions in the treeview"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Insert transactions
        for trans in transactions:
            trans_id, date, customer, order_desc, price, downpayment, balance = trans
            # Truncate order description if too long
            order_display = order_desc[:50] + "..." if len(order_desc) > 50 else order_desc
            self.tree.insert("", tk.END, values=(
                trans_id, date, customer, order_display, 
                f"{price:.2f}", f"{downpayment:.2f}", f"{balance:.2f}"
            ))

def main():
    root = tk.Tk()
    app = TransactionManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()


