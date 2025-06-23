from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash
)
from functools import wraps
from werkzeug.security import check_password_hash

from app.models import (
    init_db, add_user, get_user_by_username,
    get_user_by_email, get_all_posts, add_post,
    get_post_by_id 
)
from app.forms import PostForm
from markupsafe import Markup

app = Flask(__name__)
app.secret_key = 'something_secret'  # change in prod!

# ensure tables exist
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

@app.route('/register', methods=['GET','POST'])
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

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user_by_username(username)

        if user and check_password_hash(user['password'], password):
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

@app.route('/post/new', methods=['GET','POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        # Note: we pass session['username'] because `author` is TEXT
        add_post(
            form.title.data,
            form.content.data,
            session['username']
        )
        flash('Your post has been published!', 'success')
        return redirect(url_for('index'))

    return render_template('new_post.html', form=form)

@app.route('/post/<int:post_id>')
def view_post(post_id):
    post = get_post_by_id(post_id)
    if post is None:
        flash('Post not found.', 'warning')
        return redirect(url_for('index'))
    return render_template('view_post.html', post=post)

@app.template_filter('nl2br')
def nl2br_filter(s):
    """
    Replace newlines with <br> and mark the result safe HTML.
    """
    if s is None:
        return ''
    return Markup(s.replace('\n', '<br>\n'))

if __name__ == '__main__':
    app.run(debug=True)