"""
Form WTForms untuk Dapur Mamita.
Validasi + CSRF protection.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField, PasswordField, TextAreaField, IntegerField,
    BooleanField, SelectField, SubmitField
)
from wtforms.validators import (
    DataRequired, Length, NumberRange, Optional, ValidationError
)
from .constants import MenuCategory, OrderType, AppDefaults


class LoginForm(FlaskForm):
    """Form login admin."""
    username = StringField(
        'Username',
        validators=[DataRequired(message='Username wajib diisi.')]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired(message='Password wajib diisi.')]
    )
    submit = SubmitField('Login')


class MenuForm(FlaskForm):
    """Form CRUD menu item."""
    nama = StringField(
        'Nama Menu',
        validators=[
            DataRequired(message='Nama menu wajib diisi.'),
            Length(max=200, message='Maksimal 200 karakter.')
        ]
    )
    deskripsi = TextAreaField(
        'Deskripsi',
        validators=[Optional()]
    )
    harga = IntegerField(
        'Harga (Rp)',
        validators=[
            DataRequired(message='Harga wajib diisi.'),
            NumberRange(min=1, message='Harga harus lebih dari 0.')
        ]
    )
    kategori = SelectField(
        'Kategori',
        choices=MenuCategory.CHOICES,
        validators=[DataRequired()]
    )
    tersedia = BooleanField('Tersedia', default=True)
    foto = FileField(
        'Upload File Foto (JPG/PNG)',
        validators=[
            FileAllowed(['jpg', 'jpeg', 'png'], 'Hanya file JPG/PNG yang diizinkan.'),
        ]
    )
    foto_url_input = StringField(
        'Atau Masukkan Link / URL Foto',
        validators=[Optional(), Length(max=500)]
    )
    submit = SubmitField('Simpan')

    def validate_foto(self, field):
        """Validasi ukuran file maksimal 2MB."""
        if field.data:
            # Cek ukuran file
            field.data.seek(0, 2)  # pindah ke akhir file
            size = field.data.tell()
            field.data.seek(0)  # kembali ke awal
            if size > 2 * 1024 * 1024:
                raise ValidationError('Ukuran file maksimal 2MB.')


class MejaForm(FlaskForm):
    """Form tambah meja baru."""
    nomor_meja = IntegerField(
        'Nomor Meja',
        validators=[
            DataRequired(message='Nomor meja wajib diisi.'),
            NumberRange(min=1, message='Nomor meja harus lebih dari 0.')
        ]
    )
    submit = SubmitField('Tambah Meja')


class ProfilForm(FlaskForm):
    """Form edit profil UMKM."""
    nama_umkm = StringField(
        'Nama UMKM',
        validators=[
            DataRequired(message='Nama UMKM wajib diisi.'),
            Length(max=200)
        ]
    )
    deskripsi = TextAreaField(
        'Deskripsi',
        validators=[Optional()]
    )
    alamat = TextAreaField(
        'Alamat',
        validators=[Optional()]
    )
    no_wa = StringField(
        'Nomor WhatsApp',
        validators=[Optional(), Length(max=20)]
    )
    jam_operasional = StringField(
        'Jam Operasional',
        validators=[Optional(), Length(max=200)]
    )
    foto = FileField(
        'Upload Foto/Logo UMKM',
        validators=[
            FileAllowed(['jpg', 'jpeg', 'png'], 'Hanya file JPG/PNG yang diizinkan.'),
        ]
    )
    foto_url_input = StringField(
        'Atau Masukkan Link / URL Foto',
        validators=[Optional(), Length(max=500)]
    )
    submit = SubmitField('Simpan Profil')

    def validate_foto(self, field):
        """Validasi ukuran file maksimal 2MB."""
        if field.data:
            field.data.seek(0, 2)
            size = field.data.tell()
            field.data.seek(0)
            if size > 2 * 1024 * 1024:
                raise ValidationError('Ukuran file maksimal 2MB.')


class CheckoutForm(FlaskForm):
    """Form checkout pesanan pelanggan."""
    nama_pemesan = StringField(
        'Nama Pemesan',
        validators=[
            DataRequired(message='Nama pemesan wajib diisi.'),
            Length(max=100, message='Maksimal 100 karakter.')
        ]
    )
    tipe_pesanan = SelectField(
        'Tipe Pesanan',
        choices=OrderType.CHOICES,
        default=OrderType.DINE_IN
    )
    nomor_meja = StringField(
        'Nomor Meja (jika makan di tempat)',
        validators=[Optional(), Length(max=50)]
    )
    catatan = TextAreaField(
        'Catatan Pesanan (opsional)',
        validators=[Optional(), Length(max=500)]
    )
    submit = SubmitField('Kirim Pesanan via WhatsApp')
