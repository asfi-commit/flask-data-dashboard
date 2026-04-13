from app import app
from models import db

# Create database inside Flask app context
with app.app_context():
    db.create_all()
    print("Database created successfully!")