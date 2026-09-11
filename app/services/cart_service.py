"""
Cart Service — Pengelolaan keranjang belanja pelanggan berbasis Flask Session.
"""

from typing import List, Dict, Any, Optional
from flask import session
from ..models import MenuItem


class CartService:
    """Service untuk mengelola item keranjang belanja dalam session."""

    SESSION_KEY = 'keranjang'

    @classmethod
    def get_cart(cls) -> List[Dict[str, Any]]:
        """Mendapatkan daftar item di keranjang belanja saat ini."""
        return session.get(cls.SESSION_KEY, [])

    @classmethod
    def get_total_price(cls) -> int:
        """Menghitung total harga seluruh item di keranjang."""
        cart = cls.get_cart()
        return sum(item.get('subtotal', 0) for item in cart)

    @classmethod
    def get_total_count(cls) -> int:
        """Menghitung total kuantitas porsi/item dalam keranjang."""
        cart = cls.get_cart()
        return sum(item.get('jumlah', 0) for item in cart)

    @classmethod
    def is_empty(cls) -> bool:
        """Mengecek apakah keranjang kosong."""
        return len(cls.get_cart()) == 0

    @classmethod
    def add_item(cls, menu_item: MenuItem, jumlah: int = 1) -> bool:
        """
        Menambahkan menu ke keranjang belanja.
        Jika menu sudah ada, tambahkan jumlahnya dan perbarui subtotal.
        """
        if not menu_item or not menu_item.tersedia or jumlah < 1:
            return False

        if cls.SESSION_KEY not in session:
            session[cls.SESSION_KEY] = []

        cart = session[cls.SESSION_KEY]

        # Cek apakah item sudah ada di keranjang
        item_found = False
        for item in cart:
            if item.get('menu_id') == menu_item.id:
                item['jumlah'] += jumlah
                item['subtotal'] = item['jumlah'] * item['harga']
                item_found = True
                break

        if not item_found:
            cart.append({
                'menu_id': menu_item.id,
                'nama': menu_item.nama,
                'harga': menu_item.harga,
                'jumlah': jumlah,
                'subtotal': menu_item.harga * jumlah,
                'catatan_item': '',
                'foto_url': menu_item.foto_url or ''
            })

        session[cls.SESSION_KEY] = cart
        session.modified = True
        return True

    @classmethod
    def update_item(
        cls,
        index: int,
        action: str,
        catatan: Optional[str] = None
    ) -> bool:
        """
        Memperbarui item di keranjang:
        action: 'tambah' | 'kurang' | 'hapus' | 'catatan'
        """
        cart = cls.get_cart()
        if not (0 <= index < len(cart)):
            return False

        if action == 'tambah':
            cart[index]['jumlah'] += 1
            cart[index]['subtotal'] = cart[index]['jumlah'] * cart[index]['harga']
        elif action == 'kurang':
            cart[index]['jumlah'] -= 1
            if cart[index]['jumlah'] <= 0:
                cart.pop(index)
            else:
                cart[index]['subtotal'] = cart[index]['jumlah'] * cart[index]['harga']
        elif action == 'hapus':
            cart.pop(index)
        elif action == 'catatan':
            cart[index]['catatan_item'] = (catatan or '')[:300]
        else:
            return False

        session[cls.SESSION_KEY] = cart
        session.modified = True
        return True

    @classmethod
    def clear_cart(cls) -> None:
        """Mengosongkan keranjang belanja."""
        session.pop(cls.SESSION_KEY, None)
        session.modified = True
