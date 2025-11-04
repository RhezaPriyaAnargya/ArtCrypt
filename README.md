# ArtCrypt — Platform Kriptografi Karya Digital

ArtCrypt adalah aplikasi berbasis Streamlit untuk melindungi karya digital (gambar, dokumen, audio) dengan enkripsi berlapis dan watermark Bit Plane Slicing. Aplikasi ini dirancang untuk satu peran (Creator) yang mengelola seluruh siklus hidup karya: unggah, lihat/unduh, verifikasi keaslian, dan hapus.

> Teknologi utama: Python, Streamlit, SQLite, cryptography, PyCryptodome, Pillow, NumPy

---

## Fitur Utama

- Autentikasi Creator (Login/Register) dengan penyimpanan kredensial terenkripsi
- Enkripsi metadata (judul & deskripsi) berlapis
- Enkripsi file (PDF/DOC/Audio/Gambar) berlapis sebelum disimpan ke DB
- Watermark gambar dengan teknik Bit Plane Slicing (BPS), bit plane dapat dipilih
- Galeri karya dengan lazy loading, pagination, download, dan hapus
- Verifikasi keaslian: ekstraksi watermark dan pencocokan dengan metadata watermark terenkripsi di DB
- Analisis database (viewer) dan ekspor laporan JSON

---

## Arsitektur Singkat

- UI: `app.py` (Streamlit)
- Lapisan Kriptografi & Watermark: `crypto_utils.py`
- Koneksi & Skema DB: `connection.py` (SQLite `artcrypt.db`)
- Analisis Data Terenkripsi: `view_encrypted_data.py` (+ opsional `quick_analysis.py`)

---

## Alur Aplikasi (Web App Flow)

1) Login/Register
- Username → Camellia-CBC → Base64 → simpan ke DB
- Password → HMAC-SHA384 → Camellia-CBC → Base64 → simpan ke DB
- Saat login: dekripsi username dan verifikasi hash password

2) Upload Karya
- Metadata (judul, deskripsi): Caesar → AES-128-GCM → Camellia-CBC → Base64 → DB
- File (PDF/DOC/Audio/Gambar): AES-128-CTR → Camellia-CBC → Base64 → DB
- Jika gambar: sisip watermark BPS (default aman; opsi bit 0–3), simpan juga watermark terenkripsi (Caesar → AES-GCM → Camellia)

3) Lihat/Unduh Karya
- Dekripsi metadata & file on-demand (lazy)
- Ekstraksi watermark untuk gambar jika diminta

4) Verifikasi Karya
- Bandingkan watermark terekstrak dengan watermark terenkripsi di DB (setelah dekripsi)

5) Hapus Karya
- Konfirmasi → hapus permanen dari database

---

## Algoritma Kriptografi per Fitur

- Login & Register
  - Username: Camellia-CBC (`encrypt_username`)
  - Password: HMAC-SHA384 + Camellia-CBC (`encrypt_password`, `verify_user`)
- Metadata
  - Caesar → AES-128-GCM → Camellia-CBC (`encrypt_metadata`, `decrypt_metadata`)
- File
  - AES-128-CTR → Camellia-CBC (`encrypt_file`, `decrypt_file`)
- Watermark Gambar
  - Bit Plane Slicing (pilih bit 0–3; default aman) (`embed_watermark_bitplane`, `extract_watermark_bitplane`)

> Catatan: Di beberapa versi sebelumnya terdapat path ChaCha20/Salsa20. Implementasi saat ini menggunakan AES-CTR + Camellia untuk file; watermark tetap BPS.

---

## Persyaratan

- Python 3.10+ (disarankan)
- Windows PowerShell (perintah di bawah menggunakan PowerShell)
- Paket Python (lihat `requirements.txt`). Jika belum ada, gunakan daftar di bawah:

```
streamlit>=1.28.0
cryptography>=41.0.0
pycryptodome>=3.19.0
Pillow>=10.0.0
numpy>=1.24.0
```

---

## Instalasi

```powershell
# 1) Masuk ke folder proyek
cd "d:\1. UNIV\1. Materi Univ\SEM 5\Kriptografi\Projek akhir\ArtCrypt"

# 2) Buat & aktifkan virtualenv (opsional tapi disarankan)
python -m venv .venv; .\.venv\Scripts\Activate.ps1

# 3) Instal dependensi
pip install -r requirements.txt
```

Jika `requirements.txt` belum lengkap, install manual:

```powershell
pip install streamlit cryptography pycryptodome pillow numpy
```

---

## Menjalankan Aplikasi

