import os
import sqlite3
import re
from datetime import datetime, timedelta
from functools import wraps
from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash
)
from markupsafe import Markup

from app.models import (
    init_db,
    add_user, get_user_by_username, get_user_by_email,
    get_all_posts, get_all_users, add_post, get_post_by_id, update_post
)
from app.forms import PostForm

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'something_secret')  # change in prod!

# VULNERABLE ON PURPOSE: no SameSite/Secure, HttpOnly explicitly turned off so
# document.cookie can read the session cookie (e.g. via the XSS below), and
# CSRF validation disabled app-wide (even for the PostForm-based routes).
app.config['SESSION_COOKIE_HTTPONLY'] = False
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_SAMESITE'] = None
app.config['WTF_CSRF_ENABLED'] = False

# Ensure tables exist
init_db()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to access that page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def index():
    posts = get_all_posts()
    return render_template('index.html', posts=posts)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email    = request.form['email']

        if get_user_by_username(username) or get_user_by_email(email):
            flash('Username or email already taken.', 'warning')
            return redirect(url_for('register'))

        add_user(username, password, email)
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user     = get_user_by_username(username)

        # VULNERABLE ON PURPOSE: plaintext comparison, no password hashing.
        if user and user['password'] == password:
            session['username'] = user['username']
            flash('Login successful.', 'success')
            return redirect(url_for('index'))

        flash('Invalid username or password', 'danger')
        return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        add_post(
            form.title.data,
            form.content.data,
            session['username']
        )
        flash('Your post has been published!', 'success')
        return redirect(url_for('index'))
    return render_template('new_post.html', form=form, edit=False)

@app.route('/post/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = get_post_by_id(post_id)
    if post is None:
        flash('Post not found.', 'warning')
        return redirect(url_for('index'))

    if session.get('username') != post['author']:
        flash('You’re not allowed to edit that post.', 'danger')
        return redirect(url_for('view_post', post_id=post_id))

    cutoff = post['created_at'] + timedelta(hours=1)
    if datetime.utcnow() > cutoff:
        flash('The edit window has closed (1 hour after posting).', 'warning')
        return redirect(url_for('view_post', post_id=post_id))

    form = PostForm(data={
        'title':   post['title'],
        'content': post['content']
    })

    if form.validate_on_submit():
        update_post(
            post_id,
            form.title.data,
            form.content.data
        )
        flash('Your post has been updated.', 'success')
        return redirect(url_for('view_post', post_id=post_id))

    return render_template('new_post.html', form=form, edit=True)

@app.route('/post/<int:post_id>')
def view_post(post_id):
    post = get_post_by_id(post_id)
    if post is None:
        flash('Post not found.', 'warning')
        return redirect(url_for('index'))
    return render_template('view_post.html', post=post)

@app.route('/admin')
def admin():
    # VULNERABLE ON PURPOSE: no login_required, no is_admin check -- anyone,
    # logged in or not, can view every user's username/email/plaintext password.
    users = get_all_users()
    posts = get_all_posts()
    return render_template('admin.html', users=users, posts=posts)

@app.template_filter('nl2br')
def nl2br_filter(s):
    """
    Replace double newlines with <p> and single newlines with <br> for clean paragraph spacing.
    """
    if s is None:
        return ''
    # VULNERABLE ON PURPOSE: no escaping -- raw HTML/JS in post content executes
    # for anyone who views the post (stored XSS).
    paragraphs = re.split(r'\n\s*\n', s)
    html_paragraphs = ['<p>{}</p>'.format(p.replace('\n', '<br>')) for p in paragraphs]
    return Markup('\n'.join(html_paragraphs))

@app.route('/post/delete/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = get_post_by_id(post_id)
    if post is None:
        flash('Post not found.', 'warning')
        return redirect(url_for('index'))

    if session.get('username') != post['author']:
        flash('You do not have permission to delete this post.', 'danger')
        return redirect(url_for('view_post', post_id=post_id))

    conn = sqlite3.connect(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database.db'))
    cursor = conn.cursor()
    cursor.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    conn.commit()
    conn.close()

    flash('Post deleted successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/search')
def search():
    query = request.args.get('q', '')
    filter_by = request.args.get('filter', 'all')
    sort_order = request.args.get('sort', 'latest')

    results = []

    if query.strip():
        con = sqlite3.connect("app/database.db")
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        order_clause = "DESC" if sort_order == "latest" else "ASC"

        # VULNERABLE ON PURPOSE: query is spliced directly into the SQL string,
        # no parameterization -- classic SQL injection via `q`.
        if filter_by == 'title':
            sql = f"SELECT * FROM posts WHERE title LIKE '%{query.strip()}%' ORDER BY created_at {order_clause}"
        elif filter_by == 'content':
            sql = f"SELECT * FROM posts WHERE content LIKE '%{query.strip()}%' ORDER BY created_at {order_clause}"
        else:
            sql = f"""
                SELECT * FROM posts
                WHERE title LIKE '%{query.strip()}%' OR content LIKE '%{query.strip()}%'
                ORDER BY created_at {order_clause}
            """

        cur.execute(sql)
        results = cur.fetchall()
        con.close()

    return render_template("index.html",
                           posts=results,
                           query=query,
                           filter=filter_by,
                           sort=sort_order)


if __name__ == '__main__':
    app.run(debug=True)
