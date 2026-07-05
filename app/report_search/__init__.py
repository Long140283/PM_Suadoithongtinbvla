from flask import Blueprint

report_search_bp = Blueprint('report_search', __name__, template_folder='templates')

from . import routes
