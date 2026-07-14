from flask import Blueprint, render_template, request, jsonify, send_file
from sqlalchemy import func, and_, or_, extract
from datetime import datetime, timedelta
from decimal import Decimal
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from models import db
from models.transaksi import Transaksi
from models.member import Pelanggan
from models.layanan import Layanan
from models.detail_transaksi import DetailTransaksi
from routes.auth import login_required, owner_required


laporan_bp = Blueprint("laporan", __name__, url_prefix="/laporan")



def _format_currency(value):
    """Format value as Indonesian Rupiah"""
    return f"Rp {float(value or 0):,.0f}".replace(",", ".")


def _format_currency_unformatted(value):
    """Format value as Indonesian Rupiah without formatting (for PDF)"""
    return f"Rp {float(value or 0):,.0f}".replace(",", ".")


def _get_date_range(filter_type='harian', start_date=None, end_date=None):
    """
    Get date range based on filter type.
    
    Args:
        filter_type: 'harian', 'mingguan', 'bulanan', or 'custom'
        start_date: ISO format date string for custom range
        end_date: ISO format date string for custom range
    
    Returns:
        (datetime_start, datetime_end) tuple
    """
    today = datetime.now().date()
    
    if filter_type == 'harian':
        # Today only
        dt_start = datetime.combine(today, datetime.min.time())
        dt_end = datetime.combine(today, datetime.max.time())
    elif filter_type == 'mingguan':
        # Last 7 days
        start = today - timedelta(days=6)
        dt_start = datetime.combine(start, datetime.min.time())
        dt_end = datetime.combine(today, datetime.max.time())
    elif filter_type == 'bulanan':
        # Current month
        month_start = today.replace(day=1)
        dt_start = datetime.combine(month_start, datetime.min.time())
        dt_end = datetime.combine(today, datetime.max.time())
    elif filter_type == 'custom' and start_date and end_date:
        # Custom date range
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            dt_start = datetime.combine(start, datetime.min.time())
            dt_end = datetime.combine(end, datetime.max.time())
        except ValueError:
            # Fall back to today if parsing fails
            dt_start = datetime.combine(today, datetime.min.time())
            dt_end = datetime.combine(today, datetime.max.time())
    else:
        # Default to today
        dt_start = datetime.combine(today, datetime.min.time())
        dt_end = datetime.combine(today, datetime.max.time())
    
    return dt_start, dt_end


def _get_filter_label(filter_type, dt_start, dt_end):
    """Get human-readable filter label"""
    if filter_type == 'harian':
        return f"Harian - {dt_start.strftime('%d/%m/%Y')}"
    elif filter_type == 'mingguan':
        return f"Mingguan - {dt_start.strftime('%d/%m/%Y')} s/d {dt_end.strftime('%d/%m/%Y')}"
    elif filter_type == 'bulanan':
        return f"Bulanan - {dt_start.strftime('%B %Y')}"
    elif filter_type == 'custom':
        return f"Custom - {dt_start.strftime('%d/%m/%Y')} s/d {dt_end.strftime('%d/%m/%Y')}"
    return "Laporan"


