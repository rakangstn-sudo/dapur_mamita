"""
Storage Service — Pengelolaan upload aset/gambar ke Supabase Storage
dengan fallback penyimpanan lokal cerdas untuk server lokal/laptop.
"""

import os
import uuid
from typing import Tuple, Optional
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
    def upload_file_with_status(cls, file_storage, filename: str) -> Tuple[str, Optional[str]]:
        """
        Upload FileStorage ke Supabase Storage, atau fallback ke folder lokal app/static/uploads/.
        Returns:
            Tuple[str, Optional[str]]: (public_url, error_message)
        """
        if not file_storage:
            return '', None

        # Cek apakah Supabase dikonfigurasi
        supabase_url = current_app.config.get('SUPABASE_URL', '').strip()
        supabase_key = current_app.config.get('SUPABASE_KEY', '').strip()
        bucket_name = current_app.config.get('SUPABASE_BUCKET', 'dapur_mamita').strip()

        # Cek apakah format key Supabase valid (harus berupa JWT token diawali 'eyJ')
        is_jwt_key = supabase_key.startswith('eyJ')
        supabase_configured = bool(supabase_url and supabase_key)

        # 1. Coba upload ke Supabase jika key valid
        if supabase_configured and is_jwt_key:
            try:
                from supabase import create_client
                client = create_client(supabase_url, supabase_key)

                file_storage.seek(0)
                file_bytes = file_storage.read()
                content_type = getattr(file_storage, 'content_type', 'image/jpeg') or 'image/jpeg'
                file_path = f"uploads/{filename}"

                client.storage.from_(bucket_name).upload(
                    path=file_path,
                    file=file_bytes,
                    file_options={"content-type": content_type}
                )

                public_url = client.storage.from_(bucket_name).get_public_url(file_path)
                if public_url:
                    return public_url, None

            except Exception as err:
                current_app.logger.error(f'Gagal upload ke Supabase: {err}')
                supabase_err = str(err)
        elif supabase_configured and not is_jwt_key:
            supabase_err = (
                "SUPABASE_KEY yang dimasukkan berawalan 'sb_secret_...', "
                "bukan Project API Key (JWT) dari Supabase. "
                "Silakan gunakan API Key 'anon' atau 'service_role' dari Dashboard Supabase -> Project Settings -> API."
            )
            current_app.logger.warning(supabase_err)
        else:
            supabase_err = "Supabase Storage belum dikonfigurasi."

        # 2. Fallback: Simpan ke folder lokal app/static/uploads jika filesystem writable (seperti di laptop/localhost)
        try:
            static_folder = current_app.static_folder or os.path.join(current_app.root_path, 'static')
            uploads_dir = os.path.join(static_folder, 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)

            filepath = os.path.join(uploads_dir, filename)
            file_storage.seek(0)
            file_storage.save(filepath)

            local_url = f"/static/uploads/{filename}"
            return local_url, None

        except (OSError, IOError) as fs_err:
            # Di Vercel serverless, filesystem selain /tmp bersifat read-only
            current_app.logger.error(f'Gagal simpan ke penyimpanan lokal: {fs_err}')
            return '', f"Gagal upload: {supabase_err}"

    @classmethod
    def upload_file(cls, file_storage, filename: str) -> str:
        """Metode upload backward-compatible yang mengembalikan URL string."""
        url, _ = cls.upload_file_with_status(file_storage, filename)
        return url
