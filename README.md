# VulnFix-BlogApp
Build a deliberately vulnerable blog app, exploit the flaws (pentesting), then fix them and document everything.
# VulnFix-BlogApp

## 🛡️ Overview

VulnFix-BlogApp is a deliberately vulnerable Flask-based web application that mimics a simple blogging platform. The purpose of this project is to:

- Build and deploy a working web app with common security flaws
- Practice ethical hacking and manual vulnerability discovery
- Demonstrate how to fix the vulnerabilities using secure coding practices
- Document the process for educational and professional reference

---

## 🚀 Features

### Functional Features
- User Registration and Login
- Post creation and viewing
- Admin-only dashboard
- Post search functionality

### Vulnerabilities Implemented
| Vulnerability Type | Description |
|--------------------|-------------|
| SQL Injection (SQLi) | In the search functionality using raw SQL |
| Cross-Site Scripting (XSS) | In post creation and rendering |
| Broken Access Control | No proper role checks for admin routes |
| Insecure Password Storage | Plaintext password storage in database |
| CSRF | No token protection on forms |
| Weak Session Management | Missing `secure` and `httponly` cookie flags |

---

## ⚙️ Setup Instructions

### 🧩 Prerequisites
- Python 3.8+
- pip
- (Recommended) Virtual environment

### 📦 Installation

```bash
git clone https://github.com/jern2004/VulnFix-BlogApp.git
cd VulnFix-BlogApp
python3 -m venv venv
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
pip install -r requirements.txt
```
