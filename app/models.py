import os
import sqlite3
from flask import current_app
from werkzeug.security import generate_password_hash

def get_db_connection():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    db_path  = os.path.join(base_dir, 'database.db')
    conn     = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn   = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
      CREATE TABLE IF NOT EXISTS users (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT    NOT NULL UNIQUE,
        password TEXT    NOT NULL,
        email    TEXT    NOT NULL UNIQUE,
        is_admin INTEGER DEFAULT 0
      )
    ''')

    cursor.execute('''
      CREATE TABLE IF NOT EXISTS posts (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        title      TEXT    NOT NULL,
        content    TEXT    NOT NULL,
        author     TEXT    NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    ''')

    conn.commit()
    conn.close()

def add_user(username, password, email=None, is_admin=0):
    conn   = get_db_connection()
    cursor = conn.cursor()
    hashed = generate_password_hash(password)
    cursor.execute(
        'INSERT INTO users (username, password, email, is_admin) VALUES (?, ?, ?, ?)',
        (username, hashed, email, is_admin)
    )
    conn.commit()
    conn.close()

def get_user_by_username(username):
    conn   = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_email(email):
    conn   = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_all_posts():
    conn   = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
      'SELECT id, title, content, author, created_at FROM posts ORDER BY id DESC'
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
          'id': row['id'],
          'title': row['title'],
          'preview': row['content'][:100],
          'author': row['author'],
          'created_at': row['created_at']
        }
        for row in rows
    ]

def get_post_by_id(post_id):
    conn   = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT p.id, p.title, p.content, p.author, p.created_at '
        'FROM posts p WHERE p.id = ?',
        (post_id,)
    )
    post = cursor.fetchone()
    conn.close()
    return post

def add_post(title, content, author):
    """
    NOTE: `author` here is a TEXT field (your posts.author column).
    We pass in session['username'], not session['user_id'].
    """
    conn   = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO posts (title, content, author) VALUES (?, ?, ?)',
        (title, content, author)
    )
    conn.commit()
    conn.close()