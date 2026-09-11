"""
App Factory — Dapur Mamita
Inisialisasi Flask app, register semua extension dan blueprint.
"""

import os
from flask import Flask, render_template
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

    # Context processor global untuk template Jinja2
    @app.context_processor
    def inject_global_data():
        try:
            profil = models.ProfilUMKM.query.first()
        except Exception:
            profil = None

        raw_wa = profil.no_wa if profil and profil.no_wa else '6282118403965'
        clean_wa = ''.join(c for c in raw_wa if c.isdigit())
        if clean_wa.startswith('0'):
            clean_wa = '62' + clean_wa[1:]

        return {
            'current_profil': profil,
            'store_whatsapp': clean_wa
        }

    # Error handlers halaman ramah pengguna
    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        return render_template('errors/500.html'), 500

    return app
