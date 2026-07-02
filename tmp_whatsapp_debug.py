from app import app
from models.transaksi import Transaksi

app.config['TESTING'] = True

with app.app_context():
    tx = Transaksi.query.first()
    if not tx:
        raise SystemExit('No transaction found')
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'kasir1'
            sess['role'] = 'Karyawan'
        client.post('/karyawan/status', data={'transaksi_id': str(tx.id_transaksi), 'status': 'Siap Diambil'}, follow_redirects=False)
