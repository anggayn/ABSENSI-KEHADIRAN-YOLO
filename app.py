# Import Library Utama
import argparse
import cv2  # type: ignore
import numpy as np  # type: ignore

# Import Library Flask dan Modul Terkait
from flask import Flask, jsonify , render_template, request, redirect, url_for, Response, session,  make_response,  send_file, send_from_directory, current_app
from werkzeug.utils import secure_filename  # type: ignore

# Import Library untuk Operasi Sistem dan Manipulasi String
import os
import re

# Import Library untuk Pengolahan Data
import pandas as pd
from io import BytesIO

# Import Library untuk Pembuatan PDF
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors as tbl_colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfgen import canvas

# Import Library untuk Pengiriman Email
from flask_mail import Mail, Message

# Import Library untuk Operasi Keamanan
import random
import string
from werkzeug.security import generate_password_hash
import uuid

# Import Library untuk Threading dan Operasi Waktu
import threading
import time
from datetime import datetime, timedelta

# Import Library untuk Operasi File Sistem
import shutil
from flask import jsonify

# Import Library untuk Model YOLO
from ultralytics import YOLO  # type: ignore

# Import Library untuk Operasi Database
from db import (
    create_log_table,
    create_user_table, 
    add_category_column, 
    fetch_logs,
    clear_logs, 
    delete_log_by_id,
    register_user,
    verify_user, 
    insert_log, 
    is_username_exist, 
    is_email_exist, 
    is_valid_password, 
    get_db_connection,
)

app = Flask(__name__)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'akunsecret2112@gmail.com'
app.config['MAIL_PASSWORD'] = 'svdwzyykicgmwsnr'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.secret_key = 'your_secret_key'
mail = Mail(app)


def send_email(to, subject, body):
    # Ubah nama pengirim menjadi "Absensi Kehadiran"
    msg = Message(subject, sender=("Absensi Kehadiran", app.config['MAIL_USERNAME']), recipients=[to])
    msg.body = body
    mail.send(msg)

