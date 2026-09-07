"""
Routes halaman publik: landing page, menu digital, tentang.
"""

from flask import render_template, request, session, abort
from . import main_bp
from ..models import MenuItem, Meja, ProfilUMKM


@main_bp.route('/')
def index():
    """Landing page / halaman utama."""
    profil = ProfilUMKM.query.first()
    menu_highlights = MenuItem.query.filter_by(tersedia=True).limit(6).all()
    return render_template('main/index.html', profil=profil, menu_highlights=menu_highlights)


@main_bp.route('/menu')
def menu_list():
    """
    Halaman menu digital — dibuka setelah scan QR code.
    URL: /menu?meja=KODE_UNIK
    """
    kode_meja = request.args.get('meja', '')

    if kode_meja:
        meja = Meja.query.filter_by(kode_unik=kode_meja).first()
        if meja:
            session['meja_id'] = meja.id
            session['nomor_meja'] = meja.nomor_meja
            session['kode_meja'] = meja.kode_unik
        else:
            abort(404)
    elif 'meja_id' not in session:
        # Tidak ada kode meja di URL dan tidak ada di session
        # Tampilkan menu tanpa konteks meja (read-only)
        pass

    # Filter kategori
    kategori = request.args.get('kategori', '')
    query = MenuItem.query.filter_by(tersedia=True)
    if kategori:
        query = query.filter_by(kategori=kategori)

    menu_items = query.order_by(MenuItem.kategori, MenuItem.nama).all()

    # Ambil semua kategori unik untuk filter
    kategori_list = (
        MenuItem.query
        .filter_by(tersedia=True)
        .with_entities(MenuItem.kategori)
        .distinct()
        .order_by(MenuItem.kategori)
        .all()
    )
    kategori_list = [k[0] for k in kategori_list]

    # Hitung jumlah item di keranjang
    keranjang = session.get('keranjang', [])
    jumlah_keranjang = sum(item.get('jumlah', 0) for item in keranjang)

    return render_template(
        'main/menu_list.html',
        menu_items=menu_items,
        kategori_list=kategori_list,
        kategori_aktif=kategori,
        nomor_meja=session.get('nomor_meja'),
        jumlah_keranjang=jumlah_keranjang
    )


@main_bp.route('/tentang')
def tentang():
    """Halaman tentang UMKM."""
    profil = ProfilUMKM.query.first()
    return render_template('main/tentang.html', profil=profil)
