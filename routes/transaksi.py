from decimal import Decimal, InvalidOperation
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for, jsonify

from decimal import Decimal, InvalidOperation
from datetime import datetime

from models import db
from models.transaksi import Transaksi
from models.detail_transaksi import DetailTransaksi
from models.pembayaran import Pembayaran
from models.point_member import PointMember
from models.member import Pelanggan
from models.layanan import Layanan
from models.promo import Promo
from routes.auth import login_required, karyawan_required
from routes.compat import alias_detail, alias_payment, alias_transaction


transaksi_bp = Blueprint("transaksi", __name__, url_prefix="/transaksi")


@transaksi_bp.route("/")
@login_required
@karyawan_required
def index():
    """Daftar semua transaksi"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '', type=str)
    
    query = Transaksi.query.order_by(Transaksi.tanggal_transaksi.desc())
    
    if status_filter:
        query = query.filter_by(status_transaksi=status_filter)
    
    data_transaksi = query.paginate(page=page, per_page=20)
    return render_template("transaksi/index.html", data_transaksi=data_transaksi, status_filter=status_filter)


@transaksi_bp.route("/buat", methods=["GET", "POST"])
@login_required
@karyawan_required
def buat():
    """Buat transaksi baru"""
    if request.method == "POST":
        return _process_transaksi_form()
    
    members = Pelanggan.query.order_by(Pelanggan.nama.asc()).all()
    layanan = Layanan.query.order_by(Layanan.nama_layanan.asc()).all()
    from datetime import date
    today = date.today()
    all_promos = Promo.query.filter_by(status='Aktif').all()
    promo = [p for p in all_promos if (not p.tanggal_mulai or today >= p.tanggal_mulai) and (not p.tanggal_selesai or today <= p.tanggal_selesai)]
    
    return render_template("transaksi/form.html", members=members, layanan=layanan, promo=promo, transaksi=None)


@transaksi_bp.route("/edit/<int:id_transaksi>", methods=["GET", "POST"])
@login_required
@karyawan_required
def edit(id_transaksi):
    """Edit transaksi"""
    transaksi = Transaksi.query.get_or_404(id_transaksi)
    
    if request.method == "POST":
        return _process_transaksi_form(transaksi)
    
    members = Pelanggan.query.order_by(Pelanggan.nama.asc()).all()
    layanan = Layanan.query.order_by(Layanan.nama_layanan.asc()).all()
    from datetime import date
    today = date.today()
    all_promos = Promo.query.filter_by(status='Aktif').all()
    promo = [p for p in all_promos if (not p.tanggal_mulai or today >= p.tanggal_mulai) and (not p.tanggal_selesai or today <= p.tanggal_selesai)]
    details = DetailTransaksi.query.filter_by(transaksi_id=id_transaksi).all()
    pembayaran = Pembayaran.query.filter_by(transaksi_id_transaksi=id_transaksi).first()
    
    return render_template(
        "transaksi/form.html",
        members=members,
        layanan=layanan,
        promo=promo,
        transaksi=transaksi,
        details=details,
        pembayaran=pembayaran
    )


@transaksi_bp.route("/detail/<int:id_transaksi>")
@login_required
@karyawan_required
def detail(id_transaksi):
    """Detail transaksi"""
    transaksi = Transaksi.query.get_or_404(id_transaksi)
    details = DetailTransaksi.query.filter_by(transaksi_id_transaksi=id_transaksi).all()
    details = [alias_detail(detail) for detail in details]
    pembayaran = alias_payment(Pembayaran.query.filter_by(transaksi_id_transaksi=id_transaksi).first())
    transaksi = alias_transaction(transaksi)

    return render_template("transaksi/detail.html", transaksi=transaksi, details=details, pembayaran=pembayaran)


@transaksi_bp.route("/status/<int:id_transaksi>", methods=["POST"])
@login_required
@karyawan_required
def update_status(id_transaksi):
    """Update status transaksi"""
    transaksi = Transaksi.query.get_or_404(id_transaksi)
    status = request.form.get('status', '').strip()
    
    valid_statuses = ['Menunggu', 'Diproses', 'Selesai', 'Diambil']
    
    if status not in valid_statuses:
        flash("Status tidak valid.", "warning")
        return redirect(url_for("transaksi.detail", id_transaksi=id_transaksi))
    
    transaksi.status_transaksi = status
    db.session.commit()
    
    flash(f"Status transaksi berhasil diubah menjadi {status}.", "success")
    return redirect(url_for("transaksi.detail", id_transaksi=id_transaksi))


@transaksi_bp.route("/hapus/<int:id_transaksi>", methods=["POST"])
@login_required
@karyawan_required
def hapus(id_transaksi):
    """Hapus transaksi"""
    transaksi = Transaksi.query.get_or_404(id_transaksi)

    # Delete related records
    DetailTransaksi.query.filter_by(transaksi_id=id_transaksi).delete()
    Pembayaran.query.filter_by(transaksi_id_transaksi=id_transaksi).delete()
    PointMember.query.filter_by(transaksi_id=id_transaksi).delete()

    db.session.delete(transaksi)
    db.session.commit()

    flash("Transaksi berhasil dihapus.", "success")
    return redirect(url_for("transaksi.index"))


@transaksi_bp.route("/api/hitung-total", methods=["POST"])
@login_required
@karyawan_required
def api_hitung_total():
    """API untuk menghitung total transaksi"""
    try:
        data = request.json
        items = data.get('items', [])
        promo_id = data.get('promo_id', None)
        
        total = Decimal(0)
        
        # Calculate total
        for item in items:
            try:
                layanan_id = int(item.get('layanan_id'))
                berat = Decimal(item.get('berat', 0))
                
                layanan = Layanan.query.get(layanan_id)
                if layanan:
                    total += layanan.harga_perkg * berat
            except (ValueError, InvalidOperation):
                pass
        
        diskon = Decimal(0)
        
        # Apply promo
        if promo_id:
            try:
                promo = Promo.query.get(int(promo_id))
                if promo and promo.status == 'Aktif':
                    if total >= promo.minimal_transaksi:
                        if promo.tipe_diskon == 'Persen':
                            diskon = total * (promo.nilai_diskon / 100)
                        else:
                            diskon = promo.nilai_diskon
            except (ValueError, InvalidOperation):
                pass
        
        total_bayar = total - diskon
        
        return jsonify({
            'total': str(total),
            'diskon': str(diskon),
            'total_bayar': str(total_bayar)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400


def _process_transaksi_form(transaksi=None):
    """Process form untuk membuat/edit transaksi"""
    try:
        pelanggan_id = request.form.get('pelanggan_id', '').strip()
        karyawan_id = request.form.get('karyawan_id', '').strip()
        status_transaksi = request.form.get('status_transaksi', 'Menunggu').strip()
        total_harga = Decimal(request.form.get('total_harga', 0))
        total_bayar = Decimal(request.form.get('total_bayar', 0))
        catatan = request.form.get('catatan', '').strip()
        
        # Validate
        if not pelanggan_id:
            flash("Pelanggan wajib dipilih.", "warning")
            return redirect(url_for("transaksi.buat"))
        
        pelanggan = Pelanggan.query.get_or_404(int(pelanggan_id))
        
        # Prepare transaction items
        layanan_items = []
        i = 0
        while True:
            layanan_id = request.form.get(f'layanan_id_{i}', '')
            berat = request.form.get(f'berat_{i}', '')
            
            if not layanan_id:
                break
            
            try:
                layanan_id = int(layanan_id)
                berat = Decimal(berat)
                
                layanan = Layanan.query.get_or_404(layanan_id)
                
                if berat <= 0:
                    flash(f"Berat layanan harus lebih dari 0.", "warning")
                    return redirect(url_for("transaksi.buat"))
                
                layanan_items.append({
                    'layanan_id': layanan_id,
                    'layanan': layanan,
                    'berat': berat
                })
            except (ValueError, InvalidOperation):
                flash("Format data tidak valid.", "warning")
                return redirect(url_for("transaksi.buat"))
            
            i += 1
        
        if not layanan_items:
            flash("Minimal satu layanan harus dipilih.", "warning")
            return redirect(url_for("transaksi.buat"))
        
        # Create or update transaksi
        if transaksi is None:
            transaksi = Transaksi(
                pelanggan_id=int(pelanggan_id),
                karyawan_id=int(karyawan_id) if karyawan_id else None,
                status_transaksi=status_transaksi,
                total_harga=total_harga,
                total_bayar=total_bayar,
                catatan=catatan
            )
            db.session.add(transaksi)
            db.session.flush()
        else:
            transaksi.pelanggan_id = int(pelanggan_id)
            transaksi.karyawan_id = int(karyawan_id) if karyawan_id else None
            transaksi.status_transaksi = status_transaksi
            transaksi.total_harga = total_harga
            transaksi.total_bayar = total_bayar
            transaksi.catatan = catatan
            
            # Delete old details
            DetailTransaksi.query.filter_by(transaksi_id=transaksi.id_transaksi).delete()
        
        # Add transaction items
        for item in layanan_items:
            subtotal = item['layanan'].harga_perkg * item['berat']
            detail = DetailTransaksi(
                transaksi_id=transaksi.id_transaksi,
                layanan_id=item['layanan_id'],
                berat=item['berat'],
                harga_satuan=item['layanan'].harga_perkg,
                subtotal=subtotal
            )
            db.session.add(detail)
        
        # Handle payment
        metode_pembayaran = request.form.get('metode_pembayaran', 'Cash').strip()
        status_pembayaran = request.form.get('status_pembayaran', 'Belum Bayar').strip()
        promo_id = request.form.get('promo_id', '').strip()
        diskon = Decimal(request.form.get('diskon', 0))
        
        pembayaran = Pembayaran.query.filter_by(transaksi_id_transaksi=transaksi.id_transaksi).first()
        
        if pembayaran is None:
            pembayaran = Pembayaran(
                    transaksi_id_transaksi=transaksi.id_transaksi,
                metode_pembayaran=metode_pembayaran,
                status_pembayaran=status_pembayaran,
                jumlah_bayar=total_bayar,
                promo_id=int(promo_id) if promo_id else None,
                diskon=diskon
            )
            db.session.add(pembayaran)
        else:
            pembayaran.metode_pembayaran = metode_pembayaran
            pembayaran.status_pembayaran = status_pembayaran
            pembayaran.jumlah_bayar = total_bayar
            pembayaran.promo_id = int(promo_id) if promo_id else None
            pembayaran.diskon = diskon
            
            if status_pembayaran == 'Lunas' and not pembayaran.tanggal_pembayaran:
                pembayaran.tanggal_pembayaran = datetime.now()
        
        # Add/update member points if applicable
        if status_pembayaran == 'Lunas':
            # Calculate points (example: 1 point per Rp 1000)
            poin = int(total_bayar / 1000)
            
            if poin > 0:
                # Check if point record already exists for this transaction
                existing_point = PointMember.query.filter_by(transaksi_id=transaksi.id_transaksi).first()
                
                if existing_point is None:
                    point_record = PointMember(
                        pelanggan_id=int(pelanggan_id),
                        transaksi_id=transaksi.id_transaksi,
                        jumlah_poin=poin,
                        tipe='Earned',
                        keterangan='Poin dari transaksi'
                    )
                    db.session.add(point_record)
                    # `total_point` is computed from PointMember records in model; no DB column to update
                else:
                    # Update existing point record
                    poin_diff = poin - existing_point.jumlah_poin
                    # `total_point` is computed from PointMember records in model; no DB column to update
                    existing_point.jumlah_poin = poin
        
        db.session.commit()
        
        action = "diperbarui" if transaksi.id_transaksi else "dibuat"
        flash(f"Transaksi berhasil {action}.", "success")
        return redirect(url_for("transaksi.detail", id_transaksi=transaksi.id_transaksi))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Terjadi kesalahan: {str(e)}", "danger")
        return redirect(url_for("transaksi.buat"))
