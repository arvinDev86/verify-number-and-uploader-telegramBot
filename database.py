import sqlite3

DB_NAME = "bot_archive.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # جدول کاربران
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                username TEXT,
                phone_number TEXT,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # جدول محتوا (آرشیو)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS archives (
                category TEXT PRIMARY KEY,
                content_data TEXT,
                content_type TEXT
            )
        ''')
        conn.commit()

# --- مدیریت کاربران ---
def add_user(user_id, first_name, username, phone_number):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, first_name, username, phone_number)
            VALUES (?, ?, ?, ?)
        ''', (user_id, first_name, username, phone_number))
        conn.commit()

def get_user(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return cursor.fetchone()

def get_all_users():
    """دریافت لیست تمام کاربران برای ادمین"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT first_name, username, phone_number FROM users')
        return cursor.fetchall()

# --- مدیریت محتوا (پنل ادمین) ---
def add_content(category, content_data, content_type):
    """افزودن یا آپدیت محتوا"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO archives (category, content_data, content_type)
            VALUES (?, ?, ?)
        ''', (category, content_data, content_type))
        conn.commit()

def delete_content(category):
    """حذف یک دسته‌بندی"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM archives WHERE category = ?', (category,))
        conn.commit()

def get_all_content():
    """دریافت تمام محتواها برای ساخت منو"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM archives')
        # تبدیل لیست توپل‌ها به دیکشنری برای دسترسی راحت‌تر
        return {row[0]: {'data': row[1], 'type': row[2]} for row in cursor.fetchall()}