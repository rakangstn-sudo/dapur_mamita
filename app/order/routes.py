"""
Routes alur pemesanan customer:
- Tambah ke keranjang (session Flask)
- Lihat & edit keranjang
- Checkout → simpan Pesanan ke DB
- Lihat status pesanan
"""

import urllib.parse
from flask import (
    render_template, request, session, redirect, url_for, flash, jsonify, abort
)
from . import order_bp
from ..models import MenuItem, Meja, Pesanan, DetailPesanan, ProfilUMKM
from ..forms import CheckoutForm
from ..extensions import db


@order_bp.route('/tambah', methods=['POST'])
def tambah_keranjang():
    """Tambah item ke keranjang (disimpan di session Flask)."""
    menu_id = request.form.get('menu_id', type=int)
    jumlah = request.form.get('jumlah', 1, type=int)

    if not menu_id or jumlah < 1:
        flash('Data tidak valid.', 'danger')
        return redirect(url_for('main.menu_list'))

    menu_item = MenuItem.query.get_or_404(menu_id)

    if not menu_item.tersedia:
        flash('Menu ini sedang tidak tersedia.', 'warning')
        return redirect(url_for('main.menu_list'))

    # Inisialisasi keranjang di session kalau belum ada
    if 'keranjang' not in session:
        session['keranjang'] = []

    keranjang = session['keranjang']

    # Cek apakah item sudah ada di keranjang
    item_exists = False
    for item in keranjang:
        if item['menu_id'] == menu_id:
            item['jumlah'] += jumlah
            item['subtotal'] = item['jumlah'] * item['harga']
            item_exists = True
            break

    if not item_exists:
        keranjang.append({
            'menu_id': menu_item.id,
            'nama': menu_item.nama,
            'harga': menu_item.harga,
            'jumlah': jumlah,
            'subtotal': menu_item.harga * jumlah,
            'catatan_item': '',
            'foto_url': menu_item.foto_url or ''
        })

    session['keranjang'] = keranjang
    session.modified = True

    flash(f'{menu_item.nama} ditambahkan ke keranjang!', 'success')
    return redirect(url_for('main.menu_list'))


@order_bp.route('/keranjang')
def keranjang():
    """Lihat isi keranjang."""
    keranjang = session.get('keranjang', [])
    total = sum(item.get('subtotal', 0) for item in keranjang)
    form = CheckoutForm()
    return render_template(
        'order/keranjang.html',
        keranjang=keranjang,
        total=total,
        form=form,
        nomor_meja=session.get('nomor_meja')
    )


@order_bp.route('/update', methods=['POST'])
def update_keranjang():
    """Update jumlah atau hapus item dari keranjang."""
    action = request.form.get('action')
    index = request.form.get('index', type=int)

    keranjang = session.get('keranjang', [])

    if index is not None and 0 <= index < len(keranjang):
        if action == 'tambah':
            keranjang[index]['jumlah'] += 1
            keranjang[index]['subtotal'] = (
                keranjang[index]['jumlah'] * keranjang[index]['harga']
            )
        elif action == 'kurang':
            keranjang[index]['jumlah'] -= 1
            if keranjang[index]['jumlah'] <= 0:
                keranjang.pop(index)
            else:
                keranjang[index]['subtotal'] = (
                    keranjang[index]['jumlah'] * keranjang[index]['harga']
                )
        elif action == 'hapus':
            keranjang.pop(index)
        elif action == 'catatan':
            catatan = request.form.get('catatan_item', '')
            keranjang[index]['catatan_item'] = catatan[:300]

    session['keranjang'] = keranjang
    session.modified = True

    return redirect(url_for('order.keranjang'))


