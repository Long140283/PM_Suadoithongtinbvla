from app import create_app, db
from app.models import User

app = create_app()
app.app_context().push()

username = 'khang'
user = User.query.filter_by(username=username).first()

if user:
    print(f"User: {user.username}, Role: {user.role}")
else:
    print(f"User '{username}' not found.")
