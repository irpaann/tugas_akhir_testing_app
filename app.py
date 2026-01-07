import os
import socket
import requests
from flask import Flask, request
from extensions import db

# BLUEPRINT
from routes.auth import auth
from routes.product import product
from routes.user import user
from routes.search import search
from routes.api import api


app = Flask(__name__)
app.secret_key = "secret-key"

HOST_IP = socket.gethostbyname(socket.gethostname())
MONITORING_URL = f"http://{HOST_IP}:3000/log"

app.config['UPLOAD_FOLDER'] = "uploads"
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/webtesting'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


# REGISTER BLUEPRINT
app.register_blueprint(auth)
app.register_blueprint(product)
app.register_blueprint(user)
app.register_blueprint(search)
app.register_blueprint(api)


@app.after_request
def log_request(response):
    try:
        if request.method in ["POST", "PUT", "PATCH"]:
            payload = request.get_json(silent=True) if request.is_json else request.form.to_dict()
        else:
            payload = request.query_string.decode()

        response_body = response.get_data(as_text=True)
        response_preview = response_body[:500]

        data = {
            "ip": request.remote_addr,
            "url": request.path,
            "full_url": request.url,
            "method": request.method,
            "status": response.status_code,
            "ua": request.headers.get("User-Agent", "-"),
            "payload": payload,
            "response": response_preview
        }

        requests.post(MONITORING_URL, json=data, timeout=0.5)

    except Exception as e:
        pass

    return response


if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)

