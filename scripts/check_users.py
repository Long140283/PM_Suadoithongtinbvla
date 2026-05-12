from app import create_app
app = create_app()
with app.app_context():
    from app import db
    from app.models import User
    users = User.query.all()
    print([(u.username, u.role) for u in users])
