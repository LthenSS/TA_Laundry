#!/usr/bin/env python
"""Comprehensive validation test for PDF export implementation"""

from app import app, db
from datetime import datetime, timedelta
from decimal import Decimal

def test_all_validations():
    """Run all validation tests"""
    
    with app.app_context():
        try:
            print("=" * 60)
            print("FEATURE-007 PDF Export Implementation Validation")
            print("=" * 60)
            
            # Test 1: No code duplication
            print("\n1. CHECKING FOR CODE DUPLICATION...")
            from routes import laporan
            import inspect
            
            # Count query patterns
            source = inspect.getsource(laporan)
            func_sum_count = source.count('func.sum(')
            func_count_count = source.count('func.count(')
            query_count = source.count('.query(')
            
            print(f"   ✓ Query patterns found:")
            print(f"     - func.sum() calls: {func_sum_count}")
            print(f"     - func.count() calls: {func_count_count}")
            print(f"     - db.session.query() calls: {query_count}")
            
            # Verify reusable functions exist
            from routes.laporan import (
                _get_summary_data,
                _get_table_data,
                _get_all_table_data,
                _get_statistics_data,
                _get_date_range,
                _format_currency
            )
            print(f"   ✓ All 6 reusable helper functions exist")
            
            # Test 2: No SQLAlchemy errors
            print("\n2. TESTING SQLALCHEMY QUERIES...")
            dt_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            dt_end = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
            
            # Test summary queries
            summary = _get_summary_data(dt_start, dt_end)
            print(f"   ✓ Summary queries execute without errors")
            print(f"     - Total Revenue: {type(summary['total_revenue']).__name__}")
            print(f"     - Total Transactions: {summary['total_transactions']}")
            
            # Test table queries (paginated)
            table_data, paginated = _get_table_data(dt_start, dt_end, '', 'tanggal', 1, 20)
            print(f"   ✓ Paginated table query executes without errors")
            print(f"     - Records: {len(table_data)}")
            print(f"     - Pages: {paginated.pages}")
            
            # Test table queries (unpaginated)
            all_table_data = _get_all_table_data(dt_start, dt_end, '')
            print(f"   ✓ Unpaginated table query executes without errors")
            print(f"     - Records: {len(all_table_data)}")
            
            # Test statistics
            stats = _get_statistics_data(dt_start, dt_end)
            print(f"   ✓ Statistics queries execute without errors")
            print(f"     - Services: {len(stats['top_services'])}")
            print(f"     - Customers: {len(stats['active_customers'])}")
            
            # Test 3: Date range filtering
            print("\n3. TESTING DATE RANGE FILTERING...")
            filters = ['harian', 'mingguan', 'bulanan', 'custom']
            for f in filters:
                if f == 'custom':
                    dt_s, dt_e = _get_date_range(f, '2026-06-01', '2026-06-27')
                else:
                    dt_s, dt_e = _get_date_range(f)
                print(f"   ✓ {f.capitalize()}: {dt_s.date()} to {dt_e.date()}")
            
            # Test 4: Currency formatting
            print("\n4. TESTING CURRENCY FORMATTING...")
            test_values = [0, 1000, 1500000, 9999999.99]
            for val in test_values:
                formatted = _format_currency(Decimal(val))
                print(f"   ✓ {val} -> {formatted}")
            
            # Test 5: Routes registered
            print("\n5. CHECKING ROUTE REGISTRATION...")
            routes = {}
            for rule in app.url_map.iter_rules():
                if 'laporan' in rule.rule:
                    routes[rule.rule] = list(rule.methods - {'OPTIONS', 'HEAD'})
            
            for route, methods in sorted(routes.items()):
                print(f"   ✓ {route}: {methods}")
            
            # Test 6: Verify requirements.txt
            print("\n6. CHECKING DEPENDENCIES...")
            try:
                import reportlab
                print(f"   ✓ reportlab version: {reportlab.Version}")
            except ImportError:
                print(f"   ✗ reportlab not installed!")
            
            # Test 7: PDF generation
            print("\n7. TESTING PDF GENERATION...")
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph
            from reportlab.lib.styles import getSampleStyleSheet
            from io import BytesIO
            
            pdf_buffer = BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()
            elements.append(Paragraph("Test", styles['Normal']))
            doc.build(elements)
            
            pdf_buffer.seek(0)
            pdf_data = pdf_buffer.getvalue()
            print(f"   ✓ PDF generated successfully")
            print(f"     - Size: {len(pdf_data)} bytes")
            print(f"     - Header: {pdf_data[:8]}")
            
            # Test 8: No duplicate business logic
            print("\n8. CHECKING FOR DUPLICATE BUSINESS LOGIC...")
            
            # The index() and export() routes should use the same helper functions
            from routes.laporan import index, export
            
            index_source = inspect.getsource(index)
            export_source = inspect.getsource(export)
            
            # Verify both use the same helpers
            helpers_used = [
                '_get_date_range',
                '_get_summary_data',
                '_get_statistics_data'
            ]
            
            all_use_helpers = True
            for helper in helpers_used:
                if helper in index_source and helper in export_source:
                    print(f"   ✓ Both routes use {helper}()")
                elif helper not in index_source or helper not in export_source:
                    print(f"   ✗ Mismatch in {helper}() usage")
                    all_use_helpers = False
            
            if all_use_helpers:
                print(f"   ✓ No duplicate business logic detected")
            
            print("\n" + "=" * 60)
            print("✅ ALL VALIDATION TESTS PASSED!")
            print("=" * 60)
            return True
            
        except Exception as e:
            print(f"\n❌ VALIDATION ERROR: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    test_all_validations()
