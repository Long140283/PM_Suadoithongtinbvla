from app import create_app, db
from app.models import Role, Permission

app = create_app()

with app.app_context():
    # Find the finance role
    finance_role = Role.query.filter_by(name='finance').first()

    if finance_role:
        # Find the access_admin_dashboard permission
        admin_dashboard_permission = Permission.query.filter_by(name='access_admin_dashboard').first()

        if not admin_dashboard_permission:
            # Create the permission if it doesn't exist
            admin_dashboard_permission = Permission(name='access_admin_dashboard', display_name='Access Admin Dashboard')
            db.session.add(admin_dashboard_permission)
            db.session.commit()
            print("Permission 'access_admin_dashboard' created.")

        # Add the permission to the finance role if it's not already there
        if admin_dashboard_permission not in finance_role.permissions:
            finance_role.permissions.append(admin_dashboard_permission)
            db.session.commit()
            print("Permission 'access_admin_dashboard' added to 'finance' role.")
        else:
            print("Role 'finance' already has the 'access_admin_dashboard' permission.")
    else:
        print("Role 'finance' not found.")