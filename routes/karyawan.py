from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from models import db
from models.user import User
from routes.auth import login_required, owner_required


karyawan_bp = Blueprint("karyawan_admin", __name__, url_prefix="/karyawan")


@karyawan_bp.route("/")
@login_required
@owner_required
def index():
    data_karyawan = User.query.filter(User.role.in_(["Karyawan"]))
    data_karyawan = data_karyawan.order_by(User.id_users.asc()).all()
    return render_template("karyawan/index.html", data_karyawan=data_karyawan)


@karyawan_bp.route("/tambah", methods=["GET", "POST"])
@login_required
@owner_required
def tambah():
    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not nama or not username or not password:
            flash("Nama, username, dan password wajib diisi.", "warning")
            return render_template("karyawan/form.html", karyawan=None)

        if User.query.filter_by(username=username).first():
            flash("Username sudah digunakan.", "warning")
            return render_template("karyawan/form.html", karyawan=None)

        karyawan = User(
            nama=nama,
            username=username,
            password=generate_password_hash(password),
            role="Karyawan",
        )
        db.session.add(karyawan)
        db.session.commit()

        flash("Karyawan berhasil ditambahkan.", "success")
        return redirect(url_for("karyawan_admin.index"))

    return render_template("karyawan/form.html", karyawan=None)


@karyawan_bp.route("/edit/<int:id_users>", methods=["GET", "POST"])
@login_required
@owner_required
def edit(id_users):
    karyawan = User.query.filter(User.id_users == id_users, User.role.in_(["Karyawan"])).first_or_404()

    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        username = request.form.get("username", "").strip()

        if not nama or not username:
            flash("Nama dan username wajib diisi.", "warning")
            return render_template("karyawan/form.html", karyawan=karyawan)

        existing_user = User.query.filter(User.username == username, User.id_users != id_users).first()
        if existing_user:
            flash("Username sudah digunakan.", "warning")
            return render_template("karyawan/form.html", karyawan=karyawan)

        karyawan.nama = nama
        karyawan.username = username
        db.session.commit()

        flash("Data karyawan berhasil diperbarui.", "success")
        return redirect(url_for("karyawan_admin.index"))

    return render_template("karyawan/form.html", karyawan=karyawan)


@karyawan_bp.route("/reset-password/<int:id_users>", methods=["GET", "POST"])
@login_required
@owner_required
def reset_password(id_users):
    karyawan = User.query.filter(User.id_users == id_users, User.role.in_(["Karyawan"])).first_or_404()

    if request.method == "POST":
        password = request.form.get("password", "")
        konfirmasi_password = request.form.get("konfirmasi_password", "")

        if not password or not konfirmasi_password:
            flash("Password baru dan konfirmasi wajib diisi.", "warning")
            return render_template("karyawan/reset_password.html", karyawan=karyawan)

        if password != konfirmasi_password:
            flash("Konfirmasi password tidak sama.", "warning")
            return render_template("karyawan/reset_password.html", karyawan=karyawan)

        karyawan.password = generate_password_hash(password)
        db.session.commit()

        flash("Password karyawan berhasil direset.", "success")
        return redirect(url_for("karyawan_admin.index"))

    return render_template("karyawan/reset_password.html", karyawan=karyawan)


@karyawan_bp.route("/hapus/<int:id_users>", methods=["POST"])
@login_required
@owner_required
def hapus(id_users):
    karyawan = User.query.filter(User.id_users == id_users, User.role.in_(["Karyawan"])).first_or_404()

    try:
        db.session.delete(karyawan)
        db.session.commit()
        flash("Karyawan berhasil dihapus.", "success")
    except IntegrityError:
        db.session.rollback()
        flash("Karyawan tidak dapat dihapus karena masih terhubung dengan data transaksi.", "danger")

    return redirect(url_for("karyawan_admin.index"))
