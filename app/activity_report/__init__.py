from flask import Blueprint

activity_report_bp = Blueprint('activity_report', __name__, template_folder='templates')

from . import routes