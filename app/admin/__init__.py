from flask import Blueprint

admin = Blueprint('admin', __name__, template_folder='templates')

from . import routes, user_routes, audit_routes, permission_routes