@order_bp.route('/checkout', methods=['POST'])
def checkout():
    """Proses checkout — simpan pesanan ke database."""
    form = CheckoutForm()

    if not form.validate_on_submit():
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{error}', 'danger')
        return redirect(url_for('order.keranjang'))

    keranjang = session.get('keranjang', [])
    if not keranjang:
        flash('Keranjang masih kosong.', 'warning')
        return redirect(url_for('main.menu_list'))

    nama_pemesan = form.nama_pemesan.data.strip()
    tipe_pesanan = form.tipe_pesanan.data
    nomor_meja_input = form.nomor_meja.data.strip() if form.nomor_meja.data else ''
    
    # Tentukan keterangan meja / takeaway
    if tipe_pesanan == 'Takeaway':
        meja_info = "Bungkus (Take Away)"
    elif nomor_meja_input:
        meja_info = f"Meja {nomor_meja_input}"
    elif session.get('nomor_meja'):
        meja_info = f"Meja {session.get('nomor_meja')}"
    else:
        meja_info = "Makan di Tempat"

    meja_id = session.get('meja_id')

    # Hitung total dan buat pesanan
    total_harga = sum(item.get('subtotal', 0) for item in keranjang)

    pesanan = Pesanan(
        meja_id=meja_id,
        nama_pemesan=nama_pemesan,
        tipe_pesanan=tipe_pesanan,
        meja_info=meja_info,
        status='menunggu',
        total_harga=total_harga,
        catatan=form.catatan.data or ''
    )
    db.session.add(pesanan)
    db.session.flush()  # Dapatkan ID pesanan

    # Buat detail pesanan
    for item in keranjang:
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

    # Buat format WhatsApp otomatis
    profil = ProfilUMKM.query.first()
    no_wa = profil.no_wa if profil and profil.no_wa else '6282118403965'
    no_wa_clean = ''.join(c for c in no_wa if c.isdigit())
    if no_wa_clean.startswith('0'):
        no_wa_clean = '62' + no_wa_clean[1:]
    elif no_wa_clean.startswith('8'):
        no_wa_clean = '62' + no_wa_clean

    msg_lines = [
        "🍲 *PESANAN BARU - DAPUR MAMITA*",
        "------------------------------------",
        f"📋 *No. Pesanan:* #{pesanan.id}",
        f"👤 *Nama:* {nama_pemesan}",
        f"📍 *Tipe / Lokasi:* {meja_info}",
        "",
        "📝 *Rincian Menu:*"
    ]
    for item in keranjang:
        line = f"• {item['jumlah']}x {item['nama']} = Rp {item['subtotal']:,}".replace(",", ".")
        if item.get('catatan_item'):
            line += f"\n   _(Catatan: {item['catatan_item']})_"
        msg_lines.append(line)

    msg_lines.append("------------------------------------")
    msg_lines.append(f"💰 *TOTAL PEMBAYARAN:* Rp {total_harga:,}".replace(",", "."))
    if form.catatan.data:
        msg_lines.append(f"💬 *Catatan Tambahan:* {form.catatan.data}")
    msg_lines.append("------------------------------------")
    msg_lines.append("Halo Dapur Mamita, saya baru saja memesan lewat web menu. Mohon diproses ya! Terima kasih 🙏")

    wa_text = "\n".join(msg_lines)
    pesanan.wa_url = f"https://wa.me/{no_wa_clean}?text={urllib.parse.quote(wa_text)}"

    db.session.commit()

    # Kosongkan keranjang
    session.pop('keranjang', None)
    session['pesanan_id'] = pesanan.id
    session['nama_pemesan'] = nama_pemesan
    session.modified = True

    flash('Pesanan berhasil disimpan! Silakan klik tombol WhatsApp untuk mengirimkan rincian pesanan ke kasir/dapur 😊', 'success')
    return redirect(url_for('order.status_pesanan', pesanan_id=pesanan.id))


@order_bp.route('/status/<int:pesanan_id>')
def status_pesanan(pesanan_id):
    """Halaman status pesanan — auto-refresh via polling."""
    pesanan = Pesanan.query.get_or_404(pesanan_id)

    # Izinkan pemilik session atau admin untuk melihat
    return render_template(
        'order/status_pesanan.html',
        pesanan=pesanan,
        nomor_meja=session.get('nomor_meja') or pesanan.meja_info
    )
