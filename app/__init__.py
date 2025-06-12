from flask import Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'vulnfixdev'  # Insecure by design
from app import routes