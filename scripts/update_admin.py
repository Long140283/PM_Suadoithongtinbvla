from app import create_app
from app.models import User
from app.extensions import db

app = create_app()

with app.app_context():
    admin_user = User.query.filter_by(username='admin').first()
    if admin_user:
        admin_user.role = 'admin'
        db.session.commit()
        print("Admin user role updated to 'admin'")
    else:
        print("Admin user not found.")
