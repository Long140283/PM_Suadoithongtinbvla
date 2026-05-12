import logging
from flask import Flask, redirect, url_for
from config import Config
from .extensions import db, migrate, login_manager
from flask_wtf import CSRFProtect
from flask_bootstrap import Bootstrap


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    )

    # Extensions
    Bootstrap(app)
    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)
    login_manager.init_app(app)
    CSRFProtect(app)
    
    # Blueprints
    from .auth.routes import auth_bp
    from .admin import admin
    from .patient import patient_bp
    from .activity_report import activity_report_bp
    from .patient_search import patient_search_bp
    from .static_bp import static_bp
    from .screenshot_bp import screenshot_bp

    # Import patient sub-routes AFTER patient_bp is registered
    # This avoids circular import issues
    # Use __import__ to avoid shadowing the local 'app' variable
    __import__('app.patient.routes')
    __import__('app.patient.submission_routes')
    __import__('app.patient.dashboard_routes')
    __import__('app.patient.form_mgmt_routes')

    app.register_blueprint(static_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin,             url_prefix='/admin')
    app.register_blueprint(patient_bp,        url_prefix='/patient')
    app.register_blueprint(activity_report_bp, url_prefix='/activity_report')
    app.register_blueprint(patient_search_bp,  url_prefix='/patient_search')
    app.register_blueprint(screenshot_bp)

    # Context processors & filters
    from .context_processors import inject_dynamic_forms
    app.context_processor(inject_dynamic_forms)

    from .custom_filters import format_datetime_gmt7
    app.jinja_env.filters['datetime_gmt7'] = format_datetime_gmt7

    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    @app.route('/favicon.ico')
    def favicon():
        return '', 204

    # --- KHOI TAO OCR SAU CUNG DE TRANH LOI XUNG DOT THU VIEN (NUMPY/PANDAS) ---
    def delayed_ocr():
        import time
        time.sleep(2) # Cho phep app khoi dong xong hoan toan
        from .extensions import init_ocr
        init_ocr()

    import threading
    threading.Thread(target=delayed_ocr, daemon=True).start()

    return app
