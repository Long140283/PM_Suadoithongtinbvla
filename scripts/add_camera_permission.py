import os
import sys
sys.path.append(os.getcwd())
from app import create_app, db
from app.models import Permission, Role

app = create_app()

def add_camera_permission():
    with app.app_context():
        # Add the 'use_camera' permission
        permission = Permission.query.filter_by(name='use_camera').first()
        if not permission:
            permission = Permission(name='use_camera', display_name='Sử dụng Camera')
            db.session.add(permission)
            print("Created 'use_camera' permission.")
        else:
            print("'use_camera' permission already exists.")

        # Assign it to all roles except perhaps finance if needed, 
        # but let's just make it available for the admin to assign.
        # Actually, let's assign it to 'admin' and 'staff' by default.
        roles = Role.query.filter(Role.name.in_(['admin', 'staff'])).all()
        for role in roles:
            if permission not in role.permissions:
                role.permissions.append(permission)
                print(f"Assigned 'use_camera' to role '{role.name}'.")

        db.session.commit()
        print("Done.")

if __name__ == '__main__':
    add_camera_permission()
