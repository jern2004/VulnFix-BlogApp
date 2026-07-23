# VulnFix-BlogApp

**You are on the `vulnerable` branch.** Every vulnerability described below is
live and exploitable in this code, on purpose. This is a practice target, not a
real app: do not deploy this branch anywhere reachable by the public internet,
and do not reuse a real password when registering an account here.

The fixed version of this exact app lives on the `main` branch:

```bash
git checkout main
```

## What this project is

VulnFix-BlogApp is a small Flask blog built as a hands-on security learning
project. It went through a real cycle of building features, discovering what
was broken, exploiting it, and fixing it. Both halves of that cycle are
preserved here so students can do the same thing themselves:

- **`vulnerable` branch (this one)**: the broken version, safe to attack in a
  local sandbox.
- **`main` branch**: the same app, fixed, plus a full write-up of a real
  pentest that found additional issues beyond the ones listed below.

Start with [`docs/vulnerabilities.md`](docs/vulnerabilities.md). That's the main
guide: what each vulnerability is, why the code causes it, exact steps to
exploit it yourself against this running app, what a real attacker would do
with it, and the fixed code you'll find on `main`.

## Vulnerabilities in this branch

| # | Vulnerability | Where |
|---|---|---|
| 1 | SQL Injection | `/search`, raw string built into the query |
| 2 | Cross-Site Scripting (XSS) | Post content rendered without escaping |
| 3 | Broken Access Control | `/admin` has no login or role check |
| 4 | Insecure Password Storage | Passwords saved as plaintext |
| 5 | CSRF | No tokens on any form, CSRF checking disabled entirely |
| 6 | Weak Session Management | Cookie missing `HttpOnly`/`Secure`/`SameSite`, hardcoded secret key |

Full detail, exploit steps, and fixes for each: [`docs/vulnerabilities.md`](docs/vulnerabilities.md).

## Setup

### Prerequisites
- Python 3.8+
- pip
- (Recommended) a virtual environment

### Install

```bash
git clone https://github.com/jern2004/VulnFix-BlogApp.git
cd VulnFix-BlogApp
git checkout vulnerable
python3 -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Run

No environment variables are required on this branch (that's part of
vulnerability 6, see the guide):

```bash
python run.py
```

Open `http://127.0.0.1:5000`.

## Suggested exercise order

1. Register a throwaway account and log in.
2. Try the SQL injection against the search box (Section 1 of the guide).
   You do not even need an account for this one.
3. Create a post containing an XSS payload and view it (Section 2).
4. Log out and visit `/admin` directly (Section 3).
5. Look at what got stored for your throwaway account's password (Section 4).
6. Use the provided PoC to CSRF-delete one of your own posts (Section 5).
7. Inspect the `Set-Cookie` response header and try the session-forging script
   (Section 6).
8. Switch to `main`, repeat steps 2 through 7, and confirm each one is now
   blocked.

## Functional features (unrelated to the vulnerabilities)

- User registration and login
- Post creation, editing (within a 1 hour window), and author-only deletion
- Filtered and sorted post search
- An admin dashboard (deliberately unprotected on this branch)
