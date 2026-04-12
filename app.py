import os
import socket
import requests
from flask import Flask, request, render_template
from extensions import db
from models.rule_engine import check_rule_based
from urllib.parse import unquote

# Import Blueprints
from routes.auth import auth
from routes.product import product
from routes.user import user
from routes.search import search
from routes.api import api


app = Flask(__name__)

# ==========================================
# 1. KONFIGURASI (Environment & Variables)
# ==========================================
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")
app.config['UPLOAD_FOLDER'] = "uploads"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Deteksi Lingkungan (Docker vs Windows/Local)
IS_DOCKER = os.getenv("IS_DOCKER", "false").lower() == "true"

if IS_DOCKER:
    # Konfigurasi Docker
    MONITORING_URL = "http://dashboard_monitoring:3000/log"
    CHECK_IP_URL = "http://dashboard_monitoring:3000/api/blacklist/check"
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://root:root@db/webtesting"
else:
    # Konfigurasi Windows / Local Development
    HOST_IP = socket.gethostbyname(socket.gethostname())
    MONITORING_URL = f"http://127.0.0.1:3000/log"
    CHECK_IP_URL = f"http://127.0.0.1:3000/api/blacklist/check"
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/webtesting'

# Inisialisasi Database
db.init_app(app)

# ==========================================
# 2. REGISTRASI BLUEPRINTS
# ==========================================
app.register_blueprint(auth)
app.register_blueprint(product)
app.register_blueprint(user)
app.register_blueprint(search)
app.register_blueprint(api)

# ==========================================
# 3. MIDDLEWARE (Security & Logging)
# ==========================================
@app.before_request
def security_filter():
    # 1. Abaikan file statis
    if request.path.startswith('/static'):
        return

    client_ip = request.remote_addr
    
    # ==========================================================
    # LANGKAH A: CEK APAKAH IP INI SUDAH MASUK DAFTAR BLACKLIST
    # ==========================================================
    # Kita tanya ke dashboard apakah IP ini statusnya sedang BLOCKED
    try:
        # Gunakan endpoint check yang sudah kamu definisikan di CHECK_IP_URL
        # Contoh: http://127.0.0.1:3000/api/blacklist/check?ip=127.0.0.1
        check_ip = requests.get(f"{CHECK_IP_URL}?ip={client_ip}", timeout=0.5)
        if check_ip.status_code == 200:
            status_data = check_ip.json()
            if status_data.get("is_blocked"):
                reason = status_data.get("reason", "IP dalam daftar hitam")
                return render_template('blocked.html', reason=reason), 403
    except Exception as e:
        app.logger.error(f"Gagal cek status blacklist: {e}")

    # ==========================================================
    # LANGKAH B: SCREENING PAYLOAD (Jika IP belum di-blacklist)
    # ==========================================================
    args_str = request.query_string.decode('utf-8', errors='ignore') # Hasil: search=buku
    form_str = "&".join([f"{k}={v}" for k, v in request.form.items()]) # Hasil: username=admin&password=123
    data_str = request.get_data(as_text=True) # Data mentah dari body (JSON/XML)

    # Gabungkan semua (yang kosong tidak akan merusak string)
    raw_payload_parts = [p for p in [args_str, form_str, data_str] if p]
    raw_payload = " ".join(raw_payload_parts).strip()

    # Jika tidak ada payload sama sekali (misal sekadar buka halaman depan)
    if not raw_payload:
        raw_payload = ""# Gunakan string kosong, JANGAN gunakan "-" karena "-"
                        # dihitung karakter spesial oleh ML

    decoded_payload = unquote(raw_payload)

    security_data = {
        "ip": client_ip,
        "url": request.path,
        "full_url": request.url,
        "method": request.method,
        "payload": decoded_payload,
        "ua": request.headers.get("User-Agent", "-")
    }

    SCREENING_URL = MONITORING_URL.replace("/log", "/api/screen") 
    
    try:
        check_response = requests.post(SCREENING_URL, json=security_data, timeout=0.8)
        if check_response.status_code == 200:
            result = check_response.json()
            if result.get("action") == "BLOCK":
                return render_template('blocked.html', reason=result.get("reason")), 403
    except Exception as e:
        app.logger.error(f"Security Engine Connection Error: {e}")

@app.after_request
def log_final_status(response):
    # Logika log tetap ada untuk mencatat status akhir (200, 403, 404, dll)
    # Tapi Dashboard sudah tahu duluan dari proses screening di atas.
    if request.path.startswith('/static'):
        return response
    
    # Dashboard mungkin butuh update status final (misal: sukses 200)
    # Anda bisa membiarkan log_data dikirim ke /log seperti biasa.
    return response

# ==========================================
# 4. CLI COMMANDS & RUNNER
# ==========================================

@app.cli.command("init-db")
def init_db():
    """Command untuk inisialisasi database: 'flask init-db'"""
    with app.app_context():
        db.create_all()
    print("Database Berhasil Diinisialisasi!")

if __name__ == "__main__":
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)