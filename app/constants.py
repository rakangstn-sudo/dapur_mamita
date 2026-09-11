"""
Konstanta terpusat untuk aplikasi Dapur Mamita.
Menghindari penggunaan 'magic string' di berbagai modul.
"""

from typing import Dict, List, Tuple


class OrderStatus:
    """Status pesanan customer."""
    MENUNGGU = 'menunggu'
    DIPROSES = 'diproses'
    SELESAI = 'selesai'
    DIBATALKAN = 'dibatalkan'

    ALL: List[str] = [MENUNGGU, DIPROSES, SELESAI, DIBATALKAN]
    ACTIVE: List[str] = [MENUNGGU, DIPROSES]

    LABELS: Dict[str, str] = {
        MENUNGGU: 'Menunggu',
        DIPROSES: 'Sedang Diproses',
        SELESAI: 'Selesai',
        DIBATALKAN: 'Dibatalkan',
    }

    COLORS: Dict[str, str] = {
        MENUNGGU: 'warning',
        DIPROSES: 'info',
        SELESAI: 'success',
        DIBATALKAN: 'danger',
    }

    @classmethod
    def get_label(cls, status: str) -> str:
        return cls.LABELS.get(status, status)

    @classmethod
    def get_color(cls, status: str) -> str:
        return cls.COLORS.get(status, 'secondary')


class OrderType:
    """Tipe pesanan."""
    DINE_IN = 'Dine-in'
    TAKEAWAY = 'Takeaway'

    CHOICES: List[Tuple[str, str]] = [
        (DINE_IN, 'Makan di Tempat (Dine-in)'),
        (TAKEAWAY, 'Bungkus (Take Away)'),
    ]


class MenuCategory:
    """Kategori menu makanan/minuman."""
    MAKANAN = 'Makanan'
    MINUMAN = 'Minuman'
    SNACK = 'Snack'
    DESSERT = 'Dessert'
    PAKET = 'Paket'

    CHOICES: List[Tuple[str, str]] = [
        (MAKANAN, 'Makanan'),
        (MINUMAN, 'Minuman'),
        (SNACK, 'Snack'),
        (DESSERT, 'Dessert'),
        (PAKET, 'Paket'),
    ]


class AppDefaults:
    """Nilai default aplikasi jika konfigurasi/database belum terisi."""
    DEFAULT_STORE_NAME = 'Dapur Mamita'
    DEFAULT_WHATSAPP = '6282118403965'
    MAX_UPLOAD_SIZE_BYTES = 2 * 1024 * 1024  # 2MB
    ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png'}
