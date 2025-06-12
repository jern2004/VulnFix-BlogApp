# Development Plan

## Data Models

### users table
- **id**: INTEGER PRIMARY KEY AUTOINCREMENT  
- **username**: TEXT UNIQUE  
- **password**: TEXT           # stored in plaintext for the vulnerable version

### posts table
- **id**: INTEGER PRIMARY KEY AUTOINCREMENT  
- **title**: TEXT  
- **body**: TEXT               # raw HTML allowed  
- **author_id**: INTEGER       # references users.id  
- **created_at**: DATETIME     # timestamp of post creation

## Pseudocode Flows

### 1. Register (`/register`)
- If GET:
  - Render `register.html`
- If POST:
  - Read `username` and `password` from `request.form`
  - Insert into DB:
    `INSERT INTO users (username, password) VALUES ('{username}', '{password}')`
  - Redirect to `/login`

### 2. Login (`/login`)
- If GET:
  - Render `login.html`
- If POST:
  - Read `username` and `password`
  - Query DB:
    `SELECT id FROM users WHERE username = '{username}' AND password = '{password}'`
  - If a row is returned:
    - Set `session['user_id'] = id`
    - Redirect to `/`
  - Else:
    - Show “Invalid credentials”

### 3. Create Post (`/post/new`)
- If GET:
  - Render `new_post.html`
- If POST:
  - Read `title` and `body` from form
  - Insert into DB:
    `INSERT INTO posts (title, body, author_id, created_at) VALUES ('{title}', '{body}', session['user_id'], CURRENT_TIMESTAMP)`
  - Redirect to `/post/{new_id}`

### 4. View Post (`/post/<id>`)
- Query `SELECT title, body, author_id, created_at FROM posts WHERE id = {id}`
- Render `view_post.html`, passing raw `body` (XSS here)

### 5. Search Posts (`/search`)
- Read query param `q`
- Query DB:
  `SELECT id, title FROM posts WHERE title LIKE '%{q}%'`
- Render `search.html` with results

### 6. Admin Page (`/admin`)
- No checks
- Query all users/posts and render `admin.html`
