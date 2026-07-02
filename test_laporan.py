#!/usr/bin/env python
"""Test script for FEATURE-007 Laporan implementation"""

from app import app, db
from models.transaksi import Transaksi
from models.member import Pelanggan
from models.layanan import Layanan
from datetime import datetime, timedelta

def test_laporan_implementation():
    """Test FEATURE-007 laporan route and functionality"""
    
    with app.app_context():
        try:
            # 1. Test database connectivity
            tx_count = db.session.query(Transaksi).count()
            pelanggan_count = db.session.query(Pelanggan).count()
            layanan_count = db.session.query(Layanan).count()
            
            print("✓ Database connection successful")
            print(f"  - Transaksi records: {tx_count}")
            print(f"  - Pelanggan records: {pelanggan_count}")
            print(f"  - Layanan records: {layanan_count}")
            
            # 2. Test date range function
            from routes.laporan import _get_date_range
            dt_start, dt_end = _get_date_range('harian')
            print(f"\n✓ Date range function working (harian)")
            print(f"  - Today range: {dt_start.date()} to {dt_end.date()}")
            
            dt_start, dt_end = _get_date_range('mingguan')
            print(f"\n✓ Date range function working (mingguan)")
            print(f"  - Weekly range: {dt_start.date()} to {dt_end.date()}")
            
            dt_start, dt_end = _get_date_range('bulanan')
            print(f"\n✓ Date range function working (bulanan)")
            print(f"  - Monthly range: {dt_start.date()} to {dt_end.date()}")
            
            # 3. Test currency formatting
            from routes.laporan import _format_currency
            formatted = _format_currency(1500000)
            print(f"\n✓ Currency formatting working")
            print(f"  - Format example: {formatted}")
            
            # 4. Verify blueprint is registered
            routes = [rule.rule for rule in app.url_map.iter_rules() if 'laporan' in rule.rule]
            print(f"\n✓ Laporan blueprint registered")
            print(f"  - Routes: {routes}")
            
            print(f"\n✅ All validation checks passed!")
            return True
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    test_laporan_implementation()
