document.addEventListener('DOMContentLoaded', function () {
    const table = document.getElementById('riwayatTable');
    const searchInput = document.getElementById('searchInput');
    const statusFilter = document.getElementById('statusFilter');
    const paymentFilter = document.getElementById('paymentFilter');
    const applyBtn = document.getElementById('applyFilters');

    // Client-side realtime search (kode, nama, hp)
    searchInput && searchInput.addEventListener('input', function () {
        const q = this.value.toLowerCase();
        Array.from(table.querySelectorAll('tbody tr')).forEach(function (tr) {
            const kode = tr.querySelector('.col-kode')?.textContent.toLowerCase() || '';
            const nama = tr.querySelector('.col-nama')?.textContent.toLowerCase() || '';
            const hp = tr.querySelector('.col-hp')?.textContent.toLowerCase() || '';
            const visible = kode.includes(q) || nama.includes(q) || hp.includes(q) || q === '';
            tr.style.display = visible ? '' : 'none';
        });
    });

    // Apply filters: perform full-page reload with query params
    applyBtn && applyBtn.addEventListener('click', function (e) {
        e.preventDefault();
        const params = new URLSearchParams(window.location.search);
        params.set('q', searchInput.value || '');
        params.set('status', statusFilter.value || '');
        params.set('payment_status', paymentFilter.value || '');
        window.location.search = params.toString();
    });

    // Detail buttons: fetch detail JSON and populate modal
    table.querySelectorAll('.btn-detail').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const id = this.getAttribute('data-id');
            fetch(`/karyawan/riwayat/detail/${id}`)
                .then(r => r.json())
                .then(data => showDetailModal(data))
                .catch(err => console.error(err));
        });
    });

    function showDetailModal(data) {
        const container = document.getElementById('detailContent');
        let html = `
            <div class="row">
              <div class="col-md-6">
                <h6>Pelanggan</h6>
                <p class="mb-0"><strong>${data.pelanggan.nama}</strong></p>
                <p class="mb-0">${data.pelanggan.no_hp}</p>
                <p class="mb-0">${data.pelanggan.alamat}</p>
              </div>
              <div class="col-md-6 text-end">
                <h6>Transaksi</h6>
                <p class="mb-0">Nota: <strong>${data.kode}</strong></p>
                <p class="mb-0">Tanggal: ${data.tanggal}</p>
                <p class="mb-0">Status Laundry: <span class="badge bg-secondary">${data.status_laundry}</span></p>
                <p class="mb-0">Status Bayar: <span class="badge ${data.metode_pembayaran ? 'bg-success' : 'bg-warning text-dark'}">${data.status_pembayaran}</span></p>
              </div>
            </div>
            <hr />
            <h6>Detail Layanan</h6>
            <div class="table-responsive">
              <table class="table table-sm">
                <thead><tr><th>Layanan</th><th>Satuan</th><th>Harga</th><th>Sub Total</th></tr></thead>
                <tbody>
        `;
        data.layanan.forEach(function (l) {
            const isAddon = l.jenis === 'AddOn';
            const badge = isAddon ? ' <span class="badge" style="background:#f59e0b; font-size:10px;">Add-On</span>' : '';
            const unit = isAddon ? `${l.qty || 1} Pcs` : `${l.berat} Kg`;
            html += `<tr><td>${l.nama}${badge}</td><td>${unit}</td><td>Rp ${formatNumber(l.harga)}</td><td>Rp ${formatNumber(l.sub_total)}</td></tr>`;
        });
        html += `</tbody></table></div>`;
        html += `<div class="d-flex justify-content-end"><div class="me-4">Subtotal: <strong>Rp ${formatNumber(data.subtotal)}</strong></div><div class="me-4">Diskon: <strong>Rp ${formatNumber(data.discount)}</strong></div><div>Total: <strong>Rp ${formatNumber(data.total)}</strong></div></div>`;

        container.innerHTML = html;

        const modalEl = document.getElementById('detailModal');
        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        modal.show();

        // print button - cetak hanya nota di popup window baru
        document.getElementById('printBtn').onclick = function () {
            printNota(data);
        };
    }

    function printNota(data) {
        let layananRows = '';
        data.layanan.forEach(function (l) {
            const isAddon = l.jenis === 'AddOn';
            const badge = isAddon ? ' <span style="border: 1px solid #000; border-radius: 4px; padding: 1px 4px; font-size: 10px;">Add-On</span>' : '';
            const unit = isAddon ? `${l.qty || 1} Pcs` : `${l.berat} Kg`;
            
            layananRows += `<tr>
                <td>${l.nama}${badge}</td>
                <td>${unit}</td>
                <td>Rp ${formatNumber(l.harga)}</td>
                <td class="text-end">Rp ${formatNumber(l.sub_total)}</td>
            </tr>`;
        });

        const notaHTML = `<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <title>Nota - ${data.kode}</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Courier New', Courier, monospace;
            font-size: 13px;
            color: #000;
            background: #fff;
            padding: 20px;
            max-width: 400px;
            margin: 0 auto;
        }
        .receipt-header { text-align: center; border-bottom: 2px dashed #000; padding-bottom: 15px; margin-bottom: 15px; }
        .receipt-header h3 { font-size: 18px; font-weight: bold; margin-bottom: 5px; }
        .receipt-header p { font-size: 12px; line-height: 1.4; margin: 0; }
        .receipt-info { margin-bottom: 15px; font-size: 13px; }
        .receipt-info .row { display: flex; justify-content: space-between; margin-bottom: 5px; }
        .receipt-table { width: 100%; margin-bottom: 15px; border-collapse: collapse; }
        .receipt-table th { border-top: 1px dashed #000; border-bottom: 1px dashed #000; padding: 6px 0; text-align: left; }
        .receipt-table td { padding: 6px 0; vertical-align: top; }
        .receipt-table .text-end { text-align: right; }
        .receipt-totals { border-top: 2px dashed #000; padding-top: 10px; }
        .receipt-totals .d-flex { display: flex; justify-content: space-between; margin-bottom: 5px; }
        .receipt-totals .grand-total { font-size: 15px; font-weight: bold; border-top: 1px dashed #000; padding-top: 10px; margin-top: 5px; }
        .qris-section { text-align: center; margin-top: 15px; border-top: 2px dashed #000; padding-top: 15px; }
        .receipt-footer { text-align: center; margin-top: 20px; border-top: 1px dashed #000; padding-top: 15px; font-size: 12px; }
        @media print { body { max-width: 100%; padding: 0; } }
    </style>
</head>
<body>
    <div class="receipt-header">
        <h3>SMART WASH LAUNDRY</h3>
        <p>Jl. Tegalrejo Raya Blk. E No. 51A - 51,<br>Tegalrejo, Kec. Argomulyo, Kota Salatiga</p>
    </div>

    <div class="receipt-info">
        <div class="row"><span>No. Nota</span><strong>${data.kode}</strong></div>
        <div class="row"><span>Pelanggan</span><strong>${data.pelanggan.nama}</strong></div>
        <div class="row"><span>Kasir</span><strong>${data.kasir_nama || '-'}</strong></div>
        <div class="row"><span>Status Cucian</span><span>${data.status_laundry}</span></div>
        <div class="row">
            <span>Pembayaran</span>
            <strong>${data.status_pembayaran.toUpperCase()}</strong>
        </div>
    </div>

    <table class="receipt-table">
        <thead>
            <tr>
                <th>Layanan</th>
                <th>Qty</th>
                <th>Harga</th>
                <th class="text-end">Subtotal</th>
            </tr>
        </thead>
        <tbody>
            ${layananRows}
        </tbody>
    </table>

    <div class="receipt-totals">
        <div class="d-flex"><span>Subtotal</span><span>Rp ${formatNumber(data.subtotal)}</span></div>
        ${data.discount > 0 ? `<div class="d-flex"><span>Diskon</span><span>- Rp ${formatNumber(data.discount)}</span></div>` : ''}
        <div class="d-flex grand-total"><span>TOTAL BAYAR</span><span>Rp ${formatNumber(data.total)}</span></div>
        <div class="d-flex" style="margin-top: 5px;"><span>Metode</span><span>${data.metode_pembayaran || '-'}</span></div>
    </div>

    ${data.qris_url ? `
    <div class="qris-section">
        <div style="font-weight:bold; margin-bottom:10px;">Scan QRIS untuk Membayar</div>
        <img src="${data.qris_url}" style="max-width:180px; width:100%;">
    </div>` : ''}

    <div class="receipt-footer">
        <div style="font-weight:bold; margin-bottom:5px;">TERIMA KASIH</div>
        <div>Silakan simpan nota ini sebagai bukti transaksi.</div>
    </div>

    <script>
        window.onload = function() {
            setTimeout(function() {
                window.print();
                setTimeout(function() { window.close(); }, 800);
            }, 500);
        };
    </script>
</body>
</html>`;

        // Use Blob URL to bypass popup blockers
        const blob = new Blob([notaHTML], { type: 'text/html' });
        const blobUrl = URL.createObjectURL(blob);
        const newTab = window.open(blobUrl, '_blank');
        if (newTab) {
            // Cleanup blob URL after tab opens
            setTimeout(function() { URL.revokeObjectURL(blobUrl); }, 5000);
        } else {
            // Fallback: download as HTML file
            const a = document.createElement('a');
            a.href = blobUrl;
            a.download = 'nota-' + (data.kode || 'transaksi') + '.html';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            setTimeout(function() { URL.revokeObjectURL(blobUrl); }, 2000);
        }
    }

    function formatNumber(val) {
        try { return Number(val).toLocaleString('id-ID', {maximumFractionDigits:0}); } catch(e) { return val; }
    }
});

