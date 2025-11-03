import streamlit as st
import sqlite3
from connection import create_connection, init_db
from crypto_utils import *

# Initialize database
init_db()

st.set_page_config(page_title="ArtCrypt", page_icon="🎨")
st.title("🎨 ArtCrypt - Platform Kriptografi Karya Digital")

# Session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None

def main():
    """Main application function"""
    
    # Authentication section
    if not st.session_state.user_id:
        show_auth_section()
    else:
        show_dashboard()

def show_auth_section():
    """Show authentication section (login/register)"""
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
    
    with tab1:
        st.header("Login ke ArtCrypt")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("🚀 Login")
            
            if login_btn:
                if username and password:
                    conn = create_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT id, username_encrypted, password_encrypted FROM users")
                    user_id = verify_user(username, password, cursor.fetchall())
                    conn.close()
                    
                    if user_id:
                        st.session_state.user_id = user_id
                        st.session_state.username = username
                        st.success("🎉 Login berhasil!")
                        st.rerun()
                    else:
                        st.error("❌ Username atau password salah!")
                else:
                    st.warning("⚠️ Harap isi semua field!")
    
    with tab2:
        st.header("Daftar Akun Baru")
        with st.form("register_form"):
            new_user = st.text_input("Username Baru")
            new_pass = st.text_input("Password Baru", type="password")
            confirm_pass = st.text_input("Konfirmasi Password", type="password")
            register_btn = st.form_submit_button("✨ Daftar")
            
            if register_btn:
                if new_user and new_pass and confirm_pass:
                    if new_pass == confirm_pass:
                        conn = create_connection()
                        cursor = conn.cursor()
                        try:
                            user_enc = encrypt_username(new_user)
                            pass_enc = encrypt_password(new_pass)
                            cursor.execute("INSERT INTO users (username_encrypted, password_encrypted) VALUES (?, ?)", 
                                         (user_enc, pass_enc))
                            conn.commit()
                            st.success("✅ Registrasi berhasil! Silakan login.")
                        except sqlite3.IntegrityError:
                            st.error("❌ Username sudah ada!")
                        finally:
                            conn.close()
                    else:
                        st.error("❌ Password tidak cocok!")
                else:
                    st.warning("⚠️ Harap isi semua field!")

def show_dashboard():
    """Show main dashboard after login"""
    st.sidebar.success(f"👋 Welcome, **{st.session_state.username}**!")
    
    # Navigation - TAMBAH MENU VERIFIKASI
    menu = st.sidebar.radio("📋 Navigasi", [
        "🏠 Dashboard", 
        "📤 Upload Karya", 
        "🖼️ Galeri Karya",
        "🔍 Verifikasi Karya"
    ])
    
    if menu == "🏠 Dashboard":
        show_home_dashboard()
    elif menu == "📤 Upload Karya":
        show_upload_section()
    elif menu == "🖼️ Galeri Karya":
        show_gallery_section()
    elif menu == "🔍 Verifikasi Karya":
        show_verification_section()
    
    # Logout button
    if st.sidebar.button("🚪 Logout"):
        st.session_state.user_id = None
        st.session_state.username = None
        st.rerun()

def show_home_dashboard():
    """Show home dashboard"""
    st.header("🏠 Dashboard Overview")
    
    conn = create_connection()
    cursor = conn.cursor()
    
    # Get user artworks count
    cursor.execute("SELECT COUNT(*) FROM artworks WHERE user_id = ?", (st.session_state.user_id,))
    artworks_count = cursor.fetchone()[0]
    
    # Get total file size
    cursor.execute("SELECT file_data FROM artworks WHERE user_id = ?", (st.session_state.user_id,))
    artworks = cursor.fetchall()
    total_size = sum(len(art[0]) for art in artworks if art[0])
    total_size_mb = total_size / (1024 * 1024)
    
    # Get images with watermark count
    cursor.execute("SELECT COUNT(*) FROM artworks WHERE user_id = ? AND file_type LIKE 'image%' AND watermark_data IS NOT NULL", 
                   (st.session_state.user_id,))
    watermarked_count = cursor.fetchone()[0]
    
    conn.close()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.info("📊 Total Karya")
        st.metric("Jumlah Karya", artworks_count)
    
    with col2:
        st.info("🔐 Keamanan")
        st.metric("Level Enkripsi", "Multi-Layer")
    
    with col3:
        st.info("💾 Penyimpanan")
        st.metric("Total Ukuran", f"{total_size_mb:.2f} MB")
    
    with col4:
        st.info("💧 Watermark")
        st.metric("Gambar Terwatermark", watermarked_count)
    
    st.markdown("---")
    st.subheader("ℹ️ Tentang ArtCrypt")
    st.write("""
    ArtCrypt adalah platform untuk melindungi karya digital Anda dengan enkripsi multi-layer:
    - 🔐 **Login/Register**: Camellia CBC + HMAC-SHA384
    - 📝 **Metadata**: Caesar Cipher + AES-128-GCM + Camellia CBC  
    - 📁 **File**: Salsa20 + Camellia CBC
    - 🖼️ **Gambar**: Bit Plane Slicing Watermark
    - 🔍 **Verifikasi**: Bandingkan karya asli dengan yang diduga palsu
    """)