```powershell
# Jalankan aplikasi Streamlit
streamlit run app.py
```

Aplikasi akan terbuka di browser (localhost). Buat akun baru atau login, kemudian unggah karya.

---

## Cara Pakai (Ringkas)

1) Login/Register
- Isi username & password → klik Register atau Login.

2) Upload Karya
- Isi judul dan deskripsi.
- Pilih file (PDF/DOC/MP3/PNG/JPG).
- Jika file gambar, pilih preset/bit planes untuk watermark (LSB-only tercepat).
- Klik Upload. Progres enkripsi & penyimpanan akan ditampilkan.

3) Galeri Karya
- Data dimuat per halaman (pagination) dan hanya didekripsi saat Anda klik “Muat”.
- Anda dapat melihat pratinjau, mengunduh, memverifikasi watermark (opsional), atau menghapus karya.

4) Verifikasi Karya
- Pilih karya asli dari DB, unggah gambar pembanding, ekstrak watermark keduanya, dan bandingkan.

---

## Bit Plane Slicing (BPS) — Ringkas

- Setiap piksel 8 bit (bit 0=LSB … bit 7=MSB).
- Watermark disisipkan ke bit planes pilihan—umumnya bit 0–2 untuk perubahan visual minimal.
- Trade-off: semakin banyak/makin tinggi bit yang dipakai → kapasitas naik, kualitas gambar turun.
- Fungsi terkait:
  - `embed_watermark_bitplane(image_file, watermark_text, bit_planes=[...])`
  - `extract_watermark_bitplane(image_bytes, bit_planes=[...])`

Tips kecepatan:
- Gunakan preset “LSB Only” untuk upload cepat.
- Ekstraksi watermark dilakukan hanya saat checkbox verifikasi diaktifkan (hemat waktu).

---

## Struktur Database (ringkas)

Tabel `users`
- `id` INTEGER PK
- `username_encrypted` TEXT (Base64 hasil Camellia-CBC)
- `password_encrypted` TEXT (Base64 hasil HMAC-SHA384→Camellia-CBC)

Tabel `artworks`
- `id` INTEGER PK
- `user_id` INTEGER FK → users.id
- `title_encrypted` TEXT (Base64 Caesar→AES-GCM→Camellia)
- `description_encrypted` TEXT (Base64 Caesar→AES-GCM→Camellia)
- `file_data` BLOB (Base64 AES-CTR→Camellia)
- `file_type` TEXT (MIME)
- `watermark_data` TEXT (opsional; Base64 Caesar→AES-GCM→Camellia)

---

## Analisis Database (Opsional)

Jalankan viewer untuk melihat ringkasan dan mencoba dekripsi metadata:

```powershell
python view_encrypted_data.py
```

Script akan menampilkan statistik, contoh hasil dekripsi metadata, dan (opsional) mengekspor laporan JSON.

> Tersedia juga `quick_analysis.py` untuk analisis cepat tanpa input.

---

## Keamanan & Performa

- Nonce/IV acak untuk setiap enkripsi; penyimpanan data di-Base64.
- Tag autentikasi dari AES-GCM melindungi integritas metadata.
- Watermark BPS menyematkan identitas Creator di gambar.
- Optimasi performa: lazy loading & dekripsi on-demand, pagination, opsi kualitas pratinjau, dan jalur cepat LSB untuk watermark.

---

## Troubleshooting

- "ModuleNotFoundError: cryptography/pycryptodome/Pillow":
  ```powershell
  pip install cryptography pycryptodome pillow numpy
  ```
- "Python integer -2 out of bounds for uint8": terjadi saat manipulasi bit pada array `uint8`. Sudah diperbaiki dengan casting `int()` sebelum operasi bit dan kembali ke `np.uint8`.
- "cannot identify image file <_io.BytesIO...>": pastikan pointer file di-reset (`seek(0)`) sebelum `Image.open(...)`.
- Gagal install `salsa20`: proyek ini tidak membutuhkan paket itu; gunakan implementasi saat ini (AES-CTR + Camellia). 
- DB locked: tutup aplikasi lain yang memakai `artcrypt.db` atau salin file ke lokasi lain.

---

## Catatan Keamanan

- Jangan gunakan `MASTER_KEY` bawaan untuk produksi. Ganti dan simpan sebagai variabel lingkungan; sesuaikan pemuatan kunci di `crypto_utils.py`.
- Backup database secara berkala.

---

## Lisensi

Proyek ini untuk keperluan pembelajaran. Sesuaikan lisensi sesuai kebutuhan sebelum publikasi.

---

## Kontributor

- Creator: Anda
- Repo: ArtCrypt
