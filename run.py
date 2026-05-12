"""
Entry point cua ung dung.
Khoi tao DB, tao du lieu mac dinh, chay server.
"""
import os
import socket
import logging
from datetime import timedelta

from app import create_app, db
from app.models import User, Permission, Role
from app.constants import Permissions, Roles

logger = logging.getLogger(__name__)

app = create_app()
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)


def _seed_permissions():
    """Tao cac quyen mac dinh neu chua co."""
    for name, display in Permissions.DISPLAY_NAMES.items():
        perm = Permission.query.filter_by(name=name).first()
        if not perm:
            db.session.add(Permission(name=name, display_name=display))
        else:
            perm.display_name = display
    db.session.commit()


def _seed_role(role_name, perm_names):
    """Tao vai tro voi danh sach quyen neu chua co."""
    role = Role.query.filter_by(name=role_name).first()
    if not role:
        role = Role(name=role_name)
        perms = Permission.query.filter(Permission.name.in_(perm_names)).all()
        role.permissions.extend(perms)
        db.session.add(role)
        db.session.commit()
        logger.info('Da tao vai tro: %s', role_name)
    return role


def _seed_admin_user(admin_role):
    """Tao tai khoan admin mac dinh neu chua co."""
    if not User.query.filter_by(username='admin').first():
        user = User(username='admin', full_name='Admin User', email='admin@example.com')
        user.set_password('admin123')
        user.roles.append(admin_role)
        db.session.add(user)
        db.session.commit()
        logger.info('Da tao tai khoan admin mac dinh (mat khau: admin123)')
    else:
        logger.info('Tai khoan admin da ton tai.')


with app.app_context():
    db.create_all()
    _seed_permissions()

    admin_role   = _seed_role(Roles.ADMIN,   list(Permissions.DISPLAY_NAMES.keys()))
    _seed_role(Roles.STAFF,   [Permissions.VIEW_PATIENT, Permissions.CREATE_REQUEST])
    _seed_role(Roles.FINANCE, [Permissions.VIEW_PATIENT, Permissions.APPROVE_REQUEST,
                                Permissions.ACCESS_ADMIN_DASHBOARD])

    _seed_admin_user(admin_role)

    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    logger.info('Su dung co so du lieu: %s', db_uri)

    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except socket.gaierror:
        local_ip = '127.0.0.1'

    print('-' * 50)
    print('Ung dung dang chay!')
    print(f'  http://{local_ip}:8001')
    print(f'  http://{hostname}:8001')
    print('-' * 50)

if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    if debug:
        app.run(host='0.0.0.0', port=8001, debug=True)
    else:
        from waitress import serve
        serve(app, host='0.0.0.0', port=8001)
