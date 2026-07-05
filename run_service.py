"""
run_service.py
--------------
Entry point danh cho NSSM chay nen (background service).
- Khoi tao DB, seed du lieu
- Ghi server_info.txt de show_qr.pyw doc
- Chay Waitress voi cac tham so toi uu cho 24/7

NSSM config:
  Path       : C:\\...\\venv\\Scripts\\python.exe
  AppDir     : C:\\...\\PM_SuaDoiThongTin
  Arguments  : run_service.py
"""

import os
import sys
import socket
import logging
import logging.handlers
from datetime import timedelta

# ---------------------------------------------------------------
# Logging ra file (quan trong khi chay nen - khong co console)
# ---------------------------------------------------------------
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
LOG_FILE  = os.path.join(BASE_DIR, 'service_log.txt')
INFO_FILE = os.path.join(BASE_DIR, 'server_info.txt')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        # Xoay vong log: moi file 5 MB, giu 3 file
        logging.handlers.RotatingFileHandler(
            LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding='utf-8'
        ),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------
# Import app
# ---------------------------------------------------------------
from app import create_app, db
from app.models import User, Permission, Role
from app.constants import Permissions, Roles

SERVER_HOSTNAME_FIXED = 'SDTTBV'
_port = int(os.environ.get('PORT', 8001))


def _get_lan_ip():
    """Lay IP LAN thuc su, bo qua virtual adapter."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if not ip.startswith('127.') and not ip.startswith('169.254.'):
                return ip
    except Exception:
        pass
    return '127.0.0.1'


# ---------------------------------------------------------------
# Tao app va cau hinh
# ---------------------------------------------------------------
app = create_app()
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)

_local_ip = _get_lan_ip()
_hostname = SERVER_HOSTNAME_FIXED

app.config['SERVER_HOSTNAME']  = _hostname
app.config['SERVER_LOCAL_IP']  = _local_ip
app.config['SERVER_PORT']      = _port


# ---------------------------------------------------------------
# Seed DB
# ---------------------------------------------------------------
def _seed_permissions():
    for name, display in Permissions.DISPLAY_NAMES.items():
        perm = Permission.query.filter_by(name=name).first()
        if not perm:
            db.session.add(Permission(name=name, display_name=display))
        else:
            perm.display_name = display
    db.session.commit()


def _seed_role(role_name, perm_names):
    role = Role.query.filter_by(name=role_name).first()
    if not role:
        role = Role(name=role_name)
        perms = Permission.query.filter(Permission.name.in_(perm_names)).all()
        role.permissions.extend(perms)
        db.session.add(role)
        db.session.commit()
        logger.info('Da tao vai tro: %s', role_name)
    else:
        existing = {p.name for p in role.permissions}
        new_perms = Permission.query.filter(
            Permission.name.in_(perm_names),
            ~Permission.name.in_(existing)
        ).all()
        if new_perms:
            role.permissions.extend(new_perms)
            db.session.commit()
            logger.info('Cap nhat quyen moi cho %s: %s', role_name, [p.name for p in new_perms])
    return role


def _seed_admin_user(admin_role):
    if not User.query.filter_by(username='admin').first():
        user = User(username='admin', full_name='Admin User', email='admin@example.com')
        user.set_password('admin123')
        user.roles.append(admin_role)
        db.session.add(user)
        db.session.commit()
        logger.info('Da tao tai khoan admin mac dinh')


# ---------------------------------------------------------------
# Khoi dong
# ---------------------------------------------------------------
with app.app_context():
    db.create_all()
    _seed_permissions()
    admin_role = _seed_role(Roles.ADMIN, list(Permissions.DISPLAY_NAMES.keys()))
    _seed_role(Roles.STAFF,   [Permissions.VIEW_PATIENT, Permissions.CREATE_REQUEST])
    _seed_role(Roles.FINANCE, [Permissions.VIEW_PATIENT, Permissions.APPROVE_REQUEST,
                                Permissions.ACCESS_ADMIN_DASHBOARD])
    _seed_admin_user(admin_role)

    url = f'http://{_local_ip}:{_port}'

    # Ghi server_info.txt de show_qr.pyw hien popup QR
    try:
        with open(INFO_FILE, 'w', encoding='utf-8') as f:
            f.write(f'url={url}\n')
            f.write(f'hostname={_hostname}\n')
            f.write(f'port={_port}\n')
        logger.info('Da ghi server_info.txt: %s', url)
    except Exception as e:
        logger.warning('Khong ghi duoc server_info.txt: %s', e)

    logger.info('=' * 60)
    logger.info('  MAY CHU DANG CHAY (WAITRESS - 24/7 SERVICE)')
    logger.info('  PC/Laptop : http://%s:%s', _hostname, _port)
    logger.info('  IP LAN    : %s', url)
    logger.info('=' * 60)


if __name__ == '__main__':
    from waitress import serve

    logger.info('Khoi dong Waitress server...')

    serve(
        app,
        host='0.0.0.0',
        port=_port,

        # --- Thread pool ---
        threads=8,                  # So luong thread xu ly request dong thoi

        # --- Timeout & connection (quan trong cho 24/7) ---
        channel_timeout=120,        # Dong connection treo sau 120s
        connection_limit=200,       # Gioi han ket noi dong thoi
        cleanup_interval=30,        # Quet don ket noi cu moi 30s

        # --- Logging ---
        ident='BenhVienLongAn',     # Ten hien thi trong Server header
    )