def show_upload_section():
    """Show artwork upload section"""
    st.header("📤 Upload Karya Baru")
    
    with st.form("upload_form"):
        title = st.text_input("🎨 Judul Karya")
        description = st.text_area("📝 Deskripsi", height=100)
        file = st.file_uploader("📁 Pilih File", 
                              type=['pdf', 'docx', 'jpg', 'jpeg', 'png', 'gif', 'mp3', 'wav'])
        
        submitted = st.form_submit_button("🚀 Upload Karya")
        
        if submitted:
            if title and file:
                conn = create_connection()
                cursor = conn.cursor()
                
                try:
                    # Encrypt metadata
                    title_enc = encrypt_metadata(title)
                    desc_enc = encrypt_metadata(description)
                    
                    # Process file
                    file_data = file.getvalue()
                    file_enc = encrypt_file(file_data)
                    
                    # Watermark for images
                    watermark = None
                    if file.type.startswith('image'):
                        watermark_text = f"ArtCrypt-{st.session_state.user_id}-{title}"
                        watermarked_bytes = embed_watermark(file, watermark_text)
                        
                        # Re-encrypt the watermarked image
                        file_enc = encrypt_file(watermarked_bytes)
                        
                        # Encrypt watermark metadata
                        watermark = encrypt_metadata(watermark_text)
                    
                    # Save to database
                    cursor.execute('''
                        INSERT INTO artworks (user_id, title_encrypted, description_encrypted, 
                                            file_data, file_type, watermark_data)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (st.session_state.user_id, title_enc, desc_enc, file_enc, file.type, watermark))
                    
                    conn.commit()
                    st.success("✅ Karya berhasil diupload!")
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                finally:
                    conn.close()
            else:
                st.warning("⚠️ Harap isi judul dan pilih file!")

def show_gallery_section():
    """Show artwork gallery"""
    st.header("🖼️ Galeri Karya Saya")
    
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, title_encrypted, description_encrypted, file_data, file_type, watermark_data
        FROM artworks WHERE user_id = ? ORDER BY id DESC
    ''', (st.session_state.user_id,))
    
    artworks = cursor.fetchall()
    
    if not artworks:
        st.info("📝 Belum ada karya yang diupload. Mulai upload karya pertama Anda!")
    else:
        for art_id, title_enc, desc_enc, file_data, file_type, watermark in artworks:
            try:
                # Decrypt metadata
                title = decrypt_metadata(title_enc)
                description = decrypt_metadata(desc_enc)
                
                # Decrypt file
                file_decrypted = decrypt_file(file_data)
                
                with st.expander(f"🎨 {title}", expanded=False):
                    st.write(f"**📝 Deskripsi:** {description}")
                    st.write(f"**📄 Tipe File:** {file_type}")
                    
                    # File display section
                    if file_type.startswith('image'):
                        # Tampilkan gambar
                        st.image(file_decrypted, use_container_width=True)
                        
                        # Watermark verification untuk gambar
                        if watermark:
                            wm_text = decrypt_metadata(watermark)
                            extracted_wm = extract_watermark_from_bytes(file_decrypted)
                            
                            st.write("---")
                            st.subheader("🔍 Verifikasi Watermark")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Watermark Terenkripsi:**")
                                st.code(wm_text)
                            
                            with col2:
                                st.write(f"**Watermark Terekstrak:**")
                                st.code(extracted_wm)
                            
                            # Verifikasi
                            if wm_text == extracted_wm:
                                st.success("✅ **KARYA ASLI** - Watermark valid dan sesuai!")
                            else:
                                st.error("❌ **KARYA TIDAK VALID** - Watermark tidak cocok!")
                                st.warning("⚠️ Kemungkinan karya telah dimodifikasi atau bukan karya asli!")
                    else:
                        # Untuk file non-gambar
                        st.info(f"📁 File {file_type.split('/')[-1].upper()}")
                    
                    # Download button untuk semua file
                    file_extension = file_type.split('/')[-1] if '/' in file_type else 'file'
                    st.download_button(
                        label="📥 Download File",
                        data=file_decrypted,
                        file_name=f"{title}.{file_extension}",
                        mime=file_type,
                        use_container_width=True,
                        key=f"download_{art_id}"
                    )
            
            except Exception as e:
                st.error(f"❌ Error memuat karya ID {art_id}: {str(e)}")
    
    conn.close()

