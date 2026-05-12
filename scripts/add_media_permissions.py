import os
import sys
sys.path.append(os.getcwd())
from app import create_app, db
from app.models import Permission, Role

app = create_app()

def add_media_permissions():
    with app.app_context():
        # Permissions to add
        permissions_data = {
            'use_camera': 'Sử dụng Camera',
            'use_screenshot_full': 'Chụp toàn màn hình',
            'use_screenshot_region': 'Chụp theo vùng'
        }

        for perm_name, display_label in permissions_data.items():
            permission = Permission.query.filter_by(name=perm_name).first()
            if not permission:
                permission = Permission(name=perm_name, display_name=display_label)
                db.session.add(permission)
                print(f"Created '{perm_name}' permission.")
            else:
                permission.display_name = display_label
                print(f"'{perm_name}' permission already exists.")

            # Assign to admin and staff roles
            roles = Role.query.filter(Role.name.in_(['admin', 'staff'])).all()
            for role in roles:
                if permission not in role.permissions:
                    role.permissions.append(permission)
                    print(f"Assigned '{perm_name}' to role '{role.name}'.")

        db.session.commit()
        print("Done.")

if __name__ == '__main__':
    add_media_permissions()
