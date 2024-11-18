import argparse
import cv2  # type: ignore
import numpy as np  # type: ignore
from flask import Flask, jsonify , render_template, request, redirect, url_for, Response, session,  make_response,  send_file
 # type: ignore
from werkzeug.utils import secure_filename  # type: ignore
import os
import uuid
import time
import shutil
from flask import jsonify
from ultralytics import YOLO  # type: ignore
from db import create_log_table, create_user_table, add_category_column, fetch_logs, clear_logs, delete_log_by_id, register_user, verify_user, insert_log

app = Flask(__name__)

app.secret_key = 'your_secret_key'
create_log_table()
create_user_table()
add_category_column()

# Path untuk model YOLO
model_path = 'best (2).pt'

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
0: (0, 0, 255), # Merah untuk "Ayunda"
1: (0, 255, 0), # Hijau untuk "Dina"
2: (255, 0, 0), # Biru untuk "Angga"
3: (255, 255, 0), # Cyan untuk "Ardian"

}

# Nama kelas yang akan digunakan untuk deteksi
class_names = {
0: "Ayunda",
1: "Dina",
2: "Angga",
3: "Ardian",

}

# Fungsi untuk menambahkan kotak deteksi dan label ke gambar
def custom_plot(results):
    img = results[0].orig_img  # Ambil gambar asli
    for box in results[0].boxes:  # Loop melalui setiap kotak deteksi
        cls = int(box.cls[0])  # Ambil kelas deteksi
        color = colors.get(cls, (255, 255, 255))  # Ambil warna untuk kelas
        label = f"{class_names[cls]} {box.conf[0]:.2f}"  # Label dengan nama kelas dan confidence score
        detection_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())  # Waktu deteksi saat ini

        cv2.rectangle(img, (int(box.xyxy[0][0]), int(box.xyxy[0][1])),
                      (int(box.xyxy[0][2]), int(box.xyxy[0][3])), color, 2)  # Buat kotak pada gambar
        cv2.putText(img, label, (int(box.xyxy[0][0]), int(box.xyxy[0][1]) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)  # Tambahkan label
        cv2.putText(img, detection_time, (int(box.xyxy[0][0]), int(box.xyxy[0][3]) + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)  # Tambahkan waktu deteksi
        
    return img

# Fungsi untuk menentukan kategori berdasarkan nama
def get_category(person_name):
    if person_name in {"Ayunda", "Ardian"}:
        return "Dosen"
    else:
        return "Mahasiswa"

# @app.route("/", methods=["GET", "POST"])
# def login():
#     if request.method == "POST":
#         username = request.form.get("username")
#         password = request.form.get("password")

#         if username == "admin" and password == "admin123":
#             session["user"] = "admin"
#             return redirect(url_for("admin_dashboard"))
#         elif verify_user(username, password):
#             session["user"] = username
#             return redirect(url_for("user_dashboard"))
#         else:
#             return "Login failed. Please try again.", 401
#     return render_template('loginregister.html')

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Admin credentials check
        if username == "admin" and password == "admin123":
            session["user"] = "admin"
            response = make_response(redirect(url_for("admin_dashboard")))
            response.set_cookie("username", "admin")  # Set cookie for admin
            response.set_cookie("user_id", "1")  
            return response
        
        # For regular user login
        else:
            user_id = verify_user(username, password)
            print(f"User ID returned: {user_id}")  # Debugging output

            if user_id:  
                session["user"] = username
                response = make_response(redirect(url_for("user_dashboard")))
                response.set_cookie("username", username)  # Set cookie for username
                response.set_cookie("user_id", str(user_id))  # Set cookie for user_id (converted to string)
                return response
            else:
                return "Login failed. Please try again.", 401

    return render_template('loginregister.html')



@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")

    # Debugging output
    print(f"Username: {username}, Email: {email}, Password: {password}")

    # Validate input
    if not username or not password or not email:
        return "Registration failed. Username, email, and password are required.", 400

    if register_user(username, email, password):
        return redirect(url_for("login"))
    return "Registration failed. Username may already exist.", 400

@app.route("/admin_dashboard")
def admin_dashboard():
    if "user" in session and session["user"] == "admin":
        logs = fetch_logs()  # Pastikan fetch_logs() didefinisikan untuk mengambil log dari database
        return render_template("admin_dashboard.html", logs=logs)
    return redirect(url_for("login"))


@app.route('/user_dashboard')
def user_dashboard():
    if "user" in session and session["user"] != "admin":
        logs = fetch_logs()
        return render_template("user_dashboard.html", logs=logs)  # Render halaman user_dashboard.html
    return redirect(url_for("login"))


@app.route('/logout')
def logout():
    # Ambil username dan user_id dari cookies
    username = request.cookies.get('username')
    user_id = request.cookies.get('user_id')

    # Cek apakah user sudah login
    if username:
        session.pop('user', None)  # Hapus data user dari session

        # Hapus cookies username dan user_id
        response = make_response(redirect(url_for('login')))
        response.delete_cookie('username')
        response.delete_cookie('user_id')

        # Cek apakah admin atau user berdasarkan username
        if username == 'admin':
            print(f"Admin with ID {user_id} logged out")
        else:
            print(f"User {username} with ID {user_id} logged out")

        return response
    
    return redirect(url_for('login'))


# @app.route('/upload_user.html')
# def capture():
#     return render_template('upload_user.html')

# @app.route('/upload_user.html', methods=['GET', 'POST'])
# def upload_photo():
#     if request.method == 'POST':
#         try:
#             name = request.form.get('name')
#             if not name:
#                 return jsonify(success=False, message="Nama tidak boleh kosong")

#             photos = request.files.getlist('photos')
#             if not photos:
#                 return jsonify(success=False, message="Tidak ada foto yang dipilih")

#             user_folder = os.path.join('static/uploads', secure_filename(name))
#             os.makedirs(user_folder, exist_ok=True)

#             for photo in photos:
#                 if photo and allowed_file(photo.filename):
#                     filename = secure_filename(photo.filename)
#                     file_path = os.path.join(user_folder, filename)
#                     photo.save(file_path)
#                 else:
#                     return jsonify(success=False, 
#                                  message="Format file tidak didukung. Gunakan format PNG, JPG, atau JPEG")

#             return jsonify(success=True, 
#                          message="Foto berhasil diunggah")

#         except Exception as e:
#             return jsonify(success=False, 
#                          message=f"Terjadi kesalahan: {str(e)}")

#     return render_template('upload_user.html')

# def allowed_file(filename):
#     ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload_user.html', methods=['GET', 'POST'])
def upload_photo():
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
    clear_logs()  # Hapus semua log dari database
    return redirect(url_for('admin_dashboard'))  # Redirect kembali ke halaman home

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
    return render_template('stream.html')


# Route untuk prediksi gambar yang di-upload
@app.route("/predict", methods=["GET", "POST"])
def predict_img():
    if request.method == "POST":
        if 'file' in request.files:  # Cek apakah ada file di form
            f = request.files['file']
            basepath = os.path.dirname(__file__)  # Ambil direktori dasar
            upload_path = os.path.join(basepath, 'static', 'uploads')  # Path folder upload
            if not os.path.exists(upload_path):
                os.makedirs(upload_path)  # Buat folder jika belum ada
            filename = secure_filename(f.filename)  # Amankan nama file
            if '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png', 'mp4'}:
                unique_filename = generate_unique_filename(filename.rsplit('.', 1)[1].lower())  # Buat nama file unik
                filepath = os.path.join(upload_path, unique_filename)
                f.save(filepath)  # Simpan file

                file_extension = unique_filename.rsplit('.', 1)[1].lower()  # Ambil ekstensi file
                confidence_threshold = 0.70  # Threshold confidence
                iou_threshold = 0.90  # Threshold IoU
                detected = False

                if file_extension in {'jpg', 'jpeg', 'png', }:
                    img = cv2.imread(filepath)  # Baca gambar
                    detections = model(img, conf=confidence_threshold, iou=iou_threshold)  # Prediksi menggunakan model YOLO
                    detected = len(detections[0].boxes) > 0  # Cek apakah ada deteksi
                    img_with_boxes = custom_plot(detections)  # Tambahkan kotak dan label ke gambar
                    output_filename = generate_unique_filename('jpg')  # Buat nama file hasil
                    output_path = os.path.join('static', 'uploads', output_filename)
                    cv2.imwrite(output_path, img_with_boxes)  # Simpan gambar hasil

                    if detected:
                        cls_index = detections[0].boxes[0].cls[0].item()  # Ambil kelas deteksi pertama
                        person_name = class_names.get(cls_index, "Unknown")  # Ambil nama orang dari kelas
                        category = get_category(person_name)  # Dapatkan kategori

                        # Insert log meskipun sudah ada di tabel sebelumnya
                        insert_log(f'uploads/{output_filename}', person_name, category)

                    return render_template('result.html', detected=detected, image_path=f'uploads/{output_filename}', video_path=None)  # Render hasil
    return render_template('upload.html')  # Render halaman upload

# Fungsi untuk menangkap frame dari webcam dan melakukan deteksi
def generate_frames():
    cap = cv2.VideoCapture(0)  # Buka webcam
    detected_persons = set()  # Set untuk menyimpan orang yang terdeteksi
    detection_start_times = {}  # Dictionary untuk menyimpan waktu mulai deteksi

    while True:
        success, frame = cap.read()  # Ambil frame dari webcam
        if not success:
            break

        results = model(frame)  # Prediksi frame menggunakan YOLO
        frame_with_boxes = custom_plot(results)  # Tambahkan kotak dan label ke frame

        if len(results[0].boxes) > 0:  # Jika ada deteksi
            cls_index = results[0].boxes[0].cls[0].item()  # Ambil kelas deteksi pertama
            person_name = class_names.get(cls_index, "Unknown")  # Ambil nama orang
            category = get_category(person_name)  # Dapatkan kategori
            current_time = time.time()  # Waktu saat ini

            if person_name not in detection_start_times:  # Jika orang belum terdeteksi sebelumnya
                detection_start_times[person_name] = current_time  # Simpan waktu mulai deteksi
            elif current_time - detection_start_times[person_name] >= 20:  # Jika sudah lebih dari 20 detik
                image_filename = generate_unique_filename("jpg")  # Buat nama file gambar hasil
                image_path = os.path.join('static', 'images', image_filename)
                cv2.imwrite(image_path, frame_with_boxes)  # Simpan gambar hasil
                detected_persons.add(person_name)  # Tambahkan ke set orang terdeteksi
                insert_log(f'images/{image_filename}', person_name, category)  # Simpan log dengan kategori
                del detection_start_times[person_name]  # Hapus dari waktu deteksi

        # Konversi frame ke format JPEG untuk streaming
        ret, buffer = cv2.imencode('.jpg', frame_with_boxes)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # Kirim frame ke klien

# Route untuk streaming video
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Jika script dijalankan secara langsung
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=4000, help='Port untuk menjalankan aplikasi')
    args = parser.parse_args()

    app.run(host='0.0.0.0', port=args.port, debug=True)