def _get_summary_data(dt_start, dt_end):
    """Get summary card data for given date range (reusable)"""
    # 1. Total Revenue (Lunas transactions only)
    total_revenue = db.session.query(func.sum(Transaksi.total)).filter(
        and_(
            Transaksi.tanggal >= dt_start,
            Transaksi.tanggal <= dt_end,
            Transaksi.status_pembayaran == 'Lunas'
        )
    ).scalar() or Decimal("0")
    
    # 2. Total Transactions
    total_transactions = db.session.query(func.count(Transaksi.id_transaksi)).filter(
        and_(
            Transaksi.tanggal >= dt_start,
            Transaksi.tanggal <= dt_end
        )
    ).scalar() or 0
    
    # 3. Total Customers (distinct)
    total_customers = db.session.query(
        func.count(func.distinct(Transaksi.pelanggan_id))
    ).filter(
        and_(
            Transaksi.tanggal >= dt_start,
            Transaksi.tanggal <= dt_end
        )
    ).scalar() or 0
    
    # 4. Total Members
    total_members = db.session.query(func.count(Pelanggan.id)).filter(
        and_(
            Pelanggan.is_member == True,
            Pelanggan.created_at >= dt_start,
            Pelanggan.created_at <= dt_end
        )
    ).scalar() or 0
    
    # 5. Total Completed Laundry
    total_completed = db.session.query(func.count(Transaksi.id_transaksi)).filter(
        and_(
            Transaksi.status_laundry == 'Selesai',
            Transaksi.tanggal >= dt_start,
            Transaksi.tanggal <= dt_end
        )
    ).scalar() or 0
    
    return {
        'total_revenue': total_revenue,
        'total_transactions': total_transactions,
        'total_customers': total_customers,
        'total_members': total_members,
        'total_completed': total_completed,
    }


def _get_table_data(dt_start, dt_end, search='', sort_by='tanggal', page=1, per_page=20):
    """Get transaction table data with pagination (reusable)"""
    # Base query with joins
    table_query = db.session.query(
        Transaksi.kode_transaksi,
        Transaksi.tanggal,
        Pelanggan.nama,
        Pelanggan.is_member,
        func.group_concat(Layanan.nama_layanan.distinct()).label('layanan_list'),
        Transaksi.status_laundry,
        Transaksi.status_pembayaran,
        Transaksi.total
    ).outerjoin(
        Pelanggan, Transaksi.pelanggan_id == Pelanggan.id
    ).outerjoin(
        DetailTransaksi, Transaksi.id_transaksi == DetailTransaksi.transaksi_id_transaksi
    ).outerjoin(
        Layanan, DetailTransaksi.layanan_id_layanan == Layanan.id_layanan
    ).filter(
        and_(
            Transaksi.tanggal >= dt_start,
            Transaksi.tanggal <= dt_end
        )
    )
    
    # Apply search filter
    if search:
        q = f"%{search}%"
        table_query = table_query.filter(
            or_(
                Transaksi.kode_transaksi.ilike(q),
                Pelanggan.nama.ilike(q)
            )
        )
    
    # Group by transaction - include all non-aggregated columns for TiDB compatibility
    table_query = table_query.group_by(
        Transaksi.id_transaksi,
        Transaksi.kode_transaksi,
        Transaksi.tanggal,
        Transaksi.status_laundry,
        Transaksi.status_pembayaran,
        Transaksi.total,
        Pelanggan.nama,
        Pelanggan.is_member
    )
    
    # Apply sorting
    if sort_by == 'nama':
        table_query = table_query.order_by(Pelanggan.nama.asc())
    elif sort_by == 'status_pembayaran':
        table_query = table_query.order_by(Transaksi.status_pembayaran.asc())
    elif sort_by == 'total':
        table_query = table_query.order_by(Transaksi.total.desc())
    else:  # Default to tanggal DESC
        table_query = table_query.order_by(Transaksi.tanggal.desc())
    
    # Paginate
    paginated = table_query.paginate(page=page, per_page=per_page)
    
    # Format table data
    table_data = []
    for row in paginated.items:
        table_data.append({
            'kode_transaksi': row.kode_transaksi,
            'tanggal': row.tanggal,
            'tanggal_formatted': row.tanggal.strftime('%d/%m/%Y %H:%M') if row.tanggal else '-',
            'nama_pelanggan': row.nama or 'Non-Member',
            'member_status': 'Member' if row.is_member else 'Non-Member',
            'layanan': row.layanan_list or '-',
            'status_laundry': row.status_laundry or '-',
            'status_pembayaran': row.status_pembayaran or '-',
            'total': row.total,
            'total_formatted': _format_currency(row.total)
        })
    
    return table_data, paginated


