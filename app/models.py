import sqlite3
from werkzeug.security import generate_password_hash

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def add_user(username, password, is_admin=0):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    hashed_pw = generate_password_hash(password)
    cursor.execute('''
        INSERT INTO users (username, password, is_admin)
        VALUES (?, ?, ?)
    ''', (username, hashed_pw, is_admin))
    conn.commit()
    conn.close()

def get_user_by_username(username):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    return user
