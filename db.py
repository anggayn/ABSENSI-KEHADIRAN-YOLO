import sqlite3
from datetime import datetime
import re
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import os
import base64
from datetime import datetime as dt


# Konfigurasi
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, 'absensiyolo.db')

# Kredensial Ultramsg
ULTRAMSG_INSTANCE_ID = 'instance102723'
ULTRAMSG_API_TOKEN = 'd85nwh1eggpy7weq'

# Pemetaan nama ke nomor WhatsApp
# NAME_TO_WHATSAPP = {
#     'Angga': '+6283830959163',
#     'Surya': '+6281935698267'
# }

def get_db_connection():
    """Membuat koneksi ke database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn



def encode_image_to_base64(file_path):
    """Encode gambar ke dalam format Base64."""
    with open(file_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string

# def send_whatsapp_message(person_name, category, timestamp):
#     """Mengirim pesan WhatsApp dengan teks."""
#     print("Mengirim pesan ke WhatsApp...")

#     recipient_number = NAME_TO_WHATSAPP.get(person_name)
#     if not recipient_number:
#         print(f"Nomor WhatsApp untuk {person_name} tidak ditemukan.")
#         return

#     # Membuat isi pesan
#     message_body = (
#         f"Absensi Kehadiran\n\n"
#         f"Nama: {person_name}\n"
#         f"Kategori: {category}\n"
#         f"Waktu: {timestamp}\n\n"
#         f"Selamat anda telah melakukan absensi kehadiran."
#     )

#     # Kirim pesan teks
#     text_url = f"https://api.ultramsg.com/{ULTRAMSG_INSTANCE_ID}/messages/chat"
#     text_payload = {
#         'token': ULTRAMSG_API_TOKEN,
#         'to': recipient_number,
#         'body': message_body
#     }
#     headers = {'content-type': 'application/x-www-form-urlencoded'}

#     try:
#         text_response = requests.post(text_url, data=text_payload, headers=headers)
#         print(f"Text Response: {text_response.status_code} - {text_response.text}")

#         if text_response.status_code == 200:
#             print("Pesan teks berhasil dikirim.")
#         else:
#             print(f"Error saat mengirim pesan teks: {text_response.status_code} - {text_response.text}")

#     except Exception as e:
#         print(f"Error saat mengirim pesan teks: {str(e)}")


def get_greeting():
    """Mengembalikan ucapan berdasarkan waktu saat ini."""
    current_hour = dt.now().hour
    if 6 <= current_hour < 10:
        return "🌞 Selamat pagi"
    elif 10 <= current_hour < 15:
        return "☀️ Selamat siang"
    elif 15 <= current_hour < 18:
        return "🌅 Selamat sore"
    else:
        return "🌙 Selamat malam"

def send_whatsapp_message(person_name, category, timestamp):
    """Mengirim pesan WhatsApp dengan teks, nomor WhatsApp diambil dari database."""
    print("Mengirim pesan ke WhatsApp...")

    # Ambil nomor WhatsApp dari database berdasarkan nama pengguna
    conn = get_db_connection()
    user = conn.execute('SELECT whatsapp FROM users WHERE username = ?', (person_name,)).fetchone()
    conn.close()

    if not user or not user['whatsapp']:
        print(f"Nomor WhatsApp untuk {person_name} tidak ditemukan di database.")
        return

    recipient_number = user['whatsapp']

    # Membuat isi pesan
    greeting = get_greeting()
    message_body = (
        f"{greeting}\n\n"
        f"Kami ingin memberitahukan bahwa Anda telah berhasil melakukan absensi kehadiran pada hari ini. Berikut adalah detail absensi kehadiran:\n\n"
        f"📌 Nama: {person_name}\n"
        f"📌 Kategori: {category}\n"
        f"📌 Waktu: {timestamp}\n\n"
        f"Terima kasih telah melakukan absensi kehadiran.\n\n"
        f"Semoga aktivitas Anda hari ini berjalan lancar! 😊"
    )
    # Kirim pesan teks
    text_url = f"https://api.ultramsg.com/{ULTRAMSG_INSTANCE_ID}/messages/chat"
    text_payload = {
        'token': ULTRAMSG_API_TOKEN,
        'to': recipient_number,
        'body': message_body
    }
    headers = {'content-type': 'application/x-www-form-urlencoded'}

    try:
        text_response = requests.post(text_url, data=text_payload, headers=headers)
        print(f"Text Response: {text_response.status_code} - {text_response.text}")

        if text_response.status_code == 200:
            print("Pesan teks berhasil dikirim.")
        else:
            print(f"Error saat mengirim pesan teks: {text_response.status_code} - {text_response.text}")

    except Exception as e:
        print(f"Error saat mengirim pesan teks: {str(e)}")


# def send_image(person_name, file_path):
#     """Mengirim gambar sebagai bukti absensi."""
#     recipient_number = NAME_TO_WHATSAPP.get(person_name)
#     if not recipient_number:
#         print(f"Nomor WhatsApp untuk {person_name} tidak ditemukan.")
#         return

#     # Encode gambar ke Base64
#     try:
#         encoded_image = encode_image_to_base64(file_path)
#     except FileNotFoundError:
#         print(f"File tidak ditemukan: {file_path}")
#         return

#     # Kirim pesan gambar
#     image_url = f"https://api.ultramsg.com/{ULTRAMSG_INSTANCE_ID}/messages/image"
#     image_payload = {
#         'token': ULTRAMSG_API_TOKEN,
#         'to': recipient_number,
#         'image': encoded_image,
#         'caption': f"Ini adalah bukti absensi - {person_name}"
#     }

#     try:
#         image_response = requests.post(image_url, data=image_payload)
#         print(f"Image Response: {image_response.status_code} - {image_response.text}")
#         if image_response.status_code == 200:
#             print(f"Gambar berhasil dikirim ke {recipient_number}")
#         else:
#             print(f"Error saat mengirim gambar: {image_response.status_code} - {image_response.text}")
#     except Exception as e:
#         print(f"Error saat mengirim gambar: {str(e)}")

def send_image(person_name, file_path):
    """Mengirim gambar sebagai bukti absensi."""
    conn = get_db_connection()
    user = conn.execute('SELECT whatsapp FROM users WHERE username = ?', (person_name,)).fetchone()
    conn.close()

    if not user or not user['whatsapp']:
        print(f"Nomor WhatsApp untuk {person_name} tidak ditemukan di database.")
        return

    recipient_number = user['whatsapp']

    # Encode gambar ke Base64
    try:
        encoded_image = encode_image_to_base64(file_path)
    except FileNotFoundError:
        print(f"File tidak ditemukan: {file_path}")
        return

    # Kirim pesan gambar
    image_url = f"https://api.ultramsg.com/{ULTRAMSG_INSTANCE_ID}/messages/image"
    image_payload = {
        'token': ULTRAMSG_API_TOKEN,
        'to': recipient_number,
        'image': encoded_image,
        'caption': f"Ini adalah bukti absensi - {person_name}"
    }

    try:
        image_response = requests.post(image_url, data=image_payload)
        print(f"Image Response: {image_response.status_code} - {image_response.text}")
        if image_response.status_code == 200:
            print(f"Gambar berhasil dikirim ke {recipient_number}")
        else:
            print(f"Error saat mengirim gambar: {image_response.status_code} - {image_response.text}")
    except Exception as e:
        print(f"Error saat mengirim gambar: {str(e)}")


def insert_log(file_path, person_name, category):
    """Menambahkan log absensi ke database dan mengirim pesan WhatsApp dengan gambar."""
    print(f"Menambahkan log untuk {person_name}...")
    conn = get_db_connection()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        # Masukkan log ke database
        conn.execute('''
        INSERT INTO logs (timestamp, file_path, person_name, category)
        VALUES (?, ?, ?, ?)
        ''', (timestamp, file_path, person_name, category))
        conn.commit()
        print(f"Log berhasil ditambahkan untuk {person_name} pada {timestamp}")

        # Kirim pesan WhatsApp
        send_whatsapp_message(person_name, category, timestamp)

        # Kirim gambar sebagai bukti
        full_image_path = os.path.join(BASE_DIR, 'static', file_path)  # Jalur lengkap untuk gambar
        send_image(person_name, full_image_path)

    except sqlite3.Error as e:
        print(f"Error menambahkan log ke database: {str(e)}")
    finally:
        conn.close()



def create_log_table():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            file_path TEXT,
            person_name TEXT,
            category TEXT
        )
    ''')
    conn.commit()
    conn.close()

def create_user_table():
    conn = get_db_connection()
    conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        whatsapp TEXT UNIQUE,
        password TEXT
    )
    ''')
    conn.commit()
    conn.close()

def add_reset_code_column():
    conn = get_db_connection()
    try:
        conn.execute('ALTER TABLE users ADD COLUMN reset_code TEXT')
    except sqlite3.OperationalError:
        pass  # Kolom sudah ada
    conn.commit()
    conn.close()

# Pastikan untuk menjalankan fungsi ini di awal
add_reset_code_column()


def add_email_column():
    conn = get_db_connection()
    try:
        conn.execute('ALTER TABLE users ADD COLUMN email TEXT')
    except sqlite3.OperationalError:
        pass  # Kolom sudah ada
    conn.commit()
    conn.close()

# Jalankan fungsi ini di awal aplikasi
add_email_column()




def add_category_column():
    conn = get_db_connection()
    try:
        conn.execute('ALTER TABLE logs ADD COLUMN category TEXT')
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

# def insert_log(file_path, person_name, category):
#     conn = get_db_connection()
#     conn.execute('''
#         INSERT INTO logs (timestamp, file_path, person_name, category)
#         VALUES (?, ?, ?, ?)
#     ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), file_path, person_name, category))
#     conn.commit()
#     conn.close()

def fetch_logs(user=None, month=None, year=None, category=None):
    """Retrieve logs from the database, optionally filtered by user, month, year, and category."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM logs"
    conditions = []
    params = []

    if user:
        conditions.append("LOWER(person_name) = ?")
        params.append(user.lower())

    if month and year:
        conditions.append("strftime('%Y', timestamp) = ? AND strftime('%m', timestamp) = ?")
        params.extend([year, month.zfill(2)])

    if category:
        conditions.append("category = ?")
        params.append(category)

    # Gabungkan kondisi dengan "AND" jika ada
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    cursor.execute(query, params)
    logs = cursor.fetchall()
    conn.close()
    return logs



