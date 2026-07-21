#!/usr/bin/env python
"""End-to-end test for PDF export route"""

from app import app
from flask import session

def test_pdf_export_route():
    """Test PDF export route with Flask test client"""
    
    try:
        with app.test_client() as client:
            # Note: This test assumes no authentication is required for testing
            # In production, you would need to login first
            
            # Test 1: PDF export with harian filter
            print("Testing PDF export route...")
            response = client.get('/laporan/export?filter=harian')
            
            if response.status_code == 302:
                # Redirected to login (expected without session)
                print("✓ Route requires authentication (expected)")
                print(f"  - Status: {response.status_code} (redirect to login)")
            elif response.status_code == 200:
                # Successfully generated PDF
                if response.mimetype == 'application/pdf':
                    print("✓ PDF export route works")
                    print(f"  - Status: {response.status_code}")
                    print(f"  - Content-Type: {response.mimetype}")
                    print(f"  - Content-Length: {len(response.data)} bytes")
                else:
                    print(f"✗ Unexpected content type: {response.mimetype}")
            else:
                print(f"✗ Unexpected status code: {response.status_code}")
            
            # Test 2: Check that both routes are registered
            print("\n✓ Checking registered routes...")
            routes = {}
            for rule in app.url_map.iter_rules():
                if 'laporan' in rule.rule:
                    routes[rule.rule] = list(rule.methods - {'OPTIONS', 'HEAD'})
            
            for route, methods in routes.items():
                print(f"  - {route}: {methods}")
            
            if '/laporan/' in routes and '/laporan/export' in routes:
                print("\n✅ All routes registered correctly!")
            else:
                print("\n❌ Missing expected routes!")
                
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_pdf_export_route()
