import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Konfigurasi utama aplikasi Flask."""

    # Flask core
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-ganti-di-production')
    FLASK_ENV = os.environ.get('FLASK_ENV', 'production')

    # Database: Supabase PostgreSQL (dengan fallback lokal SQLite jika .env belum diisi)
    _db_url = os.environ.get('DATABASE_URL', '')
    if _db_url.startswith('postgres://'):
        _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = _db_url if _db_url else 'sqlite:///dapur_mamita.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
    } if 'postgresql' in SQLALCHEMY_DATABASE_URI else {}

    # Supabase Storage
    SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')
    SUPABASE_BUCKET = os.environ.get('SUPABASE_BUCKET', 'dapur-mamita')

    # Upload settings
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2 MB
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

    # Base URL (untuk generate QR code)
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')
