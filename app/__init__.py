"""
App Factory — Dapur Mamita
Inisialisasi Flask app, register semua extension dan blueprint.
"""

import os
from flask import Flask
from .config import Config
from .extensions import db, migrate, login_manager, csrf


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inisialisasi extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Pastikan folder qrcodes ada (abaikan jika serverless read-only)
    try:
        qr_folder = os.path.join(app.static_folder, 'qrcodes')
        os.makedirs(qr_folder, exist_ok=True)
    except OSError:
        pass

    # Import models agar dikenali Migrate
    from . import models  # noqa: F401

    # Register blueprints
    from .main import main_bp
    app.register_blueprint(main_bp)

    from .order import order_bp
    app.register_blueprint(order_bp, url_prefix='/order')

    from .auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from .admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from .api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    # User loader untuk Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return models.AdminUser.query.get(int(user_id))

    return app
