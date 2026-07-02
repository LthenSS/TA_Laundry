from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from models.user import User


auth_bp = Blueprint("auth", __name__)


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Silakan login terlebih dahulu.", "warning")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped_view


def owner_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if session.get("role") != "Owner":
            session.clear()
            flash("Halaman ini hanya dapat diakses oleh Owner.", "danger")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped_view


def karyawan_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if session.get("role") != "Karyawan":
            session.clear()
            flash("Halaman ini hanya dapat diakses oleh Karyawan.", "danger")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped_view


@auth_bp.route("/", methods=["GET"])
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        if session.get("role") == "Owner":
            return redirect(url_for("dashboard.index"))
        if session.get("role") == "Karyawan":
            return redirect(url_for("karyawan.dashboard"))
        session.clear()
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            role = user.role

            if role not in ("Owner", "Karyawan"):
                session.clear()
                flash("Role pengguna tidak dikenali.", "danger")
                return redirect(url_for("auth.login"))

            session.clear()
            session["user_id"] = user.id_users
            session["nama"] = user.nama
            session["username"] = user.username
            session["role"] = role
            flash(f"Selamat datang, {user.nama}.", "success")
            if role == "Owner":
                return redirect(url_for("dashboard.index"))
            if role == "Karyawan":
                return redirect(url_for("karyawan.dashboard"))
            session.clear()
            flash("Role pengguna tidak dikenali.", "danger")
            return redirect(url_for("auth.login"))

        flash("Username atau password salah.", "danger")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Anda berhasil logout.", "success")
    return redirect(url_for("auth.login"))
