
import sys
import os
from app import app, db


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def create_database():
    with app.app_context():
        db.create_all()
        print("Database and tables created inside app folder.")

if __name__ == '__main__':
    create_database()
