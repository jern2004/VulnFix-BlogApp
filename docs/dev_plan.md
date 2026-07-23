# Development Plan (vulnerable branch)

This describes the architecture of the app as it actually exists on the
`vulnerable` branch. For an exploit-by-exploit walkthrough of what's wrong with
each piece, see [`vulnerabilities.md`](vulnerabilities.md). The `main` branch has
its own version of this file describing the fixed flows.

## Data Models

### users table
- **id**: INTEGER PRIMARY KEY AUTOINCREMENT
- **username**: TEXT NOT NULL UNIQUE
- **password**: TEXT NOT NULL, stored in plaintext, see vulnerability 4
- **email**: TEXT NOT NULL UNIQUE
- **is_admin**: INTEGER DEFAULT 0, never actually checked anywhere on this branch

### posts table
- **id**: INTEGER PRIMARY KEY AUTOINCREMENT
- **title**: TEXT NOT NULL
- **content**: TEXT NOT NULL, rendered without escaping, see vulnerability 2
- **author**: TEXT NOT NULL, the username, not a foreign key
- **created_at**: TIMESTAMP DEFAULT CURRENT_TIMESTAMP

## Pseudocode Flows

### 1. Register (`/register`)
- If GET: render `register.html` (no CSRF token field)
- If POST:
  - Read `username`, `email`, `password` from the form
  - Reject only if the username or email is already taken
  - Insert the password into the database exactly as submitted, no hashing
  - Redirect to `/login`

### 2. Login (`/login`)
- If GET: render `login.html` (no CSRF token field)
- If POST:
  - Look up the user by username
  - Compare the submitted password to the stored value with `==`
  - On match: `session['username'] = user.username`, redirect to `/`
  - On failure: flash "Invalid username or password"
  - No rate limiting, so this can be brute forced

### 3. Create / Edit Post (`/post/new`, `/post/edit/<id>`)
- Requires `login_required` (a logged-in session, nothing more)
- Uses a `FlaskForm` (`PostForm`), but app-wide CSRF checking is turned off
  (`WTF_CSRF_ENABLED = False`), so the form's own token is never validated
- Edit is limited to the original author and only within 1 hour of creation

### 4. Delete Post (`/post/delete/<id>`)
- Requires `login_required`, author-only
- The form has no CSRF token, and there is no server-side check for one, so
  this endpoint can be triggered by a forged cross-site request

### 5. View Post (`/post/<id>`)
- Looks up the post by id
- Renders `post.content` through the `nl2br` filter, which does not escape the
  content before wrapping it in HTML, so any HTML or `<script>` in a post
  executes for every viewer

### 6. Search Posts (`/search`)
- Reads `q`, `filter`, `sort` from the query string
- Builds the SQL query with an f-string, splicing `q` directly into the
  statement instead of binding it as a parameter, so `q` can inject arbitrary
  SQL

### 7. Admin Page (`/admin`)
- No login check, no `is_admin` check, nothing
- Queries every user (including their plaintext password) and every post, and
  renders them for anyone who requests the URL
