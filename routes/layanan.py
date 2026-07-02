from decimal import Decimal, InvalidOperation

from flask import Blueprint, flash, redirect, render_template, request, url_for

from models import db
from models.layanan import Layanan
from routes.auth import login_required, owner_required


layanan_bp = Blueprint("layanan", __name__, url_prefix="/layanan")


@layanan_bp.route("/")
@login_required
@owner_required
def index():
    data_layanan = Layanan.query.order_by(Layanan.id_layanan.desc()).all()
    return render_template("layanan/index.html", data_layanan=data_layanan)


@layanan_bp.route("/tambah", methods=["GET", "POST"])
@login_required
@owner_required
def tambah():
    if request.method == "POST":
        nama_layanan = request.form.get("nama_layanan", "").strip()
        harga_perkg = request.form.get("harga_perkg", "0").strip()
        estimasi_hari = request.form.get("estimasi_hari", "0").strip()

        try:
            harga_perkg = Decimal(harga_perkg)
            estimasi_hari = int(estimasi_hari)
        except (InvalidOperation, ValueError):
            flash("Harga dan estimasi harus berupa angka.", "warning")
            return render_template("layanan/form.html", layanan=None)

        if not nama_layanan or harga_perkg < 0 or estimasi_hari < 1:
            flash("Nama layanan wajib diisi, harga minimal 0, dan estimasi minimal 1 hari.", "warning")
            return render_template("layanan/form.html", layanan=None)

        layanan = Layanan(
            nama_layanan=nama_layanan,
            harga_perkg=harga_perkg,
            estimasi_hari=estimasi_hari,
        )
        db.session.add(layanan)
        db.session.commit()

        flash("Layanan berhasil ditambahkan.", "success")
        return redirect(url_for("layanan.index"))

    return render_template("layanan/form.html", layanan=None)


@layanan_bp.route("/edit/<int:id_layanan>", methods=["GET", "POST"])
@login_required
@owner_required
def edit(id_layanan):
    layanan = Layanan.query.get_or_404(id_layanan)

    if request.method == "POST":
        nama_layanan = request.form.get("nama_layanan", "").strip()
        harga_perkg = request.form.get("harga_perkg", "0").strip()
        estimasi_hari = request.form.get("estimasi_hari", "0").strip()

        try:
            harga_perkg = Decimal(harga_perkg)
            estimasi_hari = int(estimasi_hari)
        except (InvalidOperation, ValueError):
            flash("Harga dan estimasi harus berupa angka.", "warning")
            return render_template("layanan/form.html", layanan=layanan)

        if not nama_layanan or harga_perkg < 0 or estimasi_hari < 1:
            flash("Nama layanan wajib diisi, harga minimal 0, dan estimasi minimal 1 hari.", "warning")
            return render_template("layanan/form.html", layanan=layanan)

        layanan.nama_layanan = nama_layanan
        layanan.harga_perkg = harga_perkg
        layanan.estimasi_hari = estimasi_hari

        db.session.commit()
        flash("Layanan berhasil diperbarui.", "success")
        return redirect(url_for("layanan.index"))

    return render_template("layanan/form.html", layanan=layanan)


@layanan_bp.route("/hapus/<int:id_layanan>", methods=["POST"])
@login_required
@owner_required
def hapus(id_layanan):
    layanan = Layanan.query.get_or_404(id_layanan)

    db.session.delete(layanan)
    db.session.commit()

    flash("Layanan berhasil dihapus.", "success")
    return redirect(url_for("layanan.index"))
