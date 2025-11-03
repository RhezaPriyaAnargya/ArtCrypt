import sqlite3

def create_connection():
    return sqlite3.connect('artcrypt.db', check_same_thread=False)

def init_db():
    conn = create_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username_encrypted TEXT UNIQUE,
            password_encrypted TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS artworks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title_encrypted TEXT,
            description_encrypted TEXT,
            file_data BLOB,
            file_type TEXT,
            watermark_data TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()