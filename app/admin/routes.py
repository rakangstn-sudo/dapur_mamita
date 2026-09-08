"""
Routes admin: dashboard, CRUD menu, CRUD meja + QR, pesanan masuk, profil UMKM.
Semua route memerlukan login.
"""

import os
import uuid
import qrcode
from io import BytesIO
from flask import (
    render_template, redirect, url_for, flash, request,
    current_app, send_file
)
from flask_login import login_required
from . import admin_bp
from ..models import MenuItem, Meja, Pesanan, ProfilUMKM, DetailPesanan
from ..forms import MenuForm, MejaForm, ProfilForm
from ..extensions import db
from datetime import datetime, timezone, timedelta


def upload_to_supabase(file_data, filename):
    """
    Upload file ke Supabase Storage.
    Returns URL publik file, atau string kosong jika gagal.
    """
    try:
        from supabase import create_client
        supabase_url = current_app.config['SUPABASE_URL']
        supabase_key = current_app.config['SUPABASE_KEY']
        bucket = current_app.config['SUPABASE_BUCKET']

        if not supabase_url or not supabase_key:
            current_app.logger.warning('Supabase belum dikonfigurasi, skip upload.')
            return ''

        client = create_client(supabase_url, supabase_key)

        # Upload file
        file_bytes = file_data.read()
        file_path = f"uploads/{filename}"

        client.storage.from_(bucket).upload(
            path=file_path,
            file=file_bytes,
            file_options={"content-type": file_data.content_type or "image/jpeg"}
        )

        # Dapatkan URL publik
        public_url = client.storage.from_(bucket).get_public_url(file_path)
        return public_url

    except Exception as e:
        current_app.logger.error(f'Gagal upload ke Supabase: {e}')
        return ''


# ─── DASHBOARD ───────────────────────────────────────────────────────────────

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard admin — ringkasan hari ini."""
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    pesanan_hari_ini = Pesanan.query.filter(
        Pesanan.created_at >= today_start
    ).count()

    pesanan_menunggu = Pesanan.query.filter_by(status='menunggu').count()
    pesanan_diproses = Pesanan.query.filter_by(status='diproses').count()

    total_menu = MenuItem.query.count()
    menu_aktif = MenuItem.query.filter_by(tersedia=True).count()
    total_meja = Meja.query.count()

    # Pendapatan hari ini (dari pesanan selesai)
    pendapatan = db.session.query(
        db.func.coalesce(db.func.sum(Pesanan.total_harga), 0)
    ).filter(
        Pesanan.status == 'selesai',
        Pesanan.created_at >= today_start
    ).scalar()

    return render_template(
        'admin/dashboard.html',
        pesanan_hari_ini=pesanan_hari_ini,
        pesanan_menunggu=pesanan_menunggu,
        pesanan_diproses=pesanan_diproses,
        total_menu=total_menu,
        menu_aktif=menu_aktif,
        total_meja=total_meja,
        pendapatan=pendapatan
    )


# ─── CRUD MENU ──────────────────────────────────────────────────────────────

@admin_bp.route('/menu')
@login_required
def menu_list():
    """Daftar semua menu."""
    menu_items = MenuItem.query.order_by(MenuItem.kategori, MenuItem.nama).all()
    return render_template('admin/menu_form.html', menu_items=menu_items, form=MenuForm(), editing=False)


@admin_bp.route('/menu/tambah', methods=['GET', 'POST'])
@login_required
def menu_tambah():
    """Tambah menu baru."""
    form = MenuForm()

    if form.validate_on_submit():
        foto_url = ''
        if form.foto.data:
            ext = form.foto.data.filename.rsplit('.', 1)[-1].lower()
            filename = f"menu_{uuid.uuid4().hex[:8]}.{ext}"
            foto_url = upload_to_supabase(form.foto.data, filename)

        menu = MenuItem(
            nama=form.nama.data,
            deskripsi=form.deskripsi.data or '',
            harga=form.harga.data,
            kategori=form.kategori.data,
            tersedia=form.tersedia.data,
            foto_url=foto_url
        )
        db.session.add(menu)
        db.session.commit()

        flash(f'Menu "{menu.nama}" berhasil ditambahkan!', 'success')
        return redirect(url_for('admin.menu_list'))

    menu_items = MenuItem.query.order_by(MenuItem.kategori, MenuItem.nama).all()
    return render_template('admin/menu_form.html', form=form, menu_items=menu_items, editing=False)


@admin_bp.route('/menu/edit/<int:menu_id>', methods=['GET', 'POST'])
@login_required
def menu_edit(menu_id):
    """Edit menu yang ada."""
    menu = MenuItem.query.get_or_404(menu_id)
    form = MenuForm(obj=menu)

    if form.validate_on_submit():
        menu.nama = form.nama.data
        menu.deskripsi = form.deskripsi.data or ''
        menu.harga = form.harga.data
        menu.kategori = form.kategori.data
        menu.tersedia = form.tersedia.data

        if form.foto.data:
            ext = form.foto.data.filename.rsplit('.', 1)[-1].lower()
            filename = f"menu_{uuid.uuid4().hex[:8]}.{ext}"
            foto_url = upload_to_supabase(form.foto.data, filename)
            if foto_url:
                menu.foto_url = foto_url

        db.session.commit()
        flash(f'Menu "{menu.nama}" berhasil diupdate!', 'success')
        return redirect(url_for('admin.menu_list'))

    menu_items = MenuItem.query.order_by(MenuItem.kategori, MenuItem.nama).all()
    return render_template(
        'admin/menu_form.html',
        form=form,
        menu_items=menu_items,
        editing=True,
        edit_menu=menu
    )


@admin_bp.route('/menu/hapus/<int:menu_id>', methods=['POST'])
@login_required
def menu_hapus(menu_id):
    """Hapus menu."""
    menu = MenuItem.query.get_or_404(menu_id)
    nama = menu.nama
    db.session.delete(menu)
    db.session.commit()
    flash(f'Menu "{nama}" berhasil dihapus.', 'info')
    return redirect(url_for('admin.menu_list'))


@admin_bp.route('/menu/toggle/<int:menu_id>', methods=['POST'])
@login_required
def menu_toggle(menu_id):
    """Toggle ketersediaan menu."""
    menu = MenuItem.query.get_or_404(menu_id)
    menu.tersedia = not menu.tersedia
    db.session.commit()
    status = 'tersedia' if menu.tersedia else 'tidak tersedia'
    flash(f'Menu "{menu.nama}" sekarang {status}.', 'info')
    return redirect(url_for('admin.menu_list'))


# ─── CRUD MEJA & QR CODE ────────────────────────────────────────────────────

def get_base_url(app):
    """Mendapatkan domain/URL dasar secara dinamis dari request browser atau config BASE_URL."""
    from flask import has_request_context, request
    if has_request_context() and request.host_url:
        # Otomatis mengikuti domain saat dibuka di hosting (misal: https://dapurmamita.my.id)
        # Tangani reverse proxy SSL (X-Forwarded-Proto)
        scheme = request.headers.get('X-Forwarded-Proto', request.scheme)
        return f"{scheme}://{request.host}".rstrip('/')
    return app.config.get('BASE_URL', 'http://localhost:5000').rstrip('/')


def create_qr_buffer(url, fill_color='#3E2723', box_size=10):
    """Generate QR code PNG ke memory buffer (BytesIO) tanpa menulis ke disk."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=box_size,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color=fill_color, back_color='white')
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf


