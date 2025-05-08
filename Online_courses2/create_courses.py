from app import create_app, db
from app.models import Course, User
import sys
import os


app = create_app()

def create_initial_courses():
    admin_username = 'admin'
    admin = User.query.filter_by(username=admin_username).first()

    if not admin:
        print(f"Admin user '{admin_username}' not found. Please run create_admin.py first.")
        sys.exit(1)

    if Course.query.first():
        print("Courses seem to exist already. Skipping creation.")
        return

    print("Creating initial courses...")
    try:
        course1 = Course(title="Python for Beginners", description="Learn Python from scratch.", instructor="John Doe", creator=admin)
        course2 = Course(title="Advanced Flask", description="Deep dive into Flask.", instructor="Jane Smith", creator=admin)
        course3 = Course(title="Web Development with Flask", description="Master web development using Flask.", instructor="Alice Brown", creator=admin)

        db.session.add_all([course1, course2, course3])
        db.session.commit()
        print("Courses have been created successfully and assigned to admin.")
    except Exception as e:
        db.session.rollback()
        print(f"An error occurred while creating courses: {e}")

if __name__ == "__main__":
    with app.app_context():
        create_initial_courses()