"""
Cau hinh ung dung.
Dung bien moi truong de ghi de gia tri mac dinh khi deploy.
"""
import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Bao mat - PHAI dat bien moi truong SECRET_KEY khi deploy
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-only-change-in-production'

    # Database
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get('DATABASE_URL')
        or 'sqlite:///' + os.path.join(basedir, 'new_database.db') + '?timeout=60'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')

    # Session
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True  # Yeu cau HTTPS


# Map ten -> class de dung trong run.py neu can
config_map = {
    'development': DevelopmentConfig,
    'production':  ProductionConfig,
    'default':     DevelopmentConfig,
}
