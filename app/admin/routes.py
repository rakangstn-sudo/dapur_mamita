"""
Routes admin: dashboard, CRUD menu, CRUD meja + QR Code, pesanan masuk, dan profil UMKM.
Semua route memerlukan login admin via Flask-Login.
"""

import uuid
from datetime import datetime, timezone
from typing import Union
from flask import (
    render_template, redirect, url_for, flash, request, send_file, Response
)
from flask_login import login_required
from . import admin_bp
from ..models import MenuItem, Meja, Pesanan, ProfilUMKM
from ..forms import MenuForm, MejaForm, ProfilForm
from ..extensions import db
from ..constants import OrderStatus
from ..services import StorageService, QRService


# ─── DASHBOARD ───────────────────────────────────────────────────────────────

@admin_bp.route('/dashboard')
@login_required
def dashboard() -> str:
    """Dashboard admin — ringkasan penjualan dan operasional hari ini."""
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    pesanan_hari_ini = Pesanan.query.filter(
        Pesanan.created_at >= today_start
    ).count()

    pesanan_menunggu = Pesanan.query.filter_by(status=OrderStatus.MENUNGGU).count()
    pesanan_diproses = Pesanan.query.filter_by(status=OrderStatus.DIPROSES).count()

    total_menu = MenuItem.query.count()
    menu_aktif = MenuItem.query.filter_by(tersedia=True).count()
    total_meja = Meja.query.count()

    # Pendapatan hari ini (hanya dari pesanan berstatus selesai)
    pendapatan = db.session.query(
        db.func.coalesce(db.func.sum(Pesanan.total_harga), 0)
    ).filter(
        Pesanan.status == OrderStatus.SELESAI,
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
def menu_list() -> str:
    """Daftar seluruh menu makanan dan minuman."""
    menu_items = MenuItem.query.order_by(MenuItem.kategori, MenuItem.nama).all()
    return render_template('admin/menu_form.html', menu_items=menu_items, form=MenuForm(), editing=False)


@admin_bp.route('/menu/tambah', methods=['GET', 'POST'])
@login_required
def menu_tambah() -> Union[Response, str]:
    """Tambah menu baru ke sistem beserta upload foto."""
    form = MenuForm()

    if form.validate_on_submit():
        foto_url = ''
        upload_err = None
        if form.foto.data:
            filename = StorageService.generate_filename(form.foto.data.filename, prefix='menu')
            foto_url, upload_err = StorageService.upload_file_with_status(form.foto.data, filename)
        elif form.foto_url_input.data and form.foto_url_input.data.strip():
            foto_url = form.foto_url_input.data.strip()

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
        if upload_err:
            flash(f'Peringatan upload foto: {upload_err}', 'warning')

        return redirect(url_for('admin.menu_list'))

    menu_items = MenuItem.query.order_by(MenuItem.kategori, MenuItem.nama).all()
    return render_template('admin/menu_form.html', form=form, menu_items=menu_items, editing=False)


@admin_bp.route('/menu/edit/<int:menu_id>', methods=['GET', 'POST'])
@login_required
def menu_edit(menu_id: int) -> Union[Response, str]:
    """Edit menu yang ada dan opsional ganti foto."""
    menu = MenuItem.query.get_or_404(menu_id)
    form = MenuForm(obj=menu)

    if form.validate_on_submit():
        menu.nama = form.nama.data
        menu.deskripsi = form.deskripsi.data or ''
        menu.harga = form.harga.data
        menu.kategori = form.kategori.data
        menu.tersedia = form.tersedia.data

        upload_err = None
        if form.foto.data:
            filename = StorageService.generate_filename(form.foto.data.filename, prefix='menu')
            uploaded_url, upload_err = StorageService.upload_file_with_status(form.foto.data, filename)
            if uploaded_url:
                menu.foto_url = uploaded_url
        elif form.foto_url_input.data and form.foto_url_input.data.strip():
            menu.foto_url = form.foto_url_input.data.strip()

        db.session.commit()
        flash(f'Menu "{menu.nama}" berhasil diupdate!', 'success')
        if upload_err:
            flash(f'Peringatan upload foto: {upload_err}', 'warning')

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
def menu_hapus(menu_id: int) -> Response:
    """Hapus menu item dari database."""
    menu = MenuItem.query.get_or_404(menu_id)
    nama = menu.nama
    db.session.delete(menu)
    db.session.commit()
    flash(f'Menu "{nama}" berhasil dihapus.', 'info')
    return redirect(url_for('admin.menu_list'))


@admin_bp.route('/menu/toggle/<int:menu_id>', methods=['POST'])
@login_required
def menu_toggle(menu_id: int) -> Response:
    """Toggle status ketersediaan menu (Habis/Tersedia)."""
    menu = MenuItem.query.get_or_404(menu_id)
    menu.tersedia = not menu.tersedia
    db.session.commit()
    status = 'tersedia' if menu.tersedia else 'tidak tersedia'
    flash(f'Menu "{menu.nama}" sekarang {status}.', 'info')
    return redirect(url_for('admin.menu_list'))


# ─── CRUD MEJA & QR CODE ────────────────────────────────────────────────────

@admin_bp.route('/outlet/qr.png')
def stream_outlet_qr() -> Response:
    """Stream gambar QR code utama outlet langsung dari memori."""
    base_url = QRService.get_base_url()
    url = f"{base_url}/menu"
    buf = QRService.create_qr_buffer(url, fill_color='#3E2723', box_size=12)
    return send_file(buf, mimetype='image/png')


@admin_bp.route('/outlet/download-qr')
@login_required
def download_outlet_qr() -> Response:
    """Download QR Code Utama Outlet Dapur Mamita langsung dari memori."""
    base_url = QRService.get_base_url()
    url = f"{base_url}/menu"
    buf = QRService.create_qr_buffer(url, fill_color='#3E2723', box_size=14)
    return send_file(
        buf,
        mimetype='image/png',
        as_attachment=True,
        download_name='QR_Menu_Dapur_Mamita.png'
    )


@admin_bp.route('/meja/qr/<kode_unik>.png')
def stream_meja_qr(kode_unik: str) -> Response:
    """Stream gambar QR code meja secara dinamis dari memori."""
    base_url = QRService.get_base_url()
    url = f"{base_url}/menu?meja={kode_unik}"
    buf = QRService.create_qr_buffer(url, fill_color='#5D4037', box_size=10)
    return send_file(buf, mimetype='image/png')


@admin_bp.route('/meja')
@login_required
def meja_list() -> str:
    """Daftar QR code (QR Utama Outlet + Meja opsional)."""
    meja_items = Meja.query.order_by(Meja.nomor_meja).all()
    form = MejaForm()
    return render_template('admin/meja_list.html', meja_list=meja_items, form=form)


@admin_bp.route('/meja/tambah', methods=['POST'])
@login_required
def meja_tambah() -> Response:
    """Tambah meja baru dan buat kode unik QR."""
    form = MejaForm()

    if form.validate_on_submit():
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
def meja_hapus(meja_id: int) -> Response:
    """Hapus meja dari sistem."""
    meja = Meja.query.get_or_404(meja_id)
    nomor = meja.nomor_meja

    db.session.delete(meja)
    db.session.commit()
    flash(f'Meja {nomor} berhasil dihapus.', 'info')
    return redirect(url_for('admin.meja_list'))


@admin_bp.route('/meja/download-qr/<int:meja_id>')
@login_required
def download_qr(meja_id: int) -> Response:
    """Download QR code meja sebagai PNG resolusi tinggi dari memori."""
    meja = Meja.query.get_or_404(meja_id)
    base_url = QRService.get_base_url()
    url = f"{base_url}/menu?meja={meja.kode_unik}"
    buf = QRService.create_qr_buffer(url, fill_color='#5D4037', box_size=14)

    return send_file(
        buf,
        mimetype='image/png',
        as_attachment=True,
        download_name=f'QR_Meja_{meja.nomor_meja}.png'
    )


@admin_bp.route('/meja/regenerate-qr/<int:meja_id>', methods=['POST'])
@login_required
def regenerate_qr(meja_id: int) -> Response:
    """Regenerate token QR code meja jika kode lama bocor/rusak."""
    meja = Meja.query.get_or_404(meja_id)
    meja.kode_unik = uuid.uuid4().hex[:8].upper()
    meja.qr_image_url = f"meja_{meja.kode_unik}.png"
    db.session.commit()
    flash(f'QR code Meja {meja.nomor_meja} berhasil di-regenerate.', 'success')
    return redirect(url_for('admin.meja_list'))


# ─── PESANAN MASUK ───────────────────────────────────────────────────────────

@admin_bp.route('/pesanan')
@login_required
def pesanan_masuk() -> str:
    """Daftar pesanan masuk (pesanan aktif dan pesanan selesai hari ini)."""
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    # Pesanan aktif (menunggu + diproses)
    pesanan_aktif = (
        Pesanan.query
        .filter(Pesanan.status.in_(OrderStatus.ACTIVE))
        .order_by(Pesanan.created_at.desc())
        .all()
    )

    # Pesanan selesai/dibatalkan hari ini
    pesanan_selesai = (
        Pesanan.query
        .filter(
            Pesanan.status.in_([OrderStatus.SELESAI, OrderStatus.DIBATALKAN]),
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
def ubah_status_pesanan(pesanan_id: int) -> Response:
    """Ubah status pesanan ke tahap selanjutnya."""
    pesanan = Pesanan.query.get_or_404(pesanan_id)
    new_status = request.form.get('status')

    if new_status not in OrderStatus.ALL:
        flash('Status tidak valid.', 'danger')
        return redirect(url_for('admin.pesanan_masuk'))

    pesanan.status = new_status
    db.session.commit()

    flash(f'Pesanan #{pesanan.id} diubah ke "{pesanan.status_label}".', 'success')
    return redirect(url_for('admin.pesanan_masuk'))


# ─── PROFIL UMKM ────────────────────────────────────────────────────────────

@admin_bp.route('/profil', methods=['GET', 'POST'])
@login_required
def profil() -> Union[Response, str]:
    """Kelola profil UMKM (nama usaha, deskripsi, alamat, kontak WhatsApp, foto/logo)."""
    profil_data = ProfilUMKM.query.first()
    if not profil_data:
        profil_data = ProfilUMKM(nama_umkm='Dapur Mamita')
        db.session.add(profil_data)
        db.session.commit()

    form = ProfilForm(obj=profil_data)

    if form.validate_on_submit():
        profil_data.nama_umkm = form.nama_umkm.data
        profil_data.deskripsi = form.deskripsi.data or ''
        profil_data.alamat = form.alamat.data or ''
        profil_data.no_wa = form.no_wa.data or ''
        profil_data.jam_operasional = form.jam_operasional.data or ''

        upload_err = None
        if form.foto.data:
            filename = StorageService.generate_filename(form.foto.data.filename, prefix='profil')
            uploaded_url, upload_err = StorageService.upload_file_with_status(form.foto.data, filename)
            if uploaded_url:
                profil_data.foto_url = uploaded_url
        elif form.foto_url_input.data and form.foto_url_input.data.strip():
            profil_data.foto_url = form.foto_url_input.data.strip()

        db.session.commit()
        flash('Profil UMKM berhasil diupdate!', 'success')
        if upload_err:
            flash(f'Peringatan upload foto: {upload_err}', 'warning')

        return redirect(url_for('admin.profil'))

    return render_template('admin/profil_form.html', form=form, profil=profil_data)
