import sqlite3
import base64

def view_encrypted_data():
    conn = sqlite3.connect('artcrypt.db')
    cursor = conn.cursor()
    
    print("🔐 DATA TERENKRIPSI DI DATABASE")
    print("=" * 70)
    
    # Tampilkan tabel users
    print("\n👥 TABEL USERS:")
    print("-" * 70)
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    
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

if __name__ == "__main__":
    view_encrypted_data()