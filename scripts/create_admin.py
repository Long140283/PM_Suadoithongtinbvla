from app import create_app
from app.models import User
from app.extensions import db

app = create_app()

with app.app_context():
    # Check if admin user exists
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(username='admin', email='admin@example.com', role='admin')
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created: username='admin', email='admin@example.com', role='admin', password='admin123'")
    else:
        print("Admin user already exists.")
