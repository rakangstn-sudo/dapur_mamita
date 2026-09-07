"""
Script Seed Data Awal Dapur Mamita.
Mengisi:
- 1 Akun Admin default (username: admin, password: admin123)
- 1 Profil UMKM default
- 10 Contoh Menu (Makanan, Minuman, Snack, Paket)
- 5 Contoh Meja lengkap dengan QR code PNG

Cara menjalankan:
    python seed.py
"""

import os
import uuid
from app import create_app
from app.extensions import db
from app.models import AdminUser, ProfilUMKM, MenuItem, Meja
from app.admin.routes import generate_qr_code

app = create_app()


def seed_database():
    with app.app_context():
        print(">> Menyiapkan tabel database...")
        db.create_all()

        # 1. Seed Admin
        admin = AdminUser.query.filter_by(username='admin').first()
        if not admin:
            admin = AdminUser(username='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            print("   [+] Admin default dibuat: admin / admin123")
        else:
            print("   [*] Admin 'admin' sudah ada.")

        # 2. Seed Profil UMKM
        profil = ProfilUMKM.query.first()
        if not profil:
            profil = ProfilUMKM(
                nama_umkm="Dapur Mamita",
                deskripsi="Sajian rumahan khas yang dimasak dengan cinta, bahan segar harian, dan rempah Nusantara terbaik.",
                alamat="Jl. Kenangan Kuliner No. 12, Kota Kuliner, Indonesia",
                no_wa="6281234567890",
                jam_operasional="Setiap Hari: 10.00 - 22.00 WIB"
            )
            db.session.add(profil)
            print("   [+] Profil UMKM berhasil diinisialisasi.")
        else:
            print("   [*] Profil UMKM sudah ada.")

        # 3. Seed Menu Items
        contoh_menu = [
            {
                "nama": "Dimsum Goreng (Isi 4)",
                "deskripsi": "Dimsum goreng gurih renyah isi olahan ayam, disajikan 4 pcs hangat-hangat dengan cocolan saus pedas manis. Pas buat nyemil rame-rame!",
                "harga": 5000,
                "kategori": "Snack",
                "tersedia": True,
                "foto_url": "/static/images/menu/dimsum_goreng.jpg"
            },
            {
                "nama": "Udang Keju (Isi 2)",
                "deskripsi": "Olahan udang gurih berbalut tepung roti krispi dengan isian keju lumer di dalamnya ala resto hits. Disajikan 2 pcs gurih melted!",
                "harga": 5000,
                "kategori": "Snack",
                "tersedia": True,
                "foto_url": ""
            },
            {
                "nama": "Lumpia Beef Kornet",
                "deskripsi": "Kulit lumpia garing renyah dengan isian kornet sapi gurih melimpah, dipadu saus sambal dan mayones lezat. Renyah harga bersahabat!",
                "harga": 5000,
                "kategori": "Snack",
                "tersedia": True,
                "foto_url": ""
            },
            {
                "nama": "Seblak Tulang",
                "deskripsi": "Seblak kuah merah pedas gurih dengan aroma rempah kencur khas. Isian potongan tulang empuk, kerupuk basah kenyal, makaroni, dan telur. Pedas nampol!",
                "harga": 10000,
                "kategori": "Makanan",
                "tersedia": True,
                "foto_url": "/static/images/menu/seblak_tulang.jpg"
            },
            {
                "nama": "Mie Jebew + Pangsit",
                "deskripsi": "Mie pedas kenyal berlumur bumbu cabai rawit gurih meresap, taburan ayam cincang, dan dilengkapi pangsit goreng renyah ala Mie Gacoan!",
                "harga": 10000,
                "kategori": "Makanan",
                "tersedia": True,
                "foto_url": "/static/images/menu/mie_jebew.jpg"
            },
            {
                "nama": "Kebab Mini",
                "deskripsi": "Kulit tortilla panggang renyah ukuran pas ngemil dengan daging kebab gurih, selada segar, dan lelehan saus mayo pedas.",
                "harga": 5000,
                "kategori": "Snack",
                "tersedia": True,
                "foto_url": ""
            },
            {
                "nama": "Kebab Jumbo",
                "deskripsi": "Kebab porsi besar dengan ekstra daging sapi melimpah, selada renyah, saus keju dan mayones spesial.",
                "harga": 10000,
                "kategori": "Snack",
                "tersedia": True,
                "foto_url": ""
            },
            {
                "nama": "Roti Goreng Selai",
                "deskripsi": "Roti empuk berbalut tepung panir krispi keemasan dengan isian selai manis lumer yang meleleh saat digigit hangat.",
                "harga": 5000,
                "kategori": "Dessert",
                "tersedia": True,
                "foto_url": ""
            },
            {
                "nama": "Es Teh Manis",
                "deskripsi": "Seduhan teh melati wangi dengan gula asli dan es batu segar dingin, teman paling pas untuk meredakan pedas.",
                "harga": 3000,
                "kategori": "Minuman",
                "tersedia": True,
                "foto_url": ""
            },
            {
                "nama": "Es Teh Jumbo",
                "deskripsi": "Es teh manis melati porsi cup jumbo super puas, dingin menyegarkan.",
                "harga": 5000,
                "kategori": "Minuman",
                "tersedia": True,
                "foto_url": ""
            }
        ]

        for data in contoh_menu:
            existing = MenuItem.query.filter_by(nama=data['nama']).first()
            if not existing:
                item = MenuItem(**data)
                db.session.add(item)
                print(f"   [+] Menu ditambahkan: {data['nama']}")
            else:
                print(f"   [*] Menu '{data['nama']}' sudah ada.")

        # 4. Seed Meja & Generate QR
        print("\n>> Mengisi Meja & Generate QR code...")
        for no in range(1, 6):
            meja = Meja.query.filter_by(nomor_meja=no).first()
            if not meja:
                kode_unik = f"MEJA{no}_{uuid.uuid4().hex[:6].upper()}"
                qr_path = generate_qr_code(kode_unik, app)

                meja = Meja(
                    nomor_meja=no,
                    kode_unik=kode_unik,
                    qr_image_url=qr_path
                )
                db.session.add(meja)
                print(f"   [+] Meja {no} dibuat (Kode: {kode_unik}, QR: static/{qr_path})")
            else:
                print(f"   [*] Meja {no} sudah ada (Kode: {meja.kode_unik})")

        db.session.commit()
        print("\n=======================================================")
        print("  SEED DATA SELESAI!")
        print("  Akun Admin : admin")
        print("  Password   : admin123")
        print("  URL Admin  : http://localhost:5000/auth/login")
        print("  Menu Publik: http://localhost:5000")
        print("=======================================================")


if __name__ == '__main__':
    seed_database()
