from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import check_password_hash, generate_password_hash
from extensions import db
from models.models import User
from sqlalchemy import text # Diperlukan untuk mengeksekusi query mentah

auth = Blueprint("auth", __name__)

@auth.route("/login", methods=["GET", "POST"])
@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        pw = request.form["password"]

        # Menggunakan Raw SQL agar rentan terhadap SQL Injection
        query = text(f"SELECT * FROM user WHERE email = '{email}'")
        result = db.session.execute(query).fetchone()

        if result:
            # Jika user ditemukan (atau berhasil di-bypass lewat SQLi)
            # Kita langsung buatkan session tanpa cek password hash untuk simulasi
            session["user"] = result[2]  # Kolom email
            session["user_name"] = result[1]  # Kolom name
            return redirect(url_for("product.index"))

        # --- PERBAIKAN DI SINI (1) ---
        # Jika query tidak menghasilkan apapun (result is None)
        return "Login gagal: Email atau payload salah."

    # --- PERBAIKAN DI SINI (2) ---
    # Jika method adalah GET (saat pertama kali buka halaman login)
    return render_template("login.html")


@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        pw = request.form["password"]
        name = request.form["name"]

        # --- PERUBAHAN: QUERY BIASA (VULNERABLE) ---
        # Pengecekan email terdaftar juga diubah menjadi query mentah
        check_query = text(f"SELECT * FROM user WHERE email = '{email}'")
        existing_user = db.session.execute(check_query).fetchone()

        if existing_user:
            return "Email sudah terdaftar."

        hashed_pw = generate_password_hash(pw)

        # Bagian insert tetap menggunakan objek untuk menjaga integritas database,
        # namun variabel 'email' dan 'name' yang masuk sudah mengandung payload jika dikirim.
        new_user = User(name=name, email=email, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("auth.login"))

    return render_template("register.html")

@auth.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))