import sqlite3
import base64
import os
from datetime import datetime
from crypto_utils import verify_user

def view_encrypted_data():
    """Tampilkan data terenkripsi di database"""
    conn = sqlite3.connect('artcrypt.db')
    cursor = conn.cursor()
    
    print("🔐 DATA TERENKRIPSI DI DATABASE")
    print("=" * 70)
    
    # Tampilkan tabel users
    print("\n👥 TABEL USERS:")
    print("-" * 70)
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    
    if not users:
        print("📭 Belum terdapat user terdaftar")
        print("💡 Register user melalui aplikasi web terlebih dahulu")
    else:
        for user in users:
            user_id, username_enc, password_enc = user
            print(f"ID: {user_id}")
            print(f"  Username (Base64): {username_enc}")
            print(f"  Password (Base64): {password_enc}")
            print(f"  Panjang Username: {len(username_enc)} karakter")
            print(f"  Panjang Password: {len(password_enc)} karakter")
            print()
    
    # Tampilkan tabel artworks dengan ukuran MB
    print("\n🎨 TABEL ARTWORKS:")
    print("-" * 70)
    cursor.execute("SELECT * FROM artworks")
    artworks = cursor.fetchall()
    
    if not artworks:
        print("📭 Belum terdapat karya dalam database")
        print("💡 Upload karya melalui aplikasi web untuk melihat data")
        conn.close()
        return
    
    total_size_bytes = 0
    
    for art in artworks:
        art_id, user_id, title_enc, desc_enc, file_data, file_type, watermark = art
        file_size_bytes = len(file_data) if file_data else 0
        file_size_mb = file_size_bytes / (1024 * 1024)
        total_size_bytes += file_size_bytes
        
        print(f"ID: {art_id}, User ID: {user_id}, Tipe: {file_type}")
        print(f"  Title Enc: {title_enc[:50]}...")
        print(f"  Desc Enc: {desc_enc[:50]}...")
        print(f"  File Size: {file_size_bytes:,} bytes ({file_size_mb:.2f} MB)")
        if watermark:
            print(f"  Watermark: {watermark[:50]}...")
        print()
    
    # Summary
    total_size_mb = total_size_bytes / (1024 * 1024)
    print(f"📊 TOTAL SEMUA FILE: {total_size_bytes:,} bytes ({total_size_mb:.2f} MB)")
    print(f"📈 TOTAL ARTWORKS: {len(artworks)}")
    
    conn.close()



def download_encrypted_files(output_dir="encrypted_files_export", username=None, password=None):
    """Download file terenkripsi untuk user tertentu setelah validasi username/password."""
    conn = sqlite3.connect('artcrypt.db')
    cursor = conn.cursor()

    # Ensure users exist
    cursor.execute("SELECT id, username_encrypted, password_encrypted FROM users")
    users = cursor.fetchall()

    if not users:
        print("📭 Belum terdapat user terdaftar")
        print("💡 Register user melalui aplikasi web terlebih dahulu")
        conn.close()
        return

    # If credentials not provided, prompt interactively
    if username is None:
        username = input("Masukkan username yang akan didownload: ").strip()
    if password is None:
        password = input("Masukkan password untuk user tersebut: ").strip()

    # Validate credentials using verify_user from crypto_utils
    user_id = verify_user(username, password, users)
    if not user_id:
        print("❌ Username atau password tidak valid. Proses download dibatalkan.")
        conn.close()
        return

    # Create output directory (user-scoped)
    user_output_dir = os.path.join(output_dir, f"user_{user_id}")
    if not os.path.exists(user_output_dir):
        os.makedirs(user_output_dir)

    print(f"\n📥 DOWNLOADING ENCRYPTED FILES FOR USER ID {user_id} TO {user_output_dir}/...")

    cursor.execute("SELECT * FROM artworks WHERE user_id = ?", (user_id,))
    artworks = cursor.fetchall()

    if not artworks:
        print("📭 Belum terdapat karya untuk user ini")
        print("💡 Upload karya melalui aplikasi web terlebih dahulu")
        conn.close()
        return

    downloaded_count = 0
    total_size = 0

    for art in artworks:
        art_id, user_id, title_enc, desc_enc, file_data, file_type, watermark = art

        if not file_data:
            continue

        # Save encrypted file (Base64 decode if needed)
        file_ext = file_type.split('/')[-1] if '/' in file_type else 'unknown'
        filename = f"encrypted_file_{art_id}_user_{user_id}.{file_ext}"
        filepath = os.path.join(user_output_dir, filename)

        try:
            if isinstance(file_data, (bytes, bytearray)):
                with open(filepath, 'wb') as f:
                    f.write(file_data)
            else:
                with open(filepath, 'wb') as f:
                    f.write(base64.b64decode(file_data))
        except Exception as e:
            print(f"⚠️  Gagal menulis file {filename}: {e}")
            continue

        file_size = os.path.getsize(filepath)
        total_size += file_size
        downloaded_count += 1

        print(f"📁 {filename} - {file_size:,} bytes")

        # Save metadata file
        metadata_filename = f"metadata_{art_id}.txt"
        metadata_filepath = os.path.join(user_output_dir, metadata_filename)

        with open(metadata_filepath, 'w', encoding='utf-8') as f:
            f.write(f"Artwork ID: {art_id}\n")
            f.write(f"User ID: {user_id}\n")
            f.write(f"File Type: {file_type}\n")
            f.write(f"Title (Encrypted Base64): {title_enc}\n")
            f.write(f"Description (Encrypted Base64): {desc_enc}\n")
            if watermark:
                f.write(f"Watermark (Encrypted Base64): {watermark}\n")
            else:
                f.write("Watermark: None\n")
            f.write(f"File Size: {file_size:,} bytes ({file_size/(1024*1024):.2f} MB)\n")

    print(f"\n✅ Download completed!")
    print(f"📊 {downloaded_count} files downloaded")
    print(f"📁 Total size: {total_size:,} bytes ({total_size/(1024*1024):.2f} MB)")
    print(f"📂 Location: {os.path.abspath(user_output_dir)}")

    conn.close()



def main_menu():
    """Menu utama untuk script view encrypted data"""
    while True:
        print("\n🔐 ARTCRYPT ENCRYPTED DATA VIEWER")
        print("=" * 50)
        print("1. 👀 View encrypted data")
        print("2.  Download encrypted files (requires username/password)")
        print("3. 🚪 Exit")

        choice = input("\nPilih menu (1-3): ").strip()

        if choice == "1":
            view_encrypted_data()
        elif choice == "2":
            dirname = input("Nama folder output (default: encrypted_files_export): ").strip()
            if not dirname:
                dirname = "encrypted_files_export"
            # Ask credentials for which user's encrypted files to download
            username = input("Masukkan username: ").strip()
            password = input("Masukkan password: ").strip()
            download_encrypted_files(dirname, username, password)
        elif choice == "3":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Pilihan tidak valid!")

if __name__ == "__main__":
    main_menu()