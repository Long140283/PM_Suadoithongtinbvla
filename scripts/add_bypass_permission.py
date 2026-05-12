from app import create_app, db
from app.models import Permission

app = create_app()

with app.app_context():
    permission_name = 'bypass_financial_approval'
    permission_display_name = 'Gửi thẳng cho admin (bỏ qua duyệt tài chính)'
    
    # Check if the permission already exists
    permission = Permission.query.filter_by(name=permission_name).first()
    
    if not permission:
        new_permission = Permission(name=permission_name, display_name=permission_display_name)
        db.session.add(new_permission)
        db.session.commit()
        print(f"Permission '{permission_name}' created successfully.")
    else:
        print(f"Permission '{permission_name}' already exists.")