def generate_random_code(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.secret_key = 'your_secret_key'
create_log_table()
create_user_table()
add_category_column()

# Path untuk model YOLO
model_path = 'dataset1.pt'

# Coba untuk load model YOLO
try:
    model = YOLO(model_path)
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
    raise

# Fungsi untuk menghasilkan nama file unik
def generate_unique_filename(extension):
    return f"{uuid.uuid4()}.{extension}"

# Warna yang akan digunakan untuk bounding box setiap kelas
colors = {
0: (0, 0, 255), 
1: (0, 255, 0), 


}

# Nama kelas yang akan digunakan untuk deteksi
class_names = {
0: "angga",
1: "manca",



}

# Fungsi untuk menambahkan kotak deteksi dan label ke gambar
def custom_plot(results, detected_persons, thickness=2, font_scale=1.0):
    img = results[0].orig_img  # Ambil gambar asli
    for box in results[0].boxes:  # Loop melalui setiap kotak deteksi
        cls = int(box.cls[0])  # Ambil kelas deteksi
        color = colors.get(cls, (255, 255, 255))  # Ambil warna untuk kelas
        confidence = box.conf[0]  # Confidence score
        label = f"{class_names[cls]} {confidence:.2f}"  # Label dengan nama kelas dan confidence score

        if confidence < 0.4:  # Hanya tampilkan jika confidence score cukup tinggi
            continue
        
        detection_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())  # Waktu deteksi saat ini

        # Buat kotak pada gambar
        cv2.rectangle(
            img,
            (int(box.xyxy[0][0]), int(box.xyxy[0][1])),
            (int(box.xyxy[0][2]), int(box.xyxy[0][3])),
            color,
            thickness  # Tetap sama tebal, tidak berubah dengan jarak
        )
        # Tambahkan label nama dan confidence score
        cv2.putText(
            img,
            label,
            (int(box.xyxy[0][0]), int(box.xyxy[0][1]) - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,  # Ukuran font tetap
            color,
            thickness  # Ketebalan teks tetap
        )
        # Tambahkan waktu deteksi di bawah kotak
        cv2.putText(
            img,
            detection_time,
            (int(box.xyxy[0][0]), int(box.xyxy[0][3]) + 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale * 0.8,  # Waktu sedikit lebih kecil
            color,
            thickness  # Ketebalan teks tetap
        )

    return img



# Fungsi untuk menentukan kategori berdasarkan nama
def get_category(person_name):
    if person_name in {"manca"}:
        return "Dosen"
    else:
        return "Mahasiswa"



@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username").lower()  # Normalisasi username ke huruf kecil
        password = request.form.get("password")

        if username == "admin":
            if password == "admin123":
                session["user"] = "admin"
                session["role"] = "admin"
                response = make_response(redirect(url_for("admin_dashboard")))
                response.set_cookie("username", "admin")
                response.set_cookie("user_id", "1")
                response.set_cookie("role", "admin")
                return response
            else:
                return render_template('loginregister.html', error="admin_password_wrong")
        else:
            if not is_username_exist(username):
                return render_template('loginregister.html', error="user_username_wrong")

            user_id = verify_user(username, password)
            if user_id:
                session["user"] = username
                session["role"] = "user"
                response = make_response(redirect(url_for("user_dashboard")))
                response.set_cookie("username", username)
                response.set_cookie("user_id", str(user_id))
                response.set_cookie("role", "user")
                return response
            else:
                return render_template('loginregister.html', error="user_password_wrong")

    return render_template('loginregister.html')




def is_valid_password(password):
    if len(password) < 8:
        return False
    if not re.search(r"\d", password):  # Harus mengandung angka
        return False
    if not re.search(r"[a-zA-Z]", password):  # Harus mengandung huruf
        return False
    return True

@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    whatsapp = request.form.get("whatsapp")
    password = request.form.get("password")
    email = request.form.get("email")

    if not username or not whatsapp or not password or not email:
        return {"success": False, "message": "All fields are required."}, 400

    if not re.match(r"^\+?\d+$", whatsapp):
        return {"success": False, "message": "Invalid WhatsApp number format."}, 400

    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return {"success": False, "message": "Invalid email format."}, 400

    if not is_valid_password(password):
        return {
            "success": False,
            "message": "Password must be at least 8 characters long and include both letters and numbers."
        }, 400

    if is_email_exist(email):
        return {"success": False, "message": "Email already registered."}, 400

    if register_user(username, whatsapp, password, email):
        return {"success": True, "message": "Registration successful."}
    
    return {"success": False, "message": "Registration failed. Username or WhatsApp number may already exist."}, 400




@app.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json()
    email = data.get("email")

    if not is_email_exist(email):
        return {"success": False, "message": "Email not found."}, 400

    reset_code = generate_random_code()
    conn = get_db_connection()
    conn.execute('UPDATE users SET reset_code = ? WHERE email = ?', (reset_code, email))
    conn.commit()
    conn.close()

    send_email(email, "Your Password Reset Code", f"Your reset code is: {reset_code}")
    return {"success": True, "message": "Reset link sent to your email."}

@app.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json()
    verification_code = data.get('verification_code')
    new_password = data.get('new_password')

    if not verification_code or not new_password:
        return jsonify({'success': False, 'message': 'Invalid input'}), 400

    if not is_valid_password(new_password):
        return jsonify({'success': False, 'message': 'Password must be at least 8 characters and include both letters and numbers.'}), 400

    # Cek kode verifikasi
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE reset_code = ?', (verification_code,)).fetchone()

    if not user:
        conn.close()
        return jsonify({'success': False, 'message': 'Invalid or expired verification code.'}), 400

    # Hash password baru dan update database
    hashed_password = generate_password_hash(new_password)
    conn.execute('UPDATE users SET password = ?, reset_code = NULL WHERE reset_code = ?', (hashed_password, verification_code))
    conn.commit()
    conn.close()

    # Bersihkan session dan cookies setelah reset
    response = make_response(redirect(url_for("login")))
    response.delete_cookie("username")
    response.delete_cookie("user_id")
    response.delete_cookie("role")
    return jsonify({'success': True, 'message': 'Password has been reset successfully.'})


    
@app.route("/admin_dashboard")
def admin_dashboard():
    if "user" in session and session["user"] == "admin":
        logs = fetch_logs()  # No user filter for admin
        return render_template("admin_dashboard.html", logs=logs)
    return redirect(url_for("login"))



@app.route('/user_dashboard')
def user_dashboard():
    if "user" in session and session["user"] != "admin":
        username = session["user"].lower()  # Normalisasi username ke huruf kecil

        # Ambil log berdasarkan username yang dinormalisasi
        logs = fetch_logs(user=username)

        # Jika tidak ada log, tetap tampilkan halaman dashboard dengan pesan
        if not logs:
            return render_template("user_dashboard.html", logs=[], message="Belum ada data absensi.")

        # Jika ada log, pastikan nama cocok dengan username
        if all(log["person_name"].lower() == username for log in logs):
            return render_template("user_dashboard.html", logs=logs)

        # Jika tidak cocok, arahkan kembali ke login
        return render_template("loginregister.html", error="access_denied")

    # Jika sesi tidak valid, arahkan ke halaman login
    return redirect(url_for("login"))




@app.route('/logout')
def logout():
    # Periksa apakah pengguna sudah login
    if 'user' in session:
        username = session.get('user')  # Ambil username dari session
        role = session.get('role', 'user')  # Ambil role dari session (default 'user')
        user_id = request.cookies.get('user_id')  # Ambil user_id dari cookies jika ada

        # Hapus data sesi
        session.clear()  # Menghapus semua data dari sesi

        # Buat respons untuk logout
        response = make_response(redirect(url_for('login')))

        # Hapus semua cookies terkait
        response.delete_cookie('username')
        response.delete_cookie('user_id')
        response.delete_cookie('role')
        response.delete_cookie('session')  # Jika Anda menggunakan cookie 'session' tambahan

        # Log untuk debugging
        if role == 'admin':
            print(f"Admin with ID {user_id} logged out")
        else:
            print(f"User {username} with ID {user_id} logged out")

        return response

    # Jika user belum login, langsung arahkan ke halaman login
    return redirect(url_for('login'))



@app.route('/upload_user.html', methods=['GET', 'POST'])
def upload_photo():
    if 'user' not in session or session.get('role') != 'user':
        # Jika user belum login atau role bukan 'user', arahkan kembali ke halaman login
        return redirect(url_for('login'))
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            if not name:
                return jsonify(success=False, message="Nama tidak boleh kosong")

            photos = request.files.getlist('photos')
            if not photos:
                return jsonify(success=False, message="Tidak ada foto yang dipilih")

            user_folder = os.path.join('static/uploads', secure_filename(name))
            os.makedirs(user_folder, exist_ok=True)

            for photo in photos:
                if photo and allowed_file(photo.filename):
                    filename = secure_filename(photo.filename)
                    file_path = os.path.join(user_folder, filename)
                    photo.save(file_path)
                else:
                    return jsonify(success=False, 
                                  message="Format file tidak didukung. Gunakan format PNG, JPG, atau JPEG")

            return jsonify(success=True, 
                          message="Foto berhasil diunggah")

        except Exception as e:
            return jsonify(success=False, 
                          message=f"Terjadi kesalahan: {str(e)}")

    # Ambil daftar folder di 'static/uploads'
    folder_list = os.listdir('static/uploads')
    return render_template('upload_user.html', folders=folder_list)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/dataset', methods=['GET'])
def dataset():
    if 'user' not in session or session.get('role') != 'admin':
        # Jika user belum login atau role bukan 'user', arahkan kembali ke halaman login
        return redirect(url_for('login'))
    try:
        base_path = 'static/uploads'
        folders = []
        if os.path.exists(base_path):
            folders = [folder for folder in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, folder))]
        
        return render_template('dataset.html', folders=folders)
    except Exception as e:
        return f"Terjadi kesalahan: {str(e)}"