def _get_all_table_data(dt_start, dt_end, search='', sort_by='tanggal'):
    """Get all transaction table data without pagination (for PDF)"""
    # Base query with joins
    table_query = db.session.query(
        Transaksi.kode_transaksi,
        Transaksi.tanggal,
        Pelanggan.nama,
        Pelanggan.is_member,
        func.group_concat(Layanan.nama_layanan.distinct()).label('layanan_list'),
        Transaksi.status_laundry,
        Transaksi.status_pembayaran,
        Transaksi.total
    ).outerjoin(
        Pelanggan, Transaksi.pelanggan_id == Pelanggan.id
    ).outerjoin(
        DetailTransaksi, Transaksi.id_transaksi == DetailTransaksi.transaksi_id_transaksi
    ).outerjoin(
        Layanan, DetailTransaksi.layanan_id_layanan == Layanan.id_layanan
    ).filter(
        and_(
            Transaksi.tanggal >= dt_start,
            Transaksi.tanggal <= dt_end
        )
    )
    
    # Apply search filter
    if search:
        q = f"%{search}%"
        table_query = table_query.filter(
            or_(
                Transaksi.kode_transaksi.ilike(q),
                Pelanggan.nama.ilike(q)
            )
        )
    
    # Group by transaction - include all non-aggregated columns for TiDB compatibility
    table_query = table_query.group_by(
        Transaksi.id_transaksi,
        Transaksi.kode_transaksi,
        Transaksi.tanggal,
        Transaksi.status_laundry,
        Transaksi.status_pembayaran,
        Transaksi.total,
        Pelanggan.nama,
        Pelanggan.is_member
    )
    
    # Apply sorting
    if sort_by == 'nama':
        table_query = table_query.order_by(Pelanggan.nama.asc())
    elif sort_by == 'status_pembayaran':
        table_query = table_query.order_by(Transaksi.status_pembayaran.asc())
    elif sort_by == 'total':
        table_query = table_query.order_by(Transaksi.total.desc())
    else:
        table_query = table_query.order_by(Transaksi.tanggal.desc())
    
    # Get all results
    results = table_query.all()
    
    # Format table data
    table_data = []
    for row in results:
        table_data.append({
            'kode_transaksi': row.kode_transaksi,
            'tanggal': row.tanggal,
            'tanggal_formatted': row.tanggal.strftime('%d/%m/%Y %H:%M') if row.tanggal else '-',
            'nama_pelanggan': row.nama or 'Non-Member',
            'member_status': 'Member' if row.is_member else 'Non-Member',
            'layanan': row.layanan_list or '-',
            'status_laundry': row.status_laundry or '-',
            'status_pembayaran': row.status_pembayaran or '-',
            'total': row.total,
            'total_formatted': _format_currency(row.total)
        })
    
    return table_data


