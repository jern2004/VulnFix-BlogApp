# VulnFix-BlogApp

**You are on the `main` branch.** This is the secure, fixed version of the app.
Every vulnerability described below has been patched here.

If you want to practice attacking the actual vulnerabilities yourself, switch to
the intentionally-broken version of this exact app:

```bash
git checkout vulnerable
```

## What this project is

VulnFix-BlogApp is a small Flask blog built as a hands-on security learning
project. It went through a real cycle: build features, find what's broken,
exploit it, fix it, write it all down. Both halves of that cycle are preserved
so students can walk through the same thing themselves.

- **`vulnerable` branch**: the broken version, safe to attack in a local
  sandbox. Has its own guide at `docs/vulnerabilities.md` on that branch.
- **`main` branch (this one)**: the fixed version, plus a real pentest report
  covering issues found beyond the original six.

Two documents matter here:

- [`docs/vulnerabilities.md`](docs/vulnerabilities.md): one section per original
  vulnerability. Explains what it is, why the vulnerable code causes it, exact
  steps to exploit it on the `vulnerable` branch, and the fixed code shown here.
- [`docs/pentesting_report.md`](docs/pentesting_report.md): a from-scratch
  security assessment run against this fixed branch, which found five more
  real issues (a hardcoded secret key allowing full session forgery, missing
  CSRF protection on login/register, weak cookie flags, and no rate limiting)
  that were not part of the original six and are also fixed here. This report
  is the source of truth on this branch's current security status.

## What got fixed

| # | Vulnerability | Fixed with |
|---|---|---|
| 1 | SQL Injection | Parameterized `?` queries everywhere |
| 2 | Cross-Site Scripting (XSS) | Post content escaped with `markupsafe.escape()` before render |
| 3 | Broken Access Control | `/admin` requires login and an `is_admin` database flag, checked on every request |
| 4 | Insecure Password Storage | Passwords hashed with `werkzeug.security`, minimum 8 characters enforced |
| 5 | CSRF | `Flask-WTF` `CSRFProtect` enabled app-wide, every form carries a token |
| 6 | Weak Session Management | Cookie now sets `HttpOnly`, `SameSite=Lax`, and an env-driven `Secure` flag; `SECRET_KEY` must come from the environment, no hardcoded fallback |

Full detail and exploit-vs-fix comparisons for each: `docs/vulnerabilities.md`.
Additional findings from the real pentest pass: `docs/pentesting_report.md`.

## Setup

### Prerequisites
- Python 3.8+
- pip
- (Recommended) a virtual environment

### Install

```bash
git clone https://github.com/jern2004/VulnFix-BlogApp.git
cd VulnFix-BlogApp
python3 -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Required environment variable

This app refuses to start without a `SECRET_KEY`. It no longer falls back to a
hardcoded default, since that was itself one of the vulnerabilities found (see
`docs/pentesting_report.md`, section 3.2). Generate one and set it before
running:

```bash
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
python run.py
```

On Windows PowerShell:

```powershell
$env:SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
python run.py
```

Open `http://127.0.0.1:5000`.

### Making a user an admin

There's no admin-promotion UI. Set the flag directly in the database:

```bash
sqlite3 app/database.db "UPDATE users SET is_admin=1 WHERE username='yourname';"
```

## Functional features

- User registration and login (passwords hashed)
- Post creation, editing (within a 1 hour window), and author-only deletion
- Filtered and sorted post search
- Admin dashboard (`/admin`), gated on the `is_admin` flag
