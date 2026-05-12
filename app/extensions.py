from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    from .models import User
    return User.query.get(int(user_id))

ocr_reader = None

def init_ocr():
    global ocr_reader
    try:
        import easyocr
        import logging
        logging.info("Initializing EasyOCR (Vietnamese)...")
        # Initialize reader once
        ocr_reader = easyocr.Reader(['vi'], gpu=True)
        logging.info("EasyOCR Ready!")
    except Exception as e:
        import logging
        logging.error(f"Failed to initialize EasyOCR: {e}")
