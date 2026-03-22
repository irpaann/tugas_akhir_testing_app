import os
import socket
import requests
from flask import Flask, request, render_template
from extensions import db
from models.rule_engine import check_rule_based

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
    if request.path.startswith('/static'):
        return

    client_ip = request.remote_addr
    
    # --- LANGKAH A: CEK STATUS BLACKLIST (DATABASE) ---
    try:
        params = {'ip': client_ip}
        response = requests.get(CHECK_IP_URL, params=params, timeout=0.2)
        if response.status_code == 200 and response.json().get("is_active"):
            # Kita tandai request ini sebagai 'blocked' agar after_request tahu alasannya
            request.attack_type = "IP Blacklisted"
            return render_template('blocked.html', reason="IP Terblokir"), 403
    except:
        pass

    # --- LANGKAH B: DETEKSI SERANGAN LOKAL (RULE-BASED) ---
    payload = f"{request.args.to_dict()} {request.form.to_dict()} {request.get_data(as_text=True)}"
    attack_type = check_rule_based(payload)
    
    if attack_type:
        # Simpan jenis serangan ke objek request agar bisa dibaca di after_request
        request.attack_type = attack_type
        return render_template('blocked.html', reason=f"Terdeteksi: {attack_type}"), 403

@app.after_request
def log_request_to_dashboard(response):
    if request.path.startswith('/static'):
        return response

    try:
        # 1. Identifikasi Payload
        if request.method in ["POST", "PUT", "PATCH"]:
            payload = request.get_json(silent=True) if request.is_json else request.form.to_dict()
        else:
            payload = request.args.to_dict()

        # 2. Ambil alasan serangan yang ditandai di before_request
        attack_reason = getattr(request, 'attack_type', None)

        log_data = {
            "ip": request.remote_addr,
            "url": request.path,
            "full_url": request.url, # Tambahkan ini agar sinkron dengan SELECT Dashboard
            "method": request.method,
            "status": response.status_code,
            "payload": payload,
            "reason": attack_reason,
            "ua": request.headers.get("User-Agent", "-")
        }

        # 3. Kirim ke Dashboard
        requests.post(MONITORING_URL, json=log_data, timeout=0.5)
        
    except Exception as e:
        app.logger.error(f"Logging Error: {e}")

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