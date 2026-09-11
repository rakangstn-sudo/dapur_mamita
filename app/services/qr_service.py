"""
QR Service — Pembuatan QR Code dinamis dan deteksi domain server.
"""

from io import BytesIO
import qrcode
from flask import current_app, has_request_context, request


class QRService:
    """Service untuk membuat dan mengalirkan QR Code langsung dari memori."""

    @staticmethod
    def get_base_url() -> str:
        """
        Mendapatkan domain dasar aplikasi secara otomatis.
        Mendukung reverse proxy SSL di Vercel / Nginx (X-Forwarded-Proto).
        """
        if has_request_context() and request.host_url:
            scheme = request.headers.get('X-Forwarded-Proto', request.scheme)
            return f"{scheme}://{request.host}".rstrip('/')
        return current_app.config.get('BASE_URL', 'http://localhost:5000').rstrip('/')

    @staticmethod
    def create_qr_buffer(
        url: str,
        fill_color: str = '#3E2723',
        back_color: str = 'white',
        box_size: int = 10,
        border: int = 4
    ) -> BytesIO:
        """
        Menghasilkan gambar QR code PNG dalam bentuk BytesIO memory buffer
        sehingga ramah serverless (tidak memerlukan akses write ke disk).
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=box_size,
            border=border,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color=fill_color, back_color=back_color)
        buf = BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return buf
