from app import create_app, db
from app.models import User
import os
import sys


app = create_app()

with app.app_context():
    admin_username = 'admin'
    admin_password = 'adminpassword'

    admin_user = User.query.filter_by(username=admin_username).first()

    if not admin_user:
        print(f"Creating admin user '{admin_username}'...")
        admin_user = User(username=admin_username, is_admin=True)
        admin_user.set_password(admin_password)
        db.session.add(admin_user)
        try:
            db.session.commit()
            print("Admin user created successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating admin user: {e}")
    else:
        print(f"Admin user '{admin_username}' already exists.")