from flask import Blueprint, flash, redirect, render_template, request, url_for

from models import db
from models.member import Pelanggan
from routes.auth import login_required, owner_required


member_bp = Blueprint("member", __name__, url_prefix="/member")


@member_bp.route("/")
@login_required
@owner_required
def index():
    """Daftar semua pelanggan"""
    data_pelanggan = Pelanggan.query.order_by(Pelanggan.created_at.desc()).all()
    return render_template("member/index.html", data_pelanggan=data_pelanggan)


@member_bp.route("/tambah", methods=["GET", "POST"])
@login_required
@owner_required
def tambah():
    """Tambah pelanggan baru"""
    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        no_hp = request.form.get("no_hp", "").strip()
        alamat = request.form.get("alamat", "").strip()

        if not nama or not no_hp or not alamat:
            flash("Nama, nomor HP, dan alamat wajib diisi.", "warning")
            return render_template("member/form.html", pelanggan=None)

        if Pelanggan.query.filter_by(no_hp=no_hp).first():
            flash("Nomor HP sudah terdaftar.", "warning")
            return render_template("member/form.html", pelanggan=None)

        is_member = request.form.get("is_member") == "on"

        pelanggan = Pelanggan(
            nama=nama,
            no_hp=no_hp,
            alamat=alamat,
            is_member=is_member,
            total_point=0,
        )
        db.session.add(pelanggan)
        db.session.commit()

        flash("Pelanggan berhasil ditambahkan.", "success")
        return redirect(url_for("member.index"))

    return render_template("member/form.html", pelanggan=None)


@member_bp.route("/edit/<int:pelanggan_id>", methods=["GET", "POST"])
@login_required
@owner_required
def edit(pelanggan_id):
    """Edit data pelanggan"""
    pelanggan = Pelanggan.query.get_or_404(pelanggan_id)

    if request.method == "POST":
        nama = request.form.get("nama", "").strip()
        no_hp = request.form.get("no_hp", "").strip()
        alamat = request.form.get("alamat", "").strip()

        if not nama or not no_hp or not alamat:
            flash("Nama, nomor HP, dan alamat wajib diisi.", "warning")
            return render_template("member/form.html", pelanggan=pelanggan)

        existing_pelanggan = Pelanggan.query.filter(
            Pelanggan.no_hp == no_hp,
            Pelanggan.id != pelanggan_id
        ).first()
        if existing_pelanggan:
            flash("Nomor HP sudah terdaftar.", "warning")
            return render_template("member/form.html", pelanggan=pelanggan)

        pelanggan.nama = nama
        pelanggan.no_hp = no_hp
        pelanggan.alamat = alamat

        db.session.commit()
        flash("Data pelanggan berhasil diperbarui.", "success")
        return redirect(url_for("member.index"))

    return render_template("member/form.html", pelanggan=pelanggan)


@member_bp.route("/detail/<int:pelanggan_id>")
@login_required
@owner_required
def detail(pelanggan_id):
    """Detail pelanggan"""
    pelanggan = Pelanggan.query.get_or_404(pelanggan_id)
    return render_template("member/detail.html", pelanggan=pelanggan)


@member_bp.route("/hapus/<int:pelanggan_id>", methods=["POST"])
@login_required
@owner_required
def hapus(pelanggan_id):
    """Hapus pelanggan"""
    pelanggan = Pelanggan.query.get_or_404(pelanggan_id)

    db.session.delete(pelanggan)
    db.session.commit()

    flash("Pelanggan berhasil dihapus.", "success")
    return redirect(url_for("member.index"))
