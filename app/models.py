import sqlite3
from werkzeug.security import generate_password_hash

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
      CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        is_admin INTEGER DEFAULT 0
      )
    ''')

    # Create posts table
    cursor.execute('''
      CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        author TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

def get_all_posts():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, content, author FROM posts ORDER BY id DESC')
    posts = cursor.fetchall()
    conn.close()
    return [
        {'id': row[0], 'title': row[1], 'preview': row[2][:100], 'author': row[3]}
        for row in posts
    ]