@app.route('/dataset/<folder_name>', methods=['GET'])
def view_folder(folder_name):
    folder_path = os.path.join('static/uploads', folder_name)
    app.logger.debug(f"Mencoba membaca folder di: {folder_path}")
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        files = os.listdir(folder_path)
        app.logger.debug(f"Isi folder: {files}")
        files = [f for f in files if os.path.isfile(os.path.join(folder_path, f))]
        return render_template('folder_contents.html', folder_name=folder_name, files=files)
    else:
        app.logger.debug("Folder tidak ditemukan atau kosong.")
        return f"Folder {folder_name} tidak ditemukan.", 404
    


@app.route('/download_folder/<folder_name>', methods=['GET'])
def download_folder(folder_name):
    try:
        folder_path = os.path.join('static/uploads', folder_name)
        
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            # Create a zip file of the folder for download
            zip_filename = f'{folder_name}.zip'
            zip_path = os.path.join('static', zip_filename)
            
            # Make the archive and save it in static folder
            shutil.make_archive(zip_path.replace('.zip', ''), 'zip', folder_path)
            
            # Return the zip file as attachment
            return send_file(zip_path, as_attachment=True)
        
        return "Folder not found.", 404
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

@app.route('/delete_folder/<folder_name>', methods=['DELETE'])
def delete_folder(folder_name):
    
    try:
        folder_path = os.path.join('static/uploads', folder_name)
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            shutil.rmtree(folder_path)  # Remove the folder and its contents
            return jsonify(success=True, message="Folder deleted successfully.")
        return jsonify(success=False, message="Folder not found."), 404
    except Exception as e:
        return jsonify(success=False, message=f"An error occurred: {str(e)}"), 500
    
