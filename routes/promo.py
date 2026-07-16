from decimal import Decimal, InvalidOperation

from flask import Blueprint, flash, redirect, render_template, request, url_for

from models import db
from models.promo import Promo
from routes.auth import login_required, owner_required


promo_bp = Blueprint("promo", __name__, url_prefix="/promo")


@promo_bp.route("/")
@login_required
@owner_required
def index():
    data_promo = Promo.query.order_by(Promo.id_promo.desc()).all()
    return render_template("promo/index.html", data_promo=data_promo)


@promo_bp.route("/tambah", methods=["GET", "POST"])
@login_required
@owner_required
def tambah():
    if request.method == "POST":
        promo = _build_promo_from_form()
        if promo is None:
            return render_template("promo/form.html", promo=None)

        db.session.add(promo)
        db.session.commit()
        flash("Promo berhasil ditambahkan.", "success")
        return redirect(url_for("promo.index"))

    return render_template("promo/form.html", promo=None)


@promo_bp.route("/edit/<int:id_promo>", methods=["GET", "POST"])
@login_required
@owner_required
def edit(id_promo):
    promo = Promo.query.get_or_404(id_promo)

    if request.method == "POST":
        updated = _build_promo_from_form(promo)
        if updated is None:
            return render_template("promo/form.html", promo=promo)

        db.session.commit()
        flash("Promo berhasil diperbarui.", "success")
        return redirect(url_for("promo.index"))

    return render_template("promo/form.html", promo=promo)


@promo_bp.route("/toggle/<int:id_promo>", methods=["POST"])
@login_required
@owner_required
def toggle(id_promo):
    promo = Promo.query.get_or_404(id_promo)
    promo.status = "Tidak Aktif" if promo.status == "Aktif" else "Aktif"
    db.session.commit()

    flash(f"Status promo {promo.nama_promo} menjadi {promo.status}.", "success")
    return redirect(url_for("promo.index"))


def _build_promo_from_form(promo=None):
    nama_promo = request.form.get("nama_promo", "").strip()
    tipe_diskon = request.form.get("tipe_diskon", "").strip()
    nilai_diskon = request.form.get("nilai_diskon", "0").strip()
    minimal_transaksi = request.form.get("minimal_transaksi", "0").strip()
    status = request.form.get("status", "Aktif").strip()
    tanggal_mulai_str = request.form.get("tanggal_mulai", "").strip()
    tanggal_selesai_str = request.form.get("tanggal_selesai", "").strip()

    try:
        nilai_diskon = Decimal(nilai_diskon)
        minimal_transaksi = Decimal(minimal_transaksi)
    except (InvalidOperation, ValueError):
        flash("Nilai diskon dan minimal transaksi harus berupa angka.", "warning")
        return None

    if not nama_promo or tipe_diskon not in ["Persen", "Nominal"] or status not in ["Aktif", "Tidak Aktif"]:
        flash("Data promo belum lengkap.", "warning")
        return None

    if nilai_diskon <= 0 or minimal_transaksi < 0:
        flash("Nilai diskon harus lebih dari 0 dan minimal transaksi tidak boleh negatif.", "warning")
        return None

    if tipe_diskon == "Persen" and nilai_diskon > 100:
        flash("Diskon persen maksimal 100%.", "warning")
        return None
        
    tanggal_mulai = None
    tanggal_selesai = None
    if tanggal_mulai_str:
        try:
            from datetime import datetime
            tanggal_mulai = datetime.strptime(tanggal_mulai_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Format tanggal mulai tidak valid.", "warning")
            return None
            
    if tanggal_selesai_str:
        try:
            from datetime import datetime
            tanggal_selesai = datetime.strptime(tanggal_selesai_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Format tanggal selesai tidak valid.", "warning")
            return None

    if promo is None:
        promo = Promo()

    promo.nama_promo = nama_promo
    promo.tipe_diskon = tipe_diskon
    promo.nilai_diskon = nilai_diskon
    promo.minimal_transaksi = minimal_transaksi
    promo.status = status
    promo.tanggal_mulai = tanggal_mulai
    promo.tanggal_selesai = tanggal_selesai

    return promo
