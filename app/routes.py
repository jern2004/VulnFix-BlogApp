from app import app

@app.route("/")
def home():
    return "<h1>VulnFix-BlogApp Home</h1>"