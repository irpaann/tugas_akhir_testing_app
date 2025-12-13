from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import check_password_hash, generate_password_hash
from extensions import db
from models.models import User

auth = Blueprint("auth", __name__)

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        pw = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, pw):
            session["user"] = user.email
            session["user_name"] = user.name
            return redirect(url_for("product.index"))

        return "Login gagal: Email atau password salah."

    return render_template("login.html")


@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        pw = request.form["password"]
        name = request.form["name"]

        if User.query.filter_by(email=email).first():
            return "Email sudah terdaftar."

        hashed_pw = generate_password_hash(pw)

        new_user = User(name=name, email=email, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
