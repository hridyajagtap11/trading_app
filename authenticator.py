from db_manager import get_db_connection
import hashlib

def hash_password(password):
    """Hashes the password for secure storage."""
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(username, password):
    """Checks if the provided password matches the stored hash for a user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user and user['password'] == hash_password(password):
        return True
    return False

def create_user(username, password):
    """Creates a new user with a hashed password."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                       (username, hash_password(password)))
        conn.commit()
        conn.close()
        return True
    except conn.IntegrityError: # This error occurs if the username is already taken
        conn.close()
        return False