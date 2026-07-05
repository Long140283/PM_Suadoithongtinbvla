"""
Entry point cua ung dung.
Khoi tao DB, tao du lieu mac dinh, chay server.
"""
import os
import logging
from datetime import timedelta

from app import create_app, db
from app.models import User, Permission, Role
from app.constants import Permissions, Roles

logger = logging.getLogger(__name__)

app = create_app()
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)

# --- Thong tin server da duoc create_app() tu dong detect va luu vao config ---
_hostname = app.config.get('SERVER_HOSTNAME')
_local_ip = app.config.get('SERVER_LOCAL_IP')
_port     = app.config.get('SERVER_PORT')


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
    """Tao vai tro voi danh sach quyen neu chua co. Cap nhat quyen moi neu role da ton tai."""
    role = Role.query.filter_by(name=role_name).first()
    if not role:
        role = Role(name=role_name)
        perms = Permission.query.filter(Permission.name.in_(perm_names)).all()
        role.permissions.extend(perms)
        db.session.add(role)
        db.session.commit()
        logger.info('Da tao vai tro: %s', role_name)
    else:
        # Them cac quyen moi chua co trong role
        existing_perm_names = {p.name for p in role.permissions}
        new_perms = Permission.query.filter(
            Permission.name.in_(perm_names),
            ~Permission.name.in_(existing_perm_names)
        ).all()
        if new_perms:
            role.permissions.extend(new_perms)
            db.session.commit()
            logger.info('Da cap nhat quyen moi cho vai tro %s: %s',
                        role_name, [p.name for p in new_perms])
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

    port = _port
    url  = f'http://{_local_ip}:{port}'

    # --- In QR code ra console de dien thoai quet ---
    def _print_qr_console(data):
        try:
            import qrcode
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=1,
                border=1,
            )
            qr.add_data(data)
            qr.make(fit=True)
            # In bang ky tu Unicode block (hien thi dep tren Windows Terminal)
            matrix = qr.get_matrix()
            print()
            for row in matrix:
                line = ''
                for cell in row:
                    line += '██' if cell else '  '
                print('  ' + line)
            print()
        except Exception as e:
            print(f'  (Khong hien thi duoc QR: {e})')

    print('=' * 60)
    print('  ỨNG DỤNG ĐANG CHẠY')
    print('=' * 60)
    print(f'  PC/Laptop (tên máy): http://{_hostname}:{port}')
    print(f'  Điện thoại (IP LAN): {url}')
    print()
    print('  Quét QR bằng điện thoại để truy cập:')
    _print_qr_console(url)
    print(f'  URL: {url}')
    print('=' * 60)

if __name__ == '__main__':
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    if debug:
        app.run(host='0.0.0.0', port=_port, debug=True)
    else:
        from waitress import serve
        serve(app, host='0.0.0.0', port=_port)
