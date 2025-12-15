## Salay Glass One-Page Checkout & E-Receipt System

This is a small, focused web application that implements the case study system:

- **Single-page checkout interface** for recording sales transactions
- **Automatic computation** of line totals, overall total, payment, and balance
- **Daily income tracking** (total sales and payments received per day)
- **Electronic receipt (e-receipt)** generation for each transaction that can be printed or saved as PDF
- **Simple history list** of recent transactions, filterable by date

The system is intentionally limited to **one main screen** so that a 2–3 person team can operate it comfortably.

### 1. Requirements

- Python 3.10+ recommended
- `pip` for installing dependencies

Install dependencies from the project root:

```bash
cd /home/kaku/repos/Customer-IM
pip install -r requirements.txt
```

### 2. Running the System

From the project root:

```bash
cd /home/kaku/repos/Customer-IM
python app.py
```

This will:

- Create a local SQLite database file `salay_glass.db` (if it doesn't already exist)
- Start the Flask development server on `http://0.0.0.0:5000`

Open your browser and go to:

- `http://localhost:5000`

You will see the **single-page checkout interface**:

- Left side: customer details, job description, line items table, total / payment / balance, and **Save sale & open receipt** button
- Right side: **Daily income summary** for the selected date and a **list of up to 50 transactions** for that date

### 3. Using the Checkout Page

- **Customer details**: Fill in customer name (required) and optional contact
- **Job / project description**: Describe the work (required)
- **Line items**:
  - Each row has description, quantity, and unit price
  - Line totals and overall total are computed automatically as you type
  - Only rows with valid entries are saved
- **Amount paid**:
  - Enter the down payment or full amount
  - Balance is computed automatically (and turns green when fully paid)
- **Save sale & open receipt**:
  - Saves the transaction to the SQLite database
  - Opens an **e-receipt modal** showing all details and line items
  - Use **Print / Save PDF** to give the customer a digital or printed receipt

### 4. Daily Income & History

- The **date picker** on the top-right card selects the day you want to inspect
- For the selected date the system shows:
  - **Total sales** (sum of all `total_amount`)
  - **Payments received** (sum of all `amount_paid`)
- The **history list** below shows:
  - Up to 50 most recent transactions for that day
  - Status chips: *Paid* or *With balance*
  - A **View receipt** action that re-opens the e-receipt at any time

All of this is still on the **same page**, matching the case study scope.

### 5. Data Storage

- Data is stored in an SQLite database: `salay_glass.db`
- Two main tables:
  - `transactions`
    - Customer, contact, description
    - Total amount, amount paid, balance
    - Timestamps and transaction date (for daily reports)
  - `line_items`
    - Optional breakdown of materials/labor for each transaction

The database file can be backed up like a normal file.

### 6. How This Maps to the Case Study

- **Problem**: handwritten receipts, scattered records, slow income tracking  
  **Solution**: a single digital page that:
  - Centralizes transaction entry
  - Automatically calculates totals and balances
  - Stores receipts electronically
  - Provides quick access to daily totals and past receipts

This implementation can be extended later (e.g., separate reports, user accounts) but is deliberately kept minimal to stay aligned with the case study focus.



