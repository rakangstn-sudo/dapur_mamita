"""
Routes alur pemesanan customer:
- Tambah ke keranjang
- Lihat & kelola keranjang belanja
- Checkout pesanan → simpan ke database & buat link WhatsApp
- Halaman status pelacakan pesanan
"""

from typing import Union
from flask import (
    render_template, request, session, redirect, url_for, flash, Response
)
from . import order_bp
from ..models import MenuItem, Pesanan, DetailPesanan, ProfilUMKM
from ..forms import CheckoutForm
from ..extensions import db
from ..constants import OrderStatus, OrderType
from ..services import CartService, WhatsAppService


@order_bp.route('/tambah', methods=['POST'])
def tambah_keranjang() -> Response:
    """Tambah item ke keranjang belanja pelanggan (tersimpan aman di session)."""
    menu_id = request.form.get('menu_id', type=int)
    jumlah = request.form.get('jumlah', 1, type=int)

    if not menu_id or jumlah < 1:
        flash('Data menu atau jumlah tidak valid.', 'danger')
        return redirect(url_for('main.menu_list'))

    menu_item = MenuItem.query.get_or_404(menu_id)

    if not menu_item.tersedia:
        flash('Maaf, menu ini sedang tidak tersedia.', 'warning')
        return redirect(url_for('main.menu_list'))

    CartService.add_item(menu_item, jumlah)
    flash(f'"{menu_item.nama}" berhasil ditambahkan ke keranjang!', 'success')
    return redirect(url_for('main.menu_list'))


@order_bp.route('/keranjang')
def keranjang() -> str:
    """Halaman rincian keranjang belanja dan form checkout."""
    cart_items = CartService.get_cart()
    total_harga = CartService.get_total_price()
    form = CheckoutForm()

    return render_template(
        'order/keranjang.html',
        keranjang=cart_items,
        total=total_harga,
        form=form,
        nomor_meja=session.get('nomor_meja')
    )


@order_bp.route('/update', methods=['POST'])
def update_keranjang() -> Response:
    """Update jumlah item, catatan rasa/pedas, atau hapus item dari keranjang."""
    action = request.form.get('action')
    index = request.form.get('index', type=int)
    catatan_item = request.form.get('catatan_item', '')

    if index is not None and action:
        CartService.update_item(index=index, action=action, catatan=catatan_item)

    return redirect(url_for('order.keranjang'))


@order_bp.route('/checkout', methods=['POST'])
def checkout() -> Response:
    """Proses checkout pesanan pelanggan: simpan ke database dan buat link WhatsApp."""
    form = CheckoutForm()

    if not form.validate_on_submit():
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{error}', 'danger')
        return redirect(url_for('order.keranjang'))

    cart_items = CartService.get_cart()
    if not cart_items:
        flash('Keranjang belanja Anda masih kosong.', 'warning')
        return redirect(url_for('main.menu_list'))

    nama_pemesan = form.nama_pemesan.data.strip()
    tipe_pesanan = form.tipe_pesanan.data
    nomor_meja_input = form.nomor_meja.data.strip() if form.nomor_meja.data else ''

    # Tentukan deskripsi meja / bungkus
    if tipe_pesanan == OrderType.TAKEAWAY:
        meja_info = "Bungkus (Take Away)"
    elif nomor_meja_input:
        meja_info = f"Meja {nomor_meja_input}"
    elif session.get('nomor_meja'):
        meja_info = f"Meja {session.get('nomor_meja')}"
    else:
        meja_info = "Makan di Tempat"

    meja_id = session.get('meja_id')
    total_harga = CartService.get_total_price()

    # 1. Simpan pesanan utama
    pesanan = Pesanan(
        meja_id=meja_id,
        nama_pemesan=nama_pemesan,
        tipe_pesanan=tipe_pesanan,
        meja_info=meja_info,
        status=OrderStatus.MENUNGGU,
        total_harga=total_harga,
        catatan=form.catatan.data or ''
    )
    db.session.add(pesanan)
    db.session.flush()  # Ambil ID pesanan otomatis

    # 2. Simpan setiap rincian item pesanan
    for item in cart_items:
        menu_item = MenuItem.query.get(item['menu_id'])
        if menu_item:
            detail = DetailPesanan(
                pesanan_id=pesanan.id,
                menu_item_id=menu_item.id,
                jumlah=item['jumlah'],
                subtotal=item['subtotal'],
                catatan_item=item.get('catatan_item', '')
            )
            db.session.add(detail)

    # 3. Buat URL WhatsApp kasir/dapur secara otomatis
    profil = ProfilUMKM.query.first()
    target_wa = profil.no_wa if profil and profil.no_wa else None

    pesanan.wa_url = WhatsAppService.create_order_wa_url(
        phone_target=target_wa,
        order_id=pesanan.id,
        customer_name=nama_pemesan,
        table_info=meja_info,
        cart_items=cart_items,
        total_price=total_harga,
        order_notes=form.catatan.data
    )

    db.session.commit()

    # 4. Bersihkan keranjang belanja dan simpan session pesanan
    CartService.clear_cart()
    session['pesanan_id'] = pesanan.id
    session['nama_pemesan'] = nama_pemesan
    session.modified = True

    flash('Pesanan berhasil disimpan! Silakan klik tombol WhatsApp untuk mengirimkan rincian pesanan ke kasir/dapur 😊', 'success')
    return redirect(url_for('order.status_pesanan', pesanan_id=pesanan.id))


@order_bp.route('/status/<int:pesanan_id>')
def status_pesanan(pesanan_id: int) -> str:
    """Halaman pelacakan status pesanan secara real-time via polling."""
    pesanan = Pesanan.query.get_or_404(pesanan_id)

    return render_template(
        'order/status_pesanan.html',
        pesanan=pesanan,
        nomor_meja=session.get('nomor_meja') or pesanan.meja_info
    )
