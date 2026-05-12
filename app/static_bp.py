from flask import Blueprint, send_from_directory

static_bp = Blueprint('static_bp', __name__, static_folder='static', static_url_path='/static')