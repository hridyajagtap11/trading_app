import sqlite3
import pandas as pd

DATABASE_NAME = "trading_app.db"

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    """Creates the users, watchlist, and transactions tables if they don't already exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # User table: stores username and hashed password
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    
    # Watchlist table: links stocks to a specific user
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            ticker TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # --- NEW: Transactions table for portfolio tracking ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            ticker TEXT NOT NULL,
            shares REAL NOT NULL,
            purchase_price REAL NOT NULL,
            purchase_date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    conn.commit()
    conn.close()

# --- Watchlist Functions (unchanged) ---
def get_user_watchlist(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ticker FROM watchlist 
        JOIN users ON watchlist.user_id = users.id 
        WHERE users.username = ?
    """, (username,))
    watchlist = [row['ticker'] for row in cursor.fetchall()]
    conn.close()
    return watchlist

def add_to_watchlist(username, ticker):
    if ticker.upper() not in get_user_watchlist(username):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        if user:
            cursor.execute("INSERT INTO watchlist (user_id, ticker) VALUES (?, ?)", (user['id'], ticker.upper()))
            conn.commit()
        conn.close()
        return True
    return False

def remove_from_watchlist(username, ticker):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if user:
        cursor.execute("DELETE FROM watchlist WHERE user_id = ? AND ticker = ?", (user['id'], ticker.upper()))
        conn.commit()
    conn.close()

# --- NEW: Portfolio Functions ---
def add_transaction(username, ticker, shares, price, date):
    """Adds a new transaction to a user's portfolio."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if user:
        cursor.execute("""
            INSERT INTO transactions (user_id, ticker, shares, purchase_price, purchase_date) 
            VALUES (?, ?, ?, ?, ?)
        """, (user['id'], ticker.upper(), shares, price, date))
        conn.commit()
    conn.close()

def get_portfolio(username):
    """Retrieves all transactions for a user and returns them as a pandas DataFrame."""
    conn = get_db_connection()
    query = """
        SELECT ticker, shares, purchase_price, purchase_date FROM transactions
        JOIN users ON transactions.user_id = users.id
        WHERE users.username = ?
    """
    df = pd.read_sql_query(query, conn, params=(username,))
    conn.close()
    return df