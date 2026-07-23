# Development Plan

> This describes the fixed flows on the `main` branch. The `vulnerable` branch has
> its own version of this file describing the intentionally-broken version of the
> same app. See [`vulnerabilities.md`](vulnerabilities.md) for exploit walkthroughs
> of the original six vulnerabilities, and [`pentesting_report.md`](pentesting_report.md)
> for a handful of additional issues found during a real assessment of this fixed code.

## Data Models

### users table
- **id**: INTEGER PRIMARY KEY AUTOINCREMENT
- **username**: TEXT UNIQUE NOT NULL
- **password**: TEXT NOT NULL   # hashed via `werkzeug.security.generate_password_hash`
- **email**: TEXT UNIQUE NOT NULL
- **is_admin**: INTEGER DEFAULT 0

### posts table
- **id**: INTEGER PRIMARY KEY AUTOINCREMENT
- **title**: TEXT NOT NULL
- **content**: TEXT NOT NULL    # escaped on render via the `nl2br` filter, not stored escaped
- **author**: TEXT NOT NULL     # username, not a foreign key
- **created_at**: TIMESTAMP DEFAULT CURRENT_TIMESTAMP

## Pseudocode Flows

### 1. Register (`/register`)
- If GET: render `register.html` (includes CSRF token)
- If POST:
  - Reject if password is under 8 characters
  - Reject if username or email already taken
  - Hash password with `generate_password_hash`, insert via parameterized query
  - Redirect to `/login`

### 2. Login (`/login`)
- If GET: render `login.html` (includes CSRF token)
- If POST:
  - Look up user by username (parameterized query)
  - Verify password with `check_password_hash`
  - On success: `session['username'] = user.username`, redirect to `/`
  - On failure: flash "Invalid username or password"

### 3. Create / Edit Post (`/post/new`, `/post/edit/<id>`)
- Requires `login_required`
- Uses a `FlaskForm` (`PostForm`), CSRF-protected and server-validated
- Edit is author-only and only allowed within 1 hour of creation

### 4. Delete Post (`/post/delete/<id>`)
- Requires `login_required`, author-only
- Form includes a CSRF token; request rejected with 400 if missing/invalid

### 5. View Post (`/post/<id>`)
- Parameterized lookup by id
- Content rendered through the `nl2br` filter, which HTML-escapes it before
  re-inserting `<p>`/`<br>` tags, which prevents stored XSS

### 6. Search Posts (`/search`)
- Reads `q`, `filter`, `sort` query params
- All queries use parameterized `?` placeholders, no string interpolation into SQL

### 7. Admin Page (`/admin`)
- Requires `login_required` **and** `session_user.is_admin == 1` (checked against
  the DB on every request, not cached in the session)
- Anonymous → redirect to `/login`; logged-in non-admin → redirect to `/` with a
  flash message; renders a user + post table for admins
