from flask import Blueprint

patient_search_bp = Blueprint(
    'patient_search',
    __name__,
    template_folder='templates',
    static_folder='static'
)

from . import routes