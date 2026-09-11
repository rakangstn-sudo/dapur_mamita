"""
Storage Service — Pengelolaan upload aset/gambar ke Supabase Storage.
"""

import uuid
from typing import Optional
from flask import current_app


class StorageService:
    """Service untuk upload dan manajemen file gambar."""

    @staticmethod
    def generate_filename(original_filename: str, prefix: str = 'file') -> str:
        """Menghasilkan nama file acak yang unik dan aman."""
        ext = original_filename.rsplit('.', 1)[-1].lower() if '.' in original_filename else 'jpg'
        unique_token = uuid.uuid4().hex[:10]
        return f"{prefix}_{unique_token}.{ext}"

    @classmethod
    def upload_file(cls, file_storage, filename: str) -> str:
        """
        Upload FileStorage (dari form WTForms/Flask request) ke Supabase Storage.
        Returns:
            str: URL publik file jika berhasil, atau string kosong jika gagal/belum dikonfigurasi.
        """
        if not file_storage:
            return ''

        try:
            from supabase import create_client

            supabase_url = current_app.config.get('SUPABASE_URL')
            supabase_key = current_app.config.get('SUPABASE_KEY')
            bucket_name = current_app.config.get('SUPABASE_BUCKET', 'dapur-mamita')

            if not supabase_url or not supabase_key:
                current_app.logger.warning('Supabase belum dikonfigurasi, skip upload.')
                return ''

            client = create_client(supabase_url, supabase_key)

            # Baca file binary
            file_bytes = file_storage.read()
            content_type = getattr(file_storage, 'content_type', 'image/jpeg') or 'image/jpeg'
            file_path = f"uploads/{filename}"

            # Eksekusi upload
            client.storage.from_(bucket_name).upload(
                path=file_path,
                file=file_bytes,
                file_options={"content-type": content_type}
            )

            # Dapatkan URL publik yang bisa diakses langsung
            public_url = client.storage.from_(bucket_name).get_public_url(file_path)
            return public_url or ''

        except Exception as err:
            current_app.logger.error(f'Gagal upload file "{filename}" ke Supabase: {err}')
            return ''
