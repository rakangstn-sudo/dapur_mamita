"""
Model database Dapur Mamita.
Semua tabel didefinisikan di sini menggunakan SQLAlchemy ORM.
"""

from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db
from .constants import OrderStatus


class AdminUser(UserMixin, db.Model):
    """Akun admin untuk mengelola sistem."""
    __tablename__ = 'admin_users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<AdminUser {self.username}>'


class ProfilUMKM(db.Model):
    """Profil UMKM (single-row table)."""
    __tablename__ = 'profil_umkm'

    id = db.Column(db.Integer, primary_key=True)
    nama_umkm = db.Column(db.String(200), nullable=False, default='Dapur Mamita')
    deskripsi = db.Column(db.Text, default='')
    foto_url = db.Column(db.String(500), default='')
    alamat = db.Column(db.Text, default='')
    no_wa = db.Column(db.String(20), default='')
    jam_operasional = db.Column(db.String(200), default='')

    def __repr__(self):
        return f'<ProfilUMKM {self.nama_umkm}>'


class MenuItem(db.Model):
    """Item menu makanan/minuman."""
    __tablename__ = 'menu_items'

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(200), nullable=False)
    deskripsi = db.Column(db.Text, default='')
    harga = db.Column(db.Integer, nullable=False)  # dalam Rupiah
    foto_url = db.Column(db.String(500), default='')
    kategori = db.Column(db.String(50), nullable=False, default='Makanan', index=True)
    tersedia = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relasi ke detail pesanan
    detail_pesanan = db.relationship('DetailPesanan', backref='menu_item', lazy='dynamic')

    def __repr__(self):
        return f'<MenuItem {self.nama}>'


class Meja(db.Model):
    """Meja di restoran, masing-masing punya QR code unik."""
    __tablename__ = 'meja'

    id = db.Column(db.Integer, primary_key=True)
    nomor_meja = db.Column(db.Integer, unique=True, nullable=False)
    kode_unik = db.Column(db.String(20), unique=True, nullable=False, index=True)
    qr_image_url = db.Column(db.String(500), default='')

    # Relasi ke pesanan
    pesanan = db.relationship('Pesanan', backref='meja', lazy='dynamic')

    def __repr__(self):
        return f'<Meja {self.nomor_meja}>'


class Pesanan(db.Model):
    """Pesanan dari customer."""
    __tablename__ = 'pesanan'

    id = db.Column(db.Integer, primary_key=True)
    meja_id = db.Column(db.Integer, db.ForeignKey('meja.id'), nullable=True)
    nama_pemesan = db.Column(db.String(100), default='Pelanggan')
    tipe_pesanan = db.Column(db.String(50), default='Dine-in')
    meja_info = db.Column(db.String(50), default='')
    status = db.Column(
        db.String(20),
        nullable=False,
        default='menunggu',
        index=True
    )  # menunggu, diproses, selesai, dibatalkan
    total_harga = db.Column(db.Integer, nullable=False, default=0)
    catatan = db.Column(db.Text, default='')
    wa_url = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relasi ke detail
    detail_items = db.relationship(
        'DetailPesanan', backref='pesanan', lazy='joined',
        cascade='all, delete-orphan'
    )

    @property
    def status_label(self):
        return OrderStatus.get_label(self.status)

    @property
    def status_color(self):
        return OrderStatus.get_color(self.status)

    def __repr__(self):
        return f'<Pesanan #{self.id} Meja {self.meja_id}>'


class DetailPesanan(db.Model):
    """Detail item dalam satu pesanan."""
    __tablename__ = 'detail_pesanan'

    id = db.Column(db.Integer, primary_key=True)
    pesanan_id = db.Column(db.Integer, db.ForeignKey('pesanan.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=False)
    jumlah = db.Column(db.Integer, nullable=False, default=1)
    subtotal = db.Column(db.Integer, nullable=False, default=0)
    catatan_item = db.Column(db.String(300), default='')

    def __repr__(self):
        return f'<DetailPesanan {self.id} - Pesanan #{self.pesanan_id}>'
