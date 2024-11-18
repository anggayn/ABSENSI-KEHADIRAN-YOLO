import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DB_NAME = 'attendance.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_log_table():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            file_path TEXT,
            person_name TEXT,
            category TEXT
        )
    ''')
    conn.commit()
    conn.close()

def create_user_table():
    conn = get_db_connection()
    conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    ''')
    conn.commit()
    conn.close()

def add_email_column():
    conn = get_db_connection()
    try:
        conn.execute('ALTER TABLE users ADD COLUMN email TEXT')
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()



def add_category_column():
    conn = get_db_connection()
    try:
        conn.execute('ALTER TABLE logs ADD COLUMN category TEXT')
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

def insert_log(file_path, person_name, category):
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO logs (timestamp, file_path, person_name, category)
        VALUES (?, ?, ?, ?)
    ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), file_path, person_name, category))
    conn.commit()
    conn.close()

def fetch_logs():
    conn = get_db_connection()
    logs = conn.execute('SELECT * FROM logs').fetchall()
    conn.close()
    return logs

def clear_logs():
    conn = get_db_connection()
    conn.execute("DELETE FROM logs")
    conn.commit()
    conn.close()

def delete_log_by_id(log_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM logs WHERE id = ?', (log_id,))
    conn.commit()
    conn.close()

def register_user(username, email, password):
    conn = get_db_connection()
    try:
        hashed_password = generate_password_hash(password)
        conn.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', (username, email, hashed_password))
        conn.commit()
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()
    return True

# def verify_user(username, password):
#     conn = get_db_connection()
#     user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
#     conn.close()
#     if user and check_password_hash(user['password'], password):
#         return True
#     return False

def verify_user(username, password):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()

    # Debugging output to check what the function retrieves
    if user:
        print(f"User found: {user}")  # Print user data for debugging
    
    if user and check_password_hash(user['password'], password):
        print(f"Valid credentials for user ID: {user['id']}")  # Show the ID
        return user['id']  # Return the user_id (assuming 'id' is the column name)
    
    return None  # If no user or invalid credentials, return None


create_user_table()
add_email_column()