def _get_statistics_data(dt_start, dt_end):
    """Get statistics data (services, customers, ratios) - reusable"""
    # Top 5 Services
    top_services = db.session.query(
        Layanan.nama_layanan,
        func.count(DetailTransaksi.id_detail).label('count'),
        func.sum(DetailTransaksi.sub_total).label('total_amount')
    ).join(
        DetailTransaksi, Layanan.id_layanan == DetailTransaksi.layanan_id_layanan
    ).join(
        Transaksi, DetailTransaksi.transaksi_id_transaksi == Transaksi.id_transaksi
    ).filter(
        and_(
            Transaksi.tanggal >= dt_start,
            Transaksi.tanggal <= dt_end
        )
    ).group_by(
        Layanan.id_layanan, Layanan.nama_layanan
    ).order_by(
        func.sum(DetailTransaksi.sub_total).desc()
    ).limit(5).all()
    
    top_services_list = []
    for service_name, count, total_amount in top_services:
        top_services_list.append({
            'name': service_name,
            'count': count,
            'total': _format_currency(total_amount or 0)
        })
    
    # Most Active Customers (top 10)
    active_customers = db.session.query(
        Pelanggan.nama,
        func.count(Transaksi.id_transaksi).label('transaction_count'),
        func.sum(Transaksi.total).label('total_spent')
    ).join(
        Transaksi, Pelanggan.id == Transaksi.pelanggan_id
    ).filter(
        and_(
            Transaksi.tanggal >= dt_start,
            Transaksi.tanggal <= dt_end
        )
    ).group_by(
        Pelanggan.id, Pelanggan.nama
    ).order_by(
        func.count(Transaksi.id_transaksi).desc()
    ).limit(10).all()
    
    active_customers_list = []
    for name, tx_count, spent in active_customers:
        active_customers_list.append({
            'name': name,
            'transaction_count': tx_count,
            'total_spent': _format_currency(spent or 0)
        })
    
    # Member vs Non-Member ratio
    member_ratio = db.session.query(
        Pelanggan.is_member,
        func.count(Pelanggan.id).label('count')
    ).filter(
        Pelanggan.created_at >= dt_start,
        Pelanggan.created_at <= dt_end
    ).group_by(
        Pelanggan.is_member
    ).all()
    
    member_count = 0
    non_member_count = 0
    for is_member, count in member_ratio:
        if is_member:
            member_count = count
        else:
            non_member_count = count
    
    return {
        'top_services': top_services_list,
        'active_customers': active_customers_list,
        'member_count': member_count,
        'non_member_count': non_member_count,
    }





@laporan_bp.route("/")
@login_required
@owner_required
def index():
    """Main report page with filtering"""
    
    # Get filter parameters
    filter_type = request.args.get('filter', 'harian')
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    search = request.args.get('search', '').strip()
    sort_by = request.args.get('sort', 'tanggal')
    page = request.args.get('page', 1, type=int)
    
    # Get date range
    dt_start, dt_end = _get_date_range(filter_type, start_date, end_date)
    
    # Get all data using reusable functions
    summary = _get_summary_data(dt_start, dt_end)
    table_data, paginated = _get_table_data(dt_start, dt_end, search, sort_by, page)
    stats = _get_statistics_data(dt_start, dt_end)
    
    return render_template(
        'laporan/laporan.html',
        # Filter info
        filter_type=filter_type,
        date_range_start=dt_start.strftime('%d/%m/%Y'),
        date_range_end=dt_end.strftime('%d/%m/%Y'),
        search=search,
        sort_by=sort_by,
        # Summary cards
        total_revenue=_format_currency(summary['total_revenue']),
        total_transactions=summary['total_transactions'],
        total_customers=summary['total_customers'],
        total_members=summary['total_members'],
        total_completed=summary['total_completed'],
        # Table
        table_data=table_data,
        paginated=paginated,
        page=page,
        # Statistics
        top_services=stats['top_services'],
        active_customers=stats['active_customers'],
        member_count=stats['member_count'],
        non_member_count=stats['non_member_count'],
    )