@app.route('/delete_all_folders', methods=['DELETE'])
def delete_all_folders():
    try:
        base_path = 'static/uploads'
        if os.path.exists(base_path) and os.path.isdir(base_path):
            # Loop through all folders in the 'static/uploads' directory
            folders = [folder for folder in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, folder))]
            for folder in folders:
                folder_path = os.path.join(base_path, folder)
                shutil.rmtree(folder_path)  # Delete the folder and its contents
            return jsonify(success=True, message="All folders deleted successfully.")
        return jsonify(success=False, message="No folders found."), 404
    except Exception as e:
        return jsonify(success=False, message=f"An error occurred: {str(e)}"), 500

 
    
# Route untuk menghapus semua log
@app.route("/clear_logs", methods=["POST"])
def clear_logs_route():
    month = request.form.get("month")
    year = request.form.get("year")
    category = request.form.get("category")
    clear_logs(month, year, category)  # Pass month, year, and category to the function
    return redirect(url_for('admin_dashboard'))


@app.route('/download/excel', methods=['GET'])
def download_excel():
    month = request.args.get('month')
    year = request.args.get('year')
    category = request.args.get('category')

    # Validasi parameter
    if not month or not year or not category:
        return "Parameter bulan, tahun, dan kategori harus disediakan.", 400

    # Fetch logs berdasarkan filter
    filtered_logs = fetch_logs(month=month, year=year, category=category)

    if not filtered_logs:
        return "Tidak ada data untuk filter yang diberikan.", 404

    # Create a list of dictionaries
    data = [
        {
            'No.': index + 1,
            'Waktu': log['timestamp'],
            'Nama': log['person_name'],
            'Kategori': log['category'],
            'Bukti Gambar': log['file_path'],
        }
        for index, log in enumerate(filtered_logs)
    ]

    df = pd.DataFrame(data, columns=['No.', 'Waktu', 'Nama', 'Kategori', 'Bukti Gambar'])

    output = BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)

    filename = f"Absensi_Kehadiran_{category}_{month}_{year}.xlsx"
    return send_file(output, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')



@app.route('/download/pdf', methods=['GET'])
def download_pdf():
    month = request.args.get('month')
    year = request.args.get('year')
    category = request.args.get('category')

    # Validasi parameter
    if not month or not year or not category:
        return "Parameter bulan, tahun, dan kategori harus disediakan.", 400

    # Fetch logs berdasarkan filter
    filtered_logs = fetch_logs(month=month, year=year, category=category)

    if not filtered_logs:
        return "Tidak ada data untuk filter yang diberikan.", 404

    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter)

    styles = getSampleStyleSheet()
    centered_title_style = ParagraphStyle(
        name="CenteredTitle",
        parent=styles["Heading1"],
        alignment=TA_CENTER,
        fontSize=16,
        spaceAfter=12,
    )

    title_text = f"Absensi Kehadiran Report for {category} {month}/{year}"
    title = Paragraph(title_text, centered_title_style)

    header = ["No.", "Waktu", "Nama", "Kategori", "Bukti Gambar"]
    table_data = [header]

    for index, log in enumerate(filtered_logs):
        image_path = os.path.join(current_app.root_path, 'static', log['file_path'])

        if os.path.exists(image_path):
            try:
                img = Image(image_path, width=50, height=50)
            except Exception:
                img = "Error loading image"
        else:
            img = "Image not found"

        table_data.append([
            index + 1,
            log['timestamp'],
            log['person_name'],
            log['category'],
            img
        ])

    # Create the table
    table = Table(table_data, colWidths=[40, 120, 100, 80, 100])  # Adjust column widths as needed

    # Style the table
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), tbl_colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), tbl_colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, tbl_colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])
    table.setStyle(style)

    # Build the PDF
    elements = []
    elements.append(title)
    elements.append(Spacer(1, 12))  # Add space below the title
    elements.append(table)

    doc.build(elements)

    output.seek(0)
    # Create filename with month, year, and category
    filename = f"Absensi_Kehadiran_{category}_{month}_{year}.pdf"
    return send_file(output, as_attachment=True, download_name=filename, mimetype='application/pdf')