def clear_logs(month, year, category):
    conn = get_db_connection()
    # Gunakan nama kolom yang benar, seperti `timestamp` di bawah
    conn.execute("DELETE FROM logs WHERE strftime('%m', timestamp) = ? AND strftime('%Y', timestamp) = ? AND category = ?", (month, year, category))
    conn.commit()
    conn.close()



def delete_log_by_id(log_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM logs WHERE id = ?', (log_id,))
    conn.commit()
    conn.close()

def register_user(username, whatsapp, password, email):
    conn = get_db_connection()
    try:
        hashed_password = generate_password_hash(password)
        conn.execute(
            'INSERT INTO users (username, whatsapp, password, email) VALUES (?, ?, ?, ?)',
            (username, whatsapp, hashed_password, email)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()
    return True



def is_username_exist(username):
    """Memeriksa apakah username sudah terdaftar di database."""
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    return user is not None  # Jika user ditemukan, kembalikan True, jika tidak, False


# def verify_user(username, password):
#     conn = get_db_connection()
#     user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
#     conn.close()
#     if user and check_password_hash(user['password'], password):
#         return True
#     return False

def verify_user(username, password):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()

    if user:
        if check_password_hash(user['password'], password):
            return user['id']
    return None


def is_email_exist(email):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    return user is not None

def update_password(email, password):
    conn = get_db_connection()
    try:
        hashed_password = generate_password_hash(password)
        conn.execute('UPDATE users SET password = ? WHERE email = ?', (hashed_password, email))
        conn.commit()
        return True
    except Exception as e:
        print(e)
        return False
    finally:
        conn.close()

def is_valid_password(password):
    if len(password) < 8:
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[a-zA-Z]", password):
        return False
    return True








create_user_table()
add_email_column()