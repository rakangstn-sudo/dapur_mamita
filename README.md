# 🍲 Dapur Mamita — Web App Menu Digital & Pemesanan Meja QR

Aplikasi web pemesanan makanan berbasis **QR Code Meja** untuk UMKM kuliner **Dapur Mamita**, dibangun menggunakan **Flask (Python 3.11+)**, **PostgreSQL di Supabase**, dan antarmuka responsif bernuansa hangat (**Bootstrap 5**).

---

## 🌟 Fitur Utama

- 📱 **QR Code per Meja (Konsep Mie Gacoan / Kopi Kenangan)**: Pelanggan scan QR di meja &rarr; otomatis masuk ke daftar menu digital khusus meja tersebut tanpa perlu install aplikasi.
- 🛒 **Pemesanan & Keranjang Belanja**: Keranjang tersimpan aman di server-side session Flask, lengkap dengan catatan khusus per item (contoh: "pedas level 2", "tanpa es").
- ⏱️ **Status Pesanan Real-time (Polling API)**: Halaman status dengan indikator visual step-by-step (*Menunggu &rarr; Diproses &rarr; Selesai*) auto-refresh setiap beberapa detik tanpa websocket yang rumit.
- 🔒 **Panel Admin Terproteksi**:
  - Login admin dengan password ter-hash (`werkzeug.security`).
  - **Dashboard Operasional**: Ringkasan pesanan hari ini, total omzet, status antrean masak.
  - **Pesanan Masuk Realtime**: Antrean pesanan dapur dengan polling otomatis dan aksi ubah status.
  - **CRUD Menu**: Atur menu, harga, kategori, ketersediaan, serta upload foto ke **Supabase Storage**.
  - **Manajemen Meja & QR Code**: Otomatis menghasilkan kode unik meja dan file QR Code PNG siap cetak / unduh.
  - **Profil UMKM**: Pengaturan nama usaha, cerita kuliner, jam buka, dan tautan langsung WhatsApp.
- 🛡️ **Keamanan**: Proteksi CSRF (`Flask-WTF`) di semua form, validasi ukuran & format upload gambar (max 2MB, JPG/PNG), serta pembatasan akses API status pesanan per session meja.

---

## 📁 Struktur Folder

```text
dapur_mamita/
│
├── app/
│   ├── __init__.py              # App Factory, inisialisasi extensions & registrasi blueprint
│   ├── models.py                # 6 Model database (AdminUser, ProfilUMKM, MenuItem, Meja, Pesanan, DetailPesanan)
│   ├── forms.py                 # WTForms validasi & CSRF (LoginForm, MenuForm, ProfilForm, MejaForm, CheckoutForm)
│   ├── config.py                # Konfigurasi aplikasi & pembacaan environment variable
│   ├── extensions.py            # Instance SQLAlchemy, Flask-Login, Flask-Migrate, CSRFProtect
│   │
│   ├── main/                    # Blueprint publik & katalog menu customer
│   │   ├── __init__.py
│   │   └── routes.py            # Landing page, daftar menu digital (?meja=xx), tentang kami
│   │
│   ├── order/                   # Blueprint alur keranjang & pemesanan customer
│   │   ├── __init__.py
│   │   └── routes.py            # Tambah keranjang, update qty, checkout DB, halaman status
│   │
│   ├── auth/                    # Blueprint autentikasi admin
│   │   ├── __init__.py
│   │   └── routes.py            # Login & logout admin
│   │
│   ├── admin/                   # Blueprint panel admin dapur
│   │   ├── __init__.py
│   │   └── routes.py            # Dashboard, CRUD menu, meja & generator QR, pesanan masuk, profil
│   │
│   ├── api/                     # Blueprint API JSON untuk polling status
│   │   ├── __init__.py
│   │   └── routes.py            # Endpoint /api/pesanan/<id>/status & /api/admin/pesanan
│   │
│   ├── templates/               # Template Jinja2 + Bootstrap 5
│   │   ├── base.html            # Layout utama (Navbar, Flash message, Footer, Font Poppins)
│   │   ├── main/
│   │   │   ├── index.html       # Beranda & Hero Section
│   │   │   ├── menu_list.html   # Katalog menu & filter kategori
│   │   │   └── tentang.html     # Profil & info kontak UMKM
│   │   ├── order/
│   │   │   ├── keranjang.html   # Review keranjang & form checkout
│   │   │   └── status_pesanan.html # Stepper status auto-polling
│   │   ├── auth/
│   │   │   └── login.html       # Halaman login admin
│   │   └── admin/
│   │       ├── dashboard.html   # Ringkasan analitik harian
│   │       ├── menu_form.html   # CRUD menu & upload foto
│   │       ├── meja_list.html   # Daftar meja, unduh & regenerate QR
│   │       ├── profil_form.html # Form edit profil UMKM
│   │       └── pesanan_masuk.html # Realtime dapur order board
│   │
│   └── static/
│       ├── css/style.css        # Palet warna hangat (coklat, krem, oranye) & animasi
│       ├── js/
│       │   ├── cart.js          # Feedback visual keranjang di client
│       │   └── polling.js       # Auto-refresh status pesanan customer via fetch()
│       └── qrcodes/             # Direktori output gambar PNG QR code per meja
│
├── .env                         # Konfigurasi privat (jangan commit ke Git)
├── .env.example                 # Template environment variables
├── .gitignore
├── requirements.txt             # Dependensi Python
├── run.py                       # Runner entry point aplikasi
└── seed.py                      # Inisialisasi akun admin default, contoh menu & meja
```

