"""
Storage Service — Pengelolaan upload aset/gambar langsung ke Supabase Storage REST API
Mendukung semua format API Key Supabase (JWT anon/service_role maupun Secret sb_secret_...)
dengan fallback penyimpanan lokal.
"""

import os
import uuid
import urllib.request
import urllib.error
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
        Upload FileStorage langsung ke Supabase Storage REST API.
        Returns:
            Tuple[str, Optional[str]]: (public_url, error_message)
        """
        if not file_storage:
            return '', None

        raw_url = str(current_app.config.get('SUPABASE_URL', '') or '').strip()
        url_lines = [l.strip().strip("'\"") for l in raw_url.splitlines() if l.strip()]
        supabase_url = url_lines[0].rstrip('/') if url_lines else ''

        raw_key = str(current_app.config.get('SUPABASE_KEY', '') or '').strip()
        key_lines = [l.strip().strip("'\"") for l in raw_key.splitlines() if l.strip()]
        supabase_key = key_lines[0] if key_lines else ''

        raw_bucket = str(current_app.config.get('SUPABASE_BUCKET', '') or '').strip()
        bucket_lines = [l.strip().strip("'\"") for l in raw_bucket.splitlines() if l.strip()]
        bucket_name = bucket_lines[0] if bucket_lines else 'dapur_mamita'

        err_msg = None

        # 1. Upload langsung via Supabase REST API (menggunakan urllib bawaan Python)
        if supabase_url and supabase_key:
            try:
                upload_endpoint = f"{supabase_url}/storage/v1/object/{bucket_name}/uploads/{filename}"
                content_type = getattr(file_storage, 'content_type', 'image/jpeg') or 'image/jpeg'

                file_storage.seek(0)
                file_bytes = file_storage.read()

                headers = {
                    "apikey": supabase_key,
                    "Authorization": f"Bearer {supabase_key}",
                    "Content-Type": content_type,
                    "x-upsert": "true"
                }

                req = urllib.request.Request(
                    upload_endpoint,
                    data=file_bytes,
                    headers=headers,
                    method="POST"
                )

                with urllib.request.urlopen(req, timeout=20) as response:
                    if response.status in (200, 201):
                        public_url = f"{supabase_url}/storage/v1/object/public/{bucket_name}/uploads/{filename}"
                        current_app.logger.info(f"Berhasil upload ke Supabase: {public_url}")
                        return public_url, None

            except urllib.error.HTTPError as http_err:
                body = http_err.read().decode('utf-8', errors='ignore')
                err_msg = f"Supabase HTTP {http_err.code}: {body}"
                current_app.logger.error(f"Gagal upload Supabase REST: {err_msg}")
            except Exception as err:
                err_msg = f"Gagal upload Supabase: {err}"
                current_app.logger.error(f"Exception upload Supabase: {err_msg}")
        else:
            err_msg = "SUPABASE_URL atau SUPABASE_KEY belum diisi."

        # 2. Fallback: Simpan ke folder lokal app/static/uploads jika berjalan di laptop/localhost
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
            current_app.logger.error(f"Gagal simpan ke penyimpanan lokal: {fs_err}")
            return '', err_msg or str(fs_err)

    @classmethod
    def upload_file(cls, file_storage, filename: str) -> str:
        """Metode upload backward-compatible yang mengembalikan URL string."""
        url, _ = cls.upload_file_with_status(file_storage, filename)
        return url
