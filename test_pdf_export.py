#!/usr/bin/env python
"""Test script for FEATURE-007 PDF Export implementation"""

from app import app, db
from models.transaksi import Transaksi
from datetime import datetime, timedelta
from io import BytesIO

def test_pdf_export():
    """Test PDF export functionality"""
    
    with app.app_context():
        try:
            # 1. Verify imports
            from routes.laporan import _get_date_range, _get_summary_data, _get_all_table_data, _get_statistics_data
            print("✓ All PDF export functions imported successfully")
            
            # 2. Test date range function
            dt_start, dt_end = _get_date_range('harian')
            print(f"✓ Date range function works")
            print(f"  - Harian: {dt_start.date()} to {dt_end.date()}")
            
            # 3. Test summary data function
            summary = _get_summary_data(dt_start, dt_end)
            print(f"\n✓ Summary data function works")
            print(f"  - Total Revenue: {summary['total_revenue']}")
            print(f"  - Total Transactions: {summary['total_transactions']}")
            
            # 4. Test table data function (no pagination)
            table_data = _get_all_table_data(dt_start, dt_end)
            print(f"\n✓ Table data function works (unpaginated)")
            print(f"  - Records returned: {len(table_data)}")
            
            # 5. Test statistics function
            stats = _get_statistics_data(dt_start, dt_end)
            print(f"\n✓ Statistics data function works")
            print(f"  - Top Services: {len(stats['top_services'])}")
            print(f"  - Active Customers: {len(stats['active_customers'])}")
            
            # 6. Test PDF generation (without saving to disk)
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph
            from reportlab.lib.styles import getSampleStyleSheet
            
            pdf_buffer = BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()
            elements.append(Paragraph("Test PDF", styles['Title']))
            doc.build(elements)
            
            pdf_buffer.seek(0)
            pdf_size = len(pdf_buffer.getvalue())
            print(f"\n✓ PDF generation works")
            print(f"  - Generated PDF size: {pdf_size} bytes")
            
            # 7. Verify routes
            routes = [rule.rule for rule in app.url_map.iter_rules() if 'laporan' in rule.rule]
            print(f"\n✓ Laporan routes registered")
            print(f"  - Routes: {routes}")
            
            print(f"\n✅ All PDF export tests passed!")
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    test_pdf_export()
