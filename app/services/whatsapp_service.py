"""
WhatsApp Service — Normalisasi nomor telepon dan pembuatan pesan pesanan otomatis.
"""

import urllib.parse
from typing import List, Dict, Any, Optional
from ..constants import AppDefaults


class WhatsAppService:
    """Service untuk integrasi link dan format pesan WhatsApp."""

    @staticmethod
    def normalize_phone(phone_raw: Optional[str]) -> str:
        """
        Menormalisasi nomor telepon Indonesia ke format internasional (misal 628...).
        Mendukung format '08...', '628...', '+628...', atau '8...'.
        """
        if not phone_raw:
            return AppDefaults.DEFAULT_WHATSAPP

        digits_only = ''.join(c for c in phone_raw if c.isdigit())
        if not digits_only:
            return AppDefaults.DEFAULT_WHATSAPP

        if digits_only.startswith('0'):
            return '62' + digits_only[1:]
        elif digits_only.startswith('8'):
            return '62' + digits_only
        elif digits_only.startswith('62'):
            return digits_only

        return digits_only

    @classmethod
    def generate_order_message(
        cls,
        order_id: int,
        customer_name: str,
        table_info: str,
        cart_items: List[Dict[str, Any]],
        total_price: int,
        order_notes: Optional[str] = None
    ) -> str:
        """Menyusun teks rincian pesanan yang rapi untuk dikirimkan ke WhatsApp kasir/dapur."""
        lines = [
            "🍲 *PESANAN BARU - DAPUR MAMITA*",
            "------------------------------------",
            f"📋 *No. Pesanan:* #{order_id}",
            f"👤 *Nama:* {customer_name}",
            f"📍 *Tipe / Lokasi:* {table_info}",
            "",
            "📝 *Rincian Menu:*"
        ]

        for item in cart_items:
            subtotal_fmt = f"Rp {item.get('subtotal', 0):,}".replace(",", ".")
            line = f"• {item.get('jumlah', 1)}x {item.get('nama', '')} = {subtotal_fmt}"
            if item.get('catatan_item'):
                line += f"\n   _(Catatan: {item['catatan_item']})_"
            lines.append(line)

        lines.append("------------------------------------")
        total_fmt = f"Rp {total_price:,}".replace(",", ".")
        lines.append(f"💰 *TOTAL PEMBAYARAN:* {total_fmt}")

        if order_notes:
            lines.append(f"💬 *Catatan Tambahan:* {order_notes.strip()}")

        lines.append("------------------------------------")
        lines.append("Halo Dapur Mamita, saya baru saja memesan lewat web menu. Mohon diproses ya! Terima kasih 🙏")

        return "\n".join(lines)

    @classmethod
    def create_order_wa_url(
        cls,
        phone_target: Optional[str],
        order_id: int,
        customer_name: str,
        table_info: str,
        cart_items: List[Dict[str, Any]],
        total_price: int,
        order_notes: Optional[str] = None
    ) -> str:
        """Membuat URL lengkap wa.me dengan pesan pesanan yang ter-encode aman."""
        clean_phone = cls.normalize_phone(phone_target)
        message_text = cls.generate_order_message(
            order_id=order_id,
            customer_name=customer_name,
            table_info=table_info,
            cart_items=cart_items,
            total_price=total_price,
            order_notes=order_notes
        )
        encoded_message = urllib.parse.quote(message_text)
        return f"https://wa.me/{clean_phone}?text={encoded_message}"