@admin_bp.route('/outlet/qr.png')
def stream_outlet_qr():
    """Stream gambar QR code utama outlet langsung dari memori."""
    base_url = get_base_url(current_app)
    url = f"{base_url}/menu"
    buf = create_qr_buffer(url, fill_color='#3E2723', box_size=12)
    return send_file(buf, mimetype='image/png')


@admin_bp.route('/outlet/download-qr')
@login_required
def download_outlet_qr():
    """Download QR Code Utama Outlet Dapur Mamita langsung dari memori."""
    base_url = get_base_url(current_app)
    url = f"{base_url}/menu"
    buf = create_qr_buffer(url, fill_color='#3E2723', box_size=14)
    return send_file(
        buf,
        mimetype='image/png',
        as_attachment=True,
        download_name='QR_Menu_Dapur_Mamita.png'
    )


@admin_bp.route('/meja/qr/<kode_unik>.png')
def stream_meja_qr(kode_unik):
    """Stream gambar QR code meja secara dinamis dari memori."""
    base_url = get_base_url(current_app)
    url = f"{base_url}/menu?meja={kode_unik}"
    buf = create_qr_buffer(url, fill_color='#5D4037', box_size=10)
    return send_file(buf, mimetype='image/png')


@admin_bp.route('/meja')
@login_required
def meja_list():
    """Daftar QR code (QR Utama Outlet + Meja opsional)."""
    meja_list = Meja.query.order_by(Meja.nomor_meja).all()
    form = MejaForm()
    return render_template(
        'admin/meja_list.html',
        meja_list=meja_list,
        form=form
    )


@admin_bp.route('/meja/tambah', methods=['POST'])
@login_required
def meja_tambah():
    """Tambah meja baru."""
    form = MejaForm()

    if form.validate_on_submit():
        # Cek duplikat nomor meja
        existing = Meja.query.filter_by(nomor_meja=form.nomor_meja.data).first()
        if existing:
            flash(f'Meja nomor {form.nomor_meja.data} sudah ada.', 'danger')
            return redirect(url_for('admin.meja_list'))

        kode_unik = uuid.uuid4().hex[:8].upper()

        meja = Meja(
            nomor_meja=form.nomor_meja.data,
            kode_unik=kode_unik,
            qr_image_url=f"meja_{kode_unik}.png"
        )

        db.session.add(meja)
        db.session.commit()

        flash(f'Meja {meja.nomor_meja} berhasil ditambahkan!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{error}', 'danger')

    return redirect(url_for('admin.meja_list'))


