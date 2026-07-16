from flask import Blueprint, render_template, jsonify, request
from sqlalchemy import func, and_, extract, or_
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta, date as date_type
from decimal import Decimal

from models import db
from models.transaksi import Transaksi
from models.member import Pelanggan
from models.layanan import Layanan
from models.detail_transaksi import DetailTransaksi
from routes.auth import login_required, owner_required


dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/owner")


def _format_currency(value):
    """Format value as Indonesian Rupiah"""
    return f"Rp {float(value or 0):,.0f}".replace(",", ".")


def _build_status_summary():
    """Build laundry status counts using a single aggregated query for owner dashboard."""
    status_summary = db.session.query(
        Transaksi.status_laundry,
        func.count(Transaksi.id_transaksi)
    ).group_by(Transaksi.status_laundry).all()

    status_data = {
        'Antrian': 0,
        'Diproses': 0,
        'Siap Diambil': 0,
        'Selesai': 0
    }
    for status, count in status_summary:
        if status in status_data:
            status_data[status] = count
    return status_data


@dashboard_bp.route("/dashboard")
@login_required
@owner_required
def index():
    # Get today's date
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    # Get first day of month
    month_start = today.replace(day=1)
    month_start_dt = datetime.combine(month_start, datetime.min.time())
    
    # 1. Today's Revenue (sum of total where status_pembayaran = 'Lunas' and tanggal is today)
    today_revenue = db.session.query(func.sum(Transaksi.total)).filter(
        and_(
            Transaksi.tanggal >= today_start,
            Transaksi.tanggal <= today_end,
            Transaksi.status_pembayaran == 'Lunas'
        )
    ).scalar() or Decimal("0")
    
    # 2. Monthly Revenue (sum of total where status_pembayaran = 'Lunas' and tanggal is current month)
    monthly_revenue = db.session.query(func.sum(Transaksi.total)).filter(
        and_(
            extract('year', Transaksi.tanggal) == today.year,
            extract('month', Transaksi.tanggal) == today.month,
            Transaksi.status_pembayaran == 'Lunas'
        )
    ).scalar() or Decimal("0")
    
    # 3. Today's Transactions (count of transaksi where tanggal is today)
    today_transactions = db.session.query(func.count(Transaksi.id_transaksi)).filter(
        and_(
            Transaksi.tanggal >= today_start,
            Transaksi.tanggal <= today_end
        )
    ).scalar() or 0
    
    # 4. Total Members
    total_members = db.session.query(func.count(Pelanggan.id)).filter(
        Pelanggan.is_member == True
    ).scalar() or 0
    
    # 5. Total Non-Members
    total_non_members = db.session.query(func.count(Pelanggan.id)).filter(
        Pelanggan.is_member == False
    ).scalar() or 0
    
    # 6. Status Summary (count by laundry status)
    status_data = _build_status_summary()
    
    # 7. Top 5 Services (group by layanan, sum the total amount)
    top_services = db.session.query(
        Layanan.nama_layanan,
        func.count(DetailTransaksi.id_detail).label('count'),
        func.sum(DetailTransaksi.sub_total).label('total_amount')
    ).join(
        DetailTransaksi, Layanan.id_layanan == DetailTransaksi.layanan_id_layanan
    ).group_by(Layanan.id_layanan, Layanan.nama_layanan).order_by(
        func.sum(DetailTransaksi.sub_total).desc()
    ).limit(5).all()
    
    top_services_list = []
    for service_name, count, total_amount in top_services:
        top_services_list.append({
            'name': service_name,
            'count': count,
            'total': _format_currency(total_amount or 0)
        })

    # 8. Recent Active Transactions (cucian aktif untuk tabel)
    recent_txns_raw = (
        db.session.query(Transaksi)
        .options(selectinload(Transaksi.pelanggan))
        .filter(Transaksi.status_laundry != 'Selesai')
        .order_by(Transaksi.tanggal.desc())
        .limit(8)
        .all()
    )

    STATUS_COLOR = {
        'Antrian': 'sw-status-queue',
        'Diproses': 'sw-status-wash',
        'Siap Diambil': 'sw-status-ready',
        'Selesai': 'sw-status-done',
    }

    recent_transactions = []
    for trx in recent_txns_raw:
        # Ambil semua layanan dari detail transaksi
        details = DetailTransaksi.query.options(selectinload(DetailTransaksi.layanan)).filter_by(transaksi_id_transaksi=trx.id_transaksi).all()
        layanan_names = ', '.join([d.layanan.nama_layanan for d in details if d.layanan]) if details else (trx.catatan or '-')
        recent_transactions.append({
            'id': trx.id_transaksi,
            'pelanggan': trx.pelanggan.nama if trx.pelanggan else '-',
            'layanan': layanan_names,
            'status': trx.status_laundry,
            'status_class': STATUS_COLOR.get(trx.status_laundry, ''),
            'total': _format_currency(trx.total or 0),
        })
    
    return render_template(
        "dashboard.html",
        today_revenue=_format_currency(today_revenue),
        monthly_revenue=_format_currency(monthly_revenue),
        today_transactions=today_transactions,
        total_members=total_members,
        total_non_members=total_non_members,
        status_summary=status_data,
        top_services=top_services_list,
        recent_transactions=recent_transactions,
    )