---

## ⚙️ Panduan Setup Supabase (Database & Storage)

Aplikasi ini menggunakan **PostgreSQL** dan **Storage Bucket** gratis dari Supabase:

### 1. Ambil `DATABASE_URL` (Koneksi PostgreSQL)
1. Buka [https://supabase.com](https://supabase.com) dan masuk ke Dashboard project Anda.
2. Klik ikon **Project Settings** (ikon gerigi di kiri bawah) &rarr; pilih menu **Database**.
3. Scroll ke bagian **Connection string**, pilih tab **URI**.
4. Salin URL tersebut. Bentuknya seperti:
   ```text
   postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
   ```
   > 💡 *Ganti `[PASSWORD]` dengan password database yang Anda tentukan saat membuat project Supabase.*

### 2. Buat Storage Bucket untuk Upload Gambar
1. Di sidebar kiri Supabase, buka menu **Storage**.
2. Klik **New Bucket**, beri nama: `dapur-mamita`.
3. Aktifkan opsi **Public bucket** (agar foto menu dan profil UMKM bisa diakses publik melalui URL).
4. Simpan bucket.

### 3. Ambil `SUPABASE_URL` dan `SUPABASE_KEY`
1. Di dashboard Supabase, buka **Project Settings** &rarr; menu **API**.
2. Salin **Project URL** &rarr; masukkan sebagai nilai `SUPABASE_URL`.
3. Salin **Project API Keys** bagian `anon` / `public` (atau `service_role` jika membutuhkan akses bypass RLS) &rarr; masukkan sebagai nilai `SUPABASE_KEY`.

---

## 🚀 Instalasi & Menjalankan di Lokal

### 1. Clone & Masuk ke Folder Proyek
```bash
git clone <url-repo-anda>
cd dapur_mamita
```

### 2. Buat & Aktifkan Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependensi
```bash
pip install -r requirements.txt
```

### 4. Buat File `.env`
Salin file `.env.example` menjadi `.env`:
```bash
cp .env.example .env     # Linux / Mac
copy .env.example .env   # Windows
```
Buka file `.env` dan isi sesuai kredensial Anda:
```env
SECRET_KEY=kunci-rahasia-acak-super-aman
FLASK_ENV=development
DATABASE_URL=postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
SUPABASE_URL=https://[PROJECT-REF].supabase.co
SUPABASE_KEY=eyJhbGciOi...
SUPABASE_BUCKET=dapur-mamita
BASE_URL=http://localhost:5000
```

### 5. Inisialisasi Database & Data Awal (Seed)
Jalankan perintah berikut untuk membuat tabel dan data contoh:
```bash
python seed.py
```
> Script ini otomatis membuat tabel database, akun admin default (`admin` / `admin123`), 10 menu kuliner contoh, serta 5 meja fisik lengkap beserta file gambar QR Code di folder `app/static/qrcodes/`.

Alternatif jika ingin menggunakan **Flask-Migrate**:
```bash
flask db init
flask db migrate -m "Inisialisasi tabel awal"
flask db upgrade
```

### 6. Jalankan Server Development
```bash
python run.py
```
Akses di browser:
- 🌐 **Halaman Publik**: `http://localhost:5000`
- 📱 **Simulasi Scan QR Meja 1**: `http://localhost:5000/menu?meja=MEJA1_XXXXXX` (lihat kode spesifik saat menjalankan `seed.py` atau di tabel meja)
- 🔐 **Login Admin**: `http://localhost:5000/auth/login`
  - **Username**: `admin`
  - **Password**: `admin123`

---

## 🌐 Panduan Deploy ke Hosting dengan Domain `.my.id`

Aplikasi Dapur Mamita siap di-deploy ke berbagai layanan hosting:

### A. Deploy di cPanel / Shared Hosting (CloudLinux / cPanel Python App)
1. Pastikan hosting mendukung **Setup Python App** (Passenger).
2. Buat subdomain atau domain utama bertarget domain `.my.id` Anda (misal `dapurmamita.my.id`).
3. Di menu **Setup Python App**:
   - Pilih versi Python: `3.11` atau yang terbaru.
   - Application root: `/home/user/dapur_mamita`
   - Application URL: `dapurmamita.my.id`
   - Application startup file: `passenger_wsgi.py` (atau arahkan ke `run.py`).
4. Buat file `passenger_wsgi.py` di root direktori jika menggunakan Passenger:
   ```python
   import sys, os
   sys.path.append(os.getcwd())
   from app import create_app
   application = create_app()
   ```
5. Di bagian **Environment Variables** di panel cPanel Python App, tambahkan:
   - `SECRET_KEY`: string acak panjang untuk sesi produksi.
   - `DATABASE_URL`: URI connection pooler Supabase.
   - `SUPABASE_URL`: URL project Supabase Anda.
   - `SUPABASE_KEY`: API key Supabase Anda.
   - `SUPABASE_BUCKET`: `dapur-mamita`
   - `BASE_URL`: `https://dapurmamita.my.id` (penting: agar QR code yang di-generate mengarah ke domain asli Anda).
6. Jalankan perintah `pip install -r requirements.txt` via Terminal cPanel.

### B. Deploy di VPS (Ubuntu 22.04 / 24.04 dengan Nginx + Gunicorn)
1. Point DNS domain `.my.id` ke IP Public VPS Anda (A Record: `@` dan `www`).
2. Install Python, git, pip, dan Nginx di server.
3. Jalankan aplikasi menggunakan **Gunicorn**:
   ```bash
   gunicorn -w 4 -b 127.0.0.1:5000 "app:create_app()"
   ```
4. Pasang SSL gratis menggunakan **Let's Encrypt / Certbot**:
   ```bash
   sudo certbot --nginx -d dapurmamita.my.id
   ```

---

## 👨‍🍳 Alur Penggunaan Aplikasi

1. **Persiapan Pemilik/Admin**:
   - Login ke `/auth/login`.
   - Buka menu **Kelola Meja**, unduh PNG QR Code untuk Meja 1 s/d selesai.
   - Cetak dan tempel di meja makan pengunjung.
2. **Pelanggan Datang**:
   - Duduk di meja fisik (misal Meja 3).
   - Membuka kamera smartphone & scan QR code meja.
   - Langsung terbuka menu digital dengan identitas meja aktif di layar.
   - Pilih aneka menu, atur catatan khusus, dan klik **Pesan Sekarang**.
3. **Dapur & Kasir**:
   - Halaman **Pesanan Masuk** di laptop/tablet dapur otomatis memperbarui daftar tanpa perlu refresh manual.
   - Koki melihat rincian item, catatan ("pedas level 2"), dan klik tombol **Mulai Masak**.
   - Setelah makanan diantar, klik **Pesanan Siap / Selesai**.
4. **Pelanggan**:
   - Di layar HP pelanggan, progress stepper otomatis bergerak dari *Menunggu* &rarr; *Sedang Diproses* &rarr; *Selesai*.

---

## 📄 Lisensi & Pembuat
Dikembangkan khusus untuk **Dapur Mamita** — Solusi Digitalisasi UMKM Kuliner Indonesia. Bebas dimodifikasi dan dikembangkan lebih lanjut (misalnya penambahan payment gateway QRIS seperti Midtrans/Xendit di masa mendatang).