def show_verification_section():
    """NEW: Show artwork verification section"""
    st.header("🔍 Verifikasi Karya")
    st.write("""
    **Fitur ini memungkinkan Anda memverifikasi keaslian karya dengan membandingkan:**
    - Karya asli dari database Anda
    - Karya yang diduga modifikasi/palsu yang Anda upload
    """)
    
    conn = create_connection()
    cursor = conn.cursor()
    
    # Get user's watermarked artworks
    cursor.execute('''
        SELECT id, title_encrypted, watermark_data 
        FROM artworks 
        WHERE user_id = ? AND file_type LIKE 'image%' AND watermark_data IS NOT NULL
        ORDER BY id DESC
    ''', (st.session_state.user_id,))
    
    watermarked_artworks = cursor.fetchall()
    
    if not watermarked_artworks:
        st.warning("""
        ❌ **Tidak ada gambar dengan watermark yang tersedia untuk diverifikasi.**
        
        Untuk menggunakan fitur verifikasi:
        1. Upload gambar terlebih dahulu di menu **📤 Upload Karya**
        2. Pastikan file berformat gambar (JPG, PNG, dll)
        3. Sistem akan otomatis menambahkan watermark
        """)
        conn.close()
        return
    
    # Step 1: Pilih karya asli dari database
    st.subheader("1. Pilih Karya Asli")
    
    # Buat pilihan dropdown
    artwork_options = {}
    for art_id, title_enc, watermark_data in watermarked_artworks:
        try:
            title = decrypt_metadata(title_enc)
            artwork_options[art_id] = title
        except:
            continue
    
    if not artwork_options:
        st.error("❌ Tidak ada karya yang dapat dipilih.")
        conn.close()
        return
    
    selected_artwork_id = st.selectbox(
        "Pilih karya asli dari database:",
        options=list(artwork_options.keys()),
        format_func=lambda x: artwork_options[x]
    )
    
    # Dapatkan data karya yang dipilih
    cursor.execute('''
        SELECT title_encrypted, description_encrypted, file_data, watermark_data
        FROM artworks WHERE id = ?
    ''', (selected_artwork_id,))
    
    original_art = cursor.fetchone()
    
    if not original_art:
        st.error("❌ Karya tidak ditemukan.")
        conn.close()
        return
    
    title_enc, desc_enc, file_data, watermark_data = original_art
    
    # Decrypt data karya asli
    try:
        original_title = decrypt_metadata(title_enc)
        original_description = decrypt_metadata(desc_enc)
        original_image = decrypt_file(file_data)
        original_watermark = decrypt_metadata(watermark_data)
        
        # Tampilkan informasi karya asli
        col1, col2 = st.columns(2)
        with col1:
            st.image(original_image, caption=f"Karya Asli: {original_title}", use_container_width=True)
        with col2:
            st.write(f"**Judul:** {original_title}")
            st.write(f"**Deskripsi:** {original_description}")
            st.write(f"**Watermark Asli:**")
            st.code(original_watermark)
        
    except Exception as e:
        st.error(f"❌ Error memuat karya asli: {str(e)}")
        conn.close()
        return
    
    # Step 2: Upload karya yang diduga modifikasi
    st.subheader("2. Upload Karya yang Diduga Modifikasi")
    
    uploaded_file = st.file_uploader(
        "Pilih file gambar yang ingin diverifikasi:",
        type=['jpg', 'jpeg', 'png', 'gif'],
        key="verification_upload"
    )
    
    if uploaded_file:
        # Process uploaded file
        suspect_image_data = uploaded_file.getvalue()
        suspect_image_name = uploaded_file.name
        
        # Tampilkan gambar yang diupload
        st.image(suspect_image_data, caption=f"Karya yang Diupload: {suspect_image_name}", use_container_width=True)
        
        # Step 3: Verifikasi
        st.subheader("3. Hasil Verifikasi")
        
        if st.button("🔍 Mulai Verifikasi", use_container_width=True):
            with st.spinner("Memproses verifikasi..."):
                try:
                    # Extract watermark dari gambar yang diupload
                    extracted_watermark = extract_watermark_from_bytes(suspect_image_data)
                    
                    # Tampilkan perbandingan
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**💧 Watermark dari Karya Asli:**")
                        st.info(original_watermark)
                    
                    with col2:
                        st.write("**💧 Watermark dari Karya Upload:**")
                        if extracted_watermark:
                            st.info(extracted_watermark)
                        else:
                            st.warning("Tidak ada watermark yang terdeteksi")
                    
                    # Hasil verifikasi
                    st.markdown("---")
                    st.subheader("🎯 **HASIL VERIFIKASI**")
                    
                    if original_watermark == extracted_watermark:
                        st.success("""
                        ✅ **KARYA ASLI TERVERIFIKASI**
                        
                        **Kesimpulan:**
                        - Watermark sesuai dan valid
                        - Karya yang diupload adalah versi asli
                        - File tidak mengalami modifikasi
                        - Keaslian karya terjamin
                        """)
                    else:
                        st.error("""
                        ❌ **KARYA TIDAK VALID TERDETEKSI**
                        
                        **Kemungkinan:**
                        - Karya telah dimodifikasi
                        - Watermark rusak/hilang
                        - Bukan karya asli dari ArtCrypt
                        - File mungkin hasil editan/kompresi
                        """)
                        
                        # Additional analysis
                        st.warning("""
                        ⚠️ **Analisis Tambahan:**
                        - Disarankan untuk tidak menggunakan karya ini
                        - Laporkan jika ini adalah pelanggaran hak cipta
                        - Gunakan hanya karya asli dari database ArtCrypt
                        """)
                
                except Exception as e:
                    st.error(f"❌ Error selama verifikasi: {str(e)}")
    
    conn.close()

if __name__ == "__main__":
    main()