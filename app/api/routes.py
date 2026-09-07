"""
API endpoints JSON untuk polling status pesanan.
"""

from flask import jsonify, session
from flask_login import login_required
from . import api_bp
from ..models import Pesanan
from ..extensions import csrf


@api_bp.route('/pesanan/<int:pesanan_id>/status')
def status_pesanan(pesanan_id):
    """
    Cek status pesanan — untuk polling dari halaman customer.
    Keamanan: hanya pemilik pesanan (berdasarkan session) yang bisa mengakses.
    """
    pesanan = Pesanan.query.get(pesanan_id)

    if not pesanan:
        return jsonify({'error': 'Pesanan tidak ditemukan'}), 404

    # Validasi: hanya pemilik session yang bisa akses
    if (session.get('pesanan_id') != pesanan.id and
            session.get('meja_id') != pesanan.meja_id):
        return jsonify({'error': 'Akses ditolak'}), 403

    return jsonify({
        'id': pesanan.id,
        'status': pesanan.status,
        'status_label': pesanan.status_label,
        'status_color': pesanan.status_color,
        'total_harga': pesanan.total_harga,
        'created_at': pesanan.created_at.strftime('%H:%M') if pesanan.created_at else '',
        'items': [
            {
                'nama': d.menu_item.nama if d.menu_item else 'Menu dihapus',
                'jumlah': d.jumlah,
                'subtotal': d.subtotal,
                'catatan_item': d.catatan_item
            }
            for d in pesanan.detail_items
        ]
    })


@api_bp.route('/admin/pesanan')
@login_required
def admin_pesanan_list():
    """
    List pesanan untuk polling dari dashboard admin.
    Returns semua pesanan aktif (menunggu + diproses).
    """
    pesanan_aktif = (
        Pesanan.query
        .filter(Pesanan.status.in_(['menunggu', 'diproses']))
        .order_by(Pesanan.created_at.desc())
        .all()
    )

    result = []
    for p in pesanan_aktif:
        result.append({
            'id': p.id,
            'nomor_meja': p.meja.nomor_meja if p.meja else '-',
            'status': p.status,
            'status_label': p.status_label,
            'status_color': p.status_color,
            'total_harga': p.total_harga,
            'catatan': p.catatan,
            'created_at': p.created_at.strftime('%H:%M') if p.created_at else '',
            'items': [
                {
                    'nama': d.menu_item.nama if d.menu_item else 'Menu dihapus',
                    'jumlah': d.jumlah,
                    'subtotal': d.subtotal,
                    'catatan_item': d.catatan_item
                }
                for d in p.detail_items
            ]
        })

    return jsonify({'pesanan': result, 'total': len(result)})