@dashboard_bp.route("/riwayat")
@login_required
@owner_required
def riwayat():
    """Read-only transaction history for owner."""
    search = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '').strip()
    payment_status = request.args.get('payment_status', '').strip()

    query = (
        db.session.query(Transaksi)
        .options(selectinload(Transaksi.pelanggan))
        .join(Pelanggan, Transaksi.pelanggan_id == Pelanggan.id)
    )

    if search:
        q = f"%{search}%"
        query = query.filter(or_(Transaksi.kode_transaksi.ilike(q), Pelanggan.nama.ilike(q), Pelanggan.no_hp.ilike(q)))

    if status_filter in ["Antrian", "Diproses", "Siap Diambil", "Selesai"]:
        query = query.filter(Transaksi.status_laundry == status_filter)

    if payment_status in ["Belum Bayar", "Lunas"]:
        query = query.filter(Transaksi.status_pembayaran == payment_status)

    orders = query.order_by(Transaksi.tanggal.desc()).all()
    result = []
    for transaksi in orders:
        pelanggan = transaksi.pelanggan
        result.append({
            'id': transaksi.id_transaksi,
            'kode': getattr(transaksi, 'kode_transaksi', transaksi.id_transaksi),
            'tanggal': transaksi.tanggal.strftime('%d/%m/%Y %H:%M') if transaksi.tanggal else '-',
            'pelanggan': pelanggan.nama if pelanggan else '-',
            'no_hp': pelanggan.no_hp if pelanggan else '-',
            'total': transaksi.total,
            'status_laundry': transaksi.status_laundry,
            'status_pembayaran': transaksi.status_pembayaran,
            'status_laundry_class': {
                'Antrian': 'bg-secondary',
                'Diproses': 'bg-primary',
                'Siap Diambil': 'bg-warning text-dark',
                'Selesai': 'bg-success',
            }.get(transaksi.status_laundry, 'bg-secondary'),
            'status_pembayaran_class': 'bg-success' if transaksi.status_pembayaran == 'Lunas' else 'bg-danger',
        })

    return render_template(
        'kasir/riwayat.html',
        orders=result,
        search=search,
        status_filter=status_filter,
        payment_status=payment_status,
        format_currency=_format_currency,
        layout_template='base.html',
    )


@dashboard_bp.route("/api/revenue-by-month")
@login_required
@owner_required
def api_revenue_by_month():
    """API endpoint for revenue by month chart data"""
    # Get last 12 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    revenue_data = db.session.query(
        extract('year', Transaksi.tanggal).label('year'),
        extract('month', Transaksi.tanggal).label('month'),
        func.sum(Transaksi.total).label('revenue')
    ).filter(
        and_(
            Transaksi.tanggal >= start_date,
            Transaksi.status_pembayaran == 'Lunas'
        )
    ).group_by(
        extract('year', Transaksi.tanggal),
        extract('month', Transaksi.tanggal)
    ).order_by(
        extract('year', Transaksi.tanggal),
        extract('month', Transaksi.tanggal)
    ).all()
    
    # Create ordered month list for the last 12 months
    months_id = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']
    month_labels = []
    revenue_values = []
    
    # Build ordered list of (year, month) for the last 12 months
    ordered_months = []
    for i in range(11, -1, -1):
        d = end_date - timedelta(days=i * 30)
        ordered_months.append((d.year, d.month))
    
    # Build lookup from actual data
    revenue_lookup = {}
    for year, month, revenue in revenue_data:
        if year and month:
            revenue_lookup[(int(year), int(month))] = float(revenue or 0)
    
    for (yr, mo) in ordered_months:
        month_labels.append(months_id[mo - 1])
        revenue_values.append(revenue_lookup.get((yr, mo), 0))
    
    return jsonify({
        'labels': month_labels,
        'data': revenue_values
    })


@dashboard_bp.route("/api/transactions-by-day")
@login_required
@owner_required
def api_transactions_by_day():
    """API endpoint for transactions by day chart data (last 7 days)"""
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=6)
    
    transactions_data = db.session.query(
        func.date(Transaksi.tanggal).label('date'),
        func.count(Transaksi.id_transaksi).label('count')
    ).filter(
        Transaksi.tanggal >= datetime.combine(start_date, datetime.min.time())
    ).group_by(
        func.date(Transaksi.tanggal)
    ).order_by(
        func.date(Transaksi.tanggal)
    ).all()
    
    # Create date labels and lookup
    day_labels_id = ['Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab', 'Min']
    day_labels = []
    transaction_counts = []
    date_index_map = {}

    for i in range(7):
        check_date = start_date + timedelta(days=i)
        day_labels.append(day_labels_id[check_date.weekday()])
        transaction_counts.append(0)
        date_index_map[check_date] = i

    # Fill in actual data
    for tx_date, count in transactions_data:
        if tx_date:
            if isinstance(tx_date, datetime):
                d = tx_date.date()
            else:
                d = tx_date
            if d in date_index_map:
                transaction_counts[date_index_map[d]] = count
    
    return jsonify({
        'labels': day_labels,
        'data': transaction_counts
    })