# Route untuk menghapus log berdasarkan ID
@app.route("/delete_log", methods=["POST"])
def delete_log():
    log_id = request.form.get("log_id")  # Ambil ID log dari form
    if log_id:
        delete_log_by_id(log_id)  # Hapus log berdasarkan ID
        return redirect(url_for("admin_dashboard"))
    return "Log ID tidak ditemukan", 400

# Route untuk menampilkan halaman stream video
@app.route("/stream")
def stream():
    if 'user' not in session or session.get('role') != 'admin':
        # Jika user belum login atau role bukan 'user', arahkan kembali ke halaman login
        return redirect(url_for('login'))
    return render_template('stream.html')

@app.route('/static/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('static/images', filename)



# Variabel global
rtsp_url = 'rtsp://admin:admin@10.3.1.41:8554/Streaming/Channels/102'
cap = cv2.VideoCapture(rtsp_url)
frame_lock = threading.Lock()
latest_frame = None

attendance_log_today = {}  # Menyimpan log kehadiran harian
last_logged_time = {}  # Menyimpan waktu terakhir seseorang masuk log
reset_time = datetime.combine(datetime.now().date(), datetime.min.time()) + timedelta(days=1)  # Reset pada tengah malam

def reset_attendance_log():
    """Reset log kehadiran harian."""
    global attendance_log_today, last_logged_time, reset_time
    attendance_log_today = {}
    last_logged_time = {}
    reset_time = datetime.combine(datetime.now().date(), datetime.min.time()) + timedelta(days=1)

def frame_grabber():
    """Thread untuk terus mengambil frame dari kamera."""
    global latest_frame
    while True:
        success, frame = cap.read()
        if not success:
            continue

        with frame_lock:
            latest_frame = frame

def generate_frames():
    """Menghasilkan frame yang diolah untuk streaming."""
    global latest_frame
    detection_start_times = {}  # Menyimpan waktu mulai deteksi untuk setiap orang

    while True:
        # Reset log jika waktu saat ini melewati reset_time
        if datetime.now() >= reset_time:
            reset_attendance_log()

        with frame_lock:
            if latest_frame is None:
                continue
            frame = latest_frame.copy()

        # Ukuran frame diperkecil untuk pemrosesan lebih cepat
        resized_frame = cv2.resize(frame, (640, 360))

        # Deteksi objek menggunakan YOLO
        results = model(resized_frame)  # Prediksi frame menggunakan YOLO
        detected_persons = set()
        frame_with_boxes = custom_plot(results, detected_persons)  # Tambahkan kotak dan label ke frame

        # Logika untuk deteksi dan pencatatan
        if len(results[0].boxes) > 0:
            detected_classes = {int(box.cls[0]) for box in results[0].boxes if box.conf[0] >= 0.7}
            current_time = time.time()

            for cls_index in detected_classes:
                person_name = class_names.get(cls_index, "Unknown")  # Ambil nama orang
                category = get_category(person_name)
                current_date = datetime.now().date()

                # Periksa apakah orang sudah ada di log kehadiran hari ini
                if person_name not in attendance_log_today:
                    if person_name not in detection_start_times:  # Orang belum mulai terdeteksi
                        detection_start_times[person_name] = current_time
                    elif current_time - detection_start_times[person_name] >= 10:  # Terdeteksi selama 10 detik
                        image_filename = generate_unique_filename("jpg")  # Buat nama file gambar
                        image_path = os.path.join('static', 'images', image_filename)
                        cv2.imwrite(image_path, frame_with_boxes)  # Simpan gambar hasil

                        detected_persons.add(person_name)  # Tambahkan ke daftar orang terdeteksi
                        insert_log(f'images/{image_filename}', person_name, category)  # Simpan log dengan kategori

                        attendance_log_today[person_name] = current_date  # Tambahkan ke log harian
                        last_logged_time[person_name] = current_time  # Simpan waktu log terakhir
                        del detection_start_times[person_name]  # Hapus dari waktu deteksi
                else:
                    # Jika orang sudah terlog hari ini, hapus dari waktu deteksi
                    if person_name in detection_start_times:
                        del detection_start_times[person_name]

        # Konversi frame ke format JPEG untuk streaming
        ret, buffer = cv2.imencode('.jpg', frame_with_boxes)
        if not ret:
            continue

        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# Mulai thread untuk mengambil frame dari kamera
thread = threading.Thread(target=frame_grabber, daemon=True)
thread.start()


@app.route('/video_feed')
def video_feed():
    """Route untuk streaming video."""
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Jika script dijalankan secara langsung
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5000, help='Port untuk menjalankan aplikasi')
    args = parser.parse_args()

    app.run(host='0.0.0.0', port=args.port, debug=True)