@admin_bp.route('/meja/hapus/<int:meja_id>', methods=['POST'])
@login_required
def meja_hapus(meja_id):
    """Hapus meja."""
    meja = Meja.query.get_or_404(meja_id)
    nomor = meja.nomor_meja

    db.session.delete(meja)
    db.session.commit()
    flash(f'Meja {nomor} berhasil dihapus.', 'info')
    return redirect(url_for('admin.meja_list'))


@admin_bp.route('/meja/download-qr/<int:meja_id>')
@login_required
def download_qr(meja_id):
    """Download QR code meja sebagai PNG dari memori."""
    meja = Meja.query.get_or_404(meja_id)
    base_url = get_base_url(current_app)
    url = f"{base_url}/menu?meja={meja.kode_unik}"
    buf = create_qr_buffer(url, fill_color='#5D4037', box_size=14)

    return send_file(
        buf,
        mimetype='image/png',
        as_attachment=True,
        download_name=f'QR_Meja_{meja.nomor_meja}.png'
    )


@admin_bp.route('/meja/regenerate-qr/<int:meja_id>', methods=['POST'])
@login_required
def regenerate_qr(meja_id):
    """Regenerate QR code untuk meja."""
    meja = Meja.query.get_or_404(meja_id)
    meja.kode_unik = uuid.uuid4().hex[:8].upper()
    meja.qr_image_url = f"meja_{meja.kode_unik}.png"
    db.session.commit()
    flash(f'QR code Meja {meja.nomor_meja} berhasil di-regenerate.', 'success')
    return redirect(url_for('admin.meja_list'))


# ─── PESANAN MASUK ───────────────────────────────────────────────────────────

@admin_bp.route('/pesanan')
@login_required
def pesanan_masuk():
    """Daftar pesanan masuk (belum selesai + selesai hari ini)."""
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    # Pesanan aktif (menunggu + diproses)
    pesanan_aktif = (
        Pesanan.query
        .filter(Pesanan.status.in_(['menunggu', 'diproses']))
        .order_by(Pesanan.created_at.desc())
        .all()
    )

    # Pesanan selesai/dibatalkan hari ini
    pesanan_selesai = (
        Pesanan.query
        .filter(
            Pesanan.status.in_(['selesai', 'dibatalkan']),
            Pesanan.created_at >= today_start
        )
        .order_by(Pesanan.created_at.desc())
        .all()
    )

    return render_template(
        'admin/pesanan_masuk.html',
        pesanan_aktif=pesanan_aktif,
        pesanan_selesai=pesanan_selesai
    )


@admin_bp.route('/pesanan/status/<int:pesanan_id>', methods=['POST'])
@login_required
def ubah_status_pesanan(pesanan_id):
    """Ubah status pesanan."""
    pesanan = Pesanan.query.get_or_404(pesanan_id)
    new_status = request.form.get('status')

    valid_statuses = ['menunggu', 'diproses', 'selesai', 'dibatalkan']
    if new_status not in valid_statuses:
        flash('Status tidak valid.', 'danger')
        return redirect(url_for('admin.pesanan_masuk'))

    pesanan.status = new_status
    db.session.commit()

    flash(f'Pesanan #{pesanan.id} diubah ke "{pesanan.status_label}".', 'success')
    return redirect(url_for('admin.pesanan_masuk'))


# ─── PROFIL UMKM ────────────────────────────────────────────────────────────

@admin_bp.route('/profil', methods=['GET', 'POST'])
@login_required
def profil():
    """Edit profil UMKM (single-row)."""
    profil = ProfilUMKM.query.first()
    if not profil:
        profil = ProfilUMKM(nama_umkm='Dapur Mamita')
        db.session.add(profil)
        db.session.commit()

    form = ProfilForm(obj=profil)

    if form.validate_on_submit():
        profil.nama_umkm = form.nama_umkm.data
        profil.deskripsi = form.deskripsi.data or ''
        profil.alamat = form.alamat.data or ''
        profil.no_wa = form.no_wa.data or ''
        profil.jam_operasional = form.jam_operasional.data or ''

        if form.foto.data:
            ext = form.foto.data.filename.rsplit('.', 1)[-1].lower()
            filename = f"profil_{uuid.uuid4().hex[:8]}.{ext}"
            foto_url = upload_to_supabase(form.foto.data, filename)
            if foto_url:
                profil.foto_url = foto_url

        db.session.commit()
        flash('Profil UMKM berhasil diupdate!', 'success')
        return redirect(url_for('admin.profil'))

    return render_template('admin/profil_form.html', form=form, profil=profil)