def generate_pdf_bytes(filter_type, dt_start, dt_end, search='', sort_by='tanggal'):
    """Generate PDF report and return BytesIO object"""
    # Get all data using reusable functions
    summary = _get_summary_data(dt_start, dt_end)
    table_data = _get_all_table_data(dt_start, dt_end, search, sort_by)
    
    # Create PDF
    pdf_bytes = BytesIO()
    doc = SimpleDocTemplate(pdf_bytes, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    
    # Setup styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#17212b'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#6c757d'),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    # Title
    elements.append(Paragraph("SMART WASH LAUNDRY", title_style))
    filter_label = _get_filter_label(filter_type, dt_start, dt_end)
    generated_date = datetime.now().strftime('%d/%m/%Y %H:%M')
    elements.append(Paragraph(f"Laporan - {filter_label}", subtitle_style))
    elements.append(Paragraph(f"Periode: {dt_start.strftime('%d/%m/%Y')} s/d {dt_end.strftime('%d/%m/%Y')} | Dibuat: {generated_date}", subtitle_style))
    elements.append(Spacer(1, 0.15*inch))
    
    # Summary Cards as Table
    summary_data = [
        ['Total Pendapatan', 'Total Transaksi', 'Total Pelanggan', 'Total Member', 'Selesai'],
        [
            _format_currency(summary['total_revenue']),
            str(summary['total_transactions']),
            str(summary['total_customers']),
            str(summary['total_members']),
            str(summary['total_completed'])
        ]
    ]
    summary_table = Table(summary_data, colWidths=[1.5*inch, 1.4*inch, 1.4*inch, 1.4*inch, 1.4*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d6efd')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.beige, colors.white]),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Transaction Table
    if table_data:
        tx_data = [
            ['Kode', 'Tanggal', 'Pelanggan', 'Status', 'Layanan', 'Cucian', 'Pembayaran', 'Total']
        ]
        
        for row in table_data:
            tx_data.append([
                row['kode_transaksi'],
                row['tanggal'].strftime('%d/%m/%Y') if row['tanggal'] else '-',
                row['nama_pelanggan'][:22],  # Expanded truncate size
                'Member' if row['member_status'] == 'Member' else 'Non-Mbr',
                row['layanan'][:18] if row['layanan'] != '-' else '-', # Expanded
                row['status_laundry'][:8] if row['status_laundry'] else '-',
                'Lunas' if row['status_pembayaran'] == 'Lunas' else 'Belum',
                _format_currency(row['total'])
            ])
        
        tx_table = Table(tx_data, colWidths=[1.1*inch, 0.75*inch, 1.3*inch, 0.65*inch, 1.25*inch, 0.65*inch, 0.65*inch, 0.9*inch])
        tx_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#17212b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8f9fa'), colors.white]),
            ('ALIGN', (7, 0), (7, -1), 'RIGHT'),  # Right align Total column
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(Paragraph("Daftar Transaksi", styles['Heading3']))
        elements.append(tx_table)
    else:
        elements.append(Paragraph("Tidak ada data transaksi untuk periode ini.", styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    pdf_bytes.seek(0)
    return pdf_bytes


@laporan_bp.route("/export")
@login_required
@owner_required
def export():
    """Export current report as PDF"""
    try:
        # Get filter parameters
        filter_type = request.args.get('filter', 'harian')
        start_date = request.args.get('start')
        end_date = request.args.get('end')
        search = request.args.get('search', '').strip()
        sort_by = request.args.get('sort', 'tanggal')
        
        # Get date range
        dt_start, dt_end = _get_date_range(filter_type, start_date, end_date)
        
        # Generate PDF
        pdf_bytes = generate_pdf_bytes(filter_type, dt_start, dt_end, search, sort_by)
        
        filename = f"laporan_{filter_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        return send_file(
            pdf_bytes,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@laporan_bp.route("/test-email")
@login_required
@owner_required
def test_email():
    """Manually trigger daily report email for testing"""
    try:
        from flask import current_app
        from utils.email_sender import send_daily_report
        
        # Get date range for today
        dt_start, dt_end = _get_date_range('harian', None, None)
        
        # Generate PDF
        pdf_bytes = generate_pdf_bytes('harian', dt_start, dt_end)
        
        filename = f"laporan_harian_TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        receiver_email = request.args.get('email') or current_app.config.get('MAIL_RECEIVER')
        if not receiver_email:
            return jsonify({'success': False, 'error': 'No receiver email configured. Add MAIL_RECEIVER to .env or pass ?email=...'})
            
        success = send_daily_report(pdf_bytes, filename, receiver_email)
        
        if success:
            return jsonify({'success': True, 'message': f'Test email successfully sent to {receiver_email}'})
        else:
            return jsonify({'success': False, 'error': 'Failed to send email. Check server logs and credentials.'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
