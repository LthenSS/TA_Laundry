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
                <thead><tr><th>Layanan</th><th>Berat</th><th>Harga</th><th>Sub Total</th></tr></thead>
                <tbody>
        `;
        data.layanan.forEach(function (l) {
            html += `<tr><td>${l.nama}</td><td>${l.berat} Kg</td><td>Rp ${formatNumber(l.harga)}</td><td>Rp ${formatNumber(l.sub_total)}</td></tr>`;
        });
        html += `</tbody></table></div>`;
        html += `<div class="d-flex justify-content-end"><div class="me-4">Subtotal: <strong>Rp ${formatNumber(data.subtotal)}</strong></div><div class="me-4">Diskon: <strong>Rp ${formatNumber(data.discount)}</strong></div><div>Total: <strong>Rp ${formatNumber(data.total)}</strong></div></div>`;

        container.innerHTML = html;

        const modalEl = document.getElementById('detailModal');
        const modal = new bootstrap.Modal(modalEl);
        modal.show();

        // print button - cetak hanya nota di popup window baru
        document.getElementById('printBtn').onclick = function () {
            printNota(data);
        };
    }

    function printNota(data) {
        let layananRows = '';
        data.layanan.forEach(function (l) {
            layananRows += `
                <tr>
                    <td>${l.nama}</td>
                    <td>${l.berat} Kg</td>
                    <td>Rp ${formatNumber(l.harga)}</td>
                    <td style="text-align:right;">Rp ${formatNumber(l.sub_total)}</td>
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
            font-size: 12px;
            color: #000;
            background: #fff;
            padding: 20px;
            max-width: 320px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 10px;
            border-bottom: 2px dashed #000;
            padding-bottom: 8px;
        }
        .header h2 {
            font-size: 16px;
            font-weight: bold;
            letter-spacing: 1px;
        }
        .header p {
            font-size: 11px;
            margin-top: 2px;
        }
        .section {
            margin: 8px 0;
            border-bottom: 1px dashed #000;
            padding-bottom: 8px;
        }
        .row-info {
            display: flex;
            justify-content: space-between;
            margin: 3px 0;
        }
        .row-info .label { color: #444; }
        .row-info .value { font-weight: bold; text-align: right; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 6px 0;
        }
        thead tr th {
            border-top: 1px solid #000;
            border-bottom: 1px solid #000;
            padding: 4px 2px;
            text-align: left;
            font-size: 11px;
        }
        tbody tr td {
            padding: 4px 2px;
            font-size: 11px;
            vertical-align: top;
        }
        tbody tr:last-child td {
            border-bottom: 1px solid #000;
        }
        .totals { margin-top: 8px; }
        .total-row {
            display: flex;
            justify-content: space-between;
            margin: 3px 0;
        }
        .total-row.grand-total {
            font-size: 14px;
            font-weight: bold;
            border-top: 2px solid #000;
            padding-top: 5px;
            margin-top: 5px;
        }
        .footer {
            text-align: center;
            margin-top: 14px;
            border-top: 2px dashed #000;
            padding-top: 8px;
            font-size: 11px;
        }
        @media print {
            body { padding: 0; }
            @page { margin: 5mm; size: 80mm auto; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h2>SMART WASH LAUNDRY</h2>
        <p>Nota Transaksi</p>
    </div>

    <div class="section">
        <div class="row-info"><span class="label">No. Nota</span><span class="value">${data.kode}</span></div>
        <div class="row-info"><span class="label">Tanggal</span><span class="value">${data.tanggal}</span></div>
        <div class="row-info"><span class="label">Status Laundry</span><span class="value">${data.status_laundry}</span></div>
        <div class="row-info"><span class="label">Status Bayar</span><span class="value">${data.status_pembayaran}</span></div>
    </div>

    <div class="section">
        <div class="row-info"><span class="label">Pelanggan</span><span class="value">${data.pelanggan.nama}</span></div>
        <div class="row-info"><span class="label">No. HP</span><span class="value">${data.pelanggan.no_hp}</span></div>
        <div class="row-info"><span class="label">Alamat</span><span class="value" style="max-width:60%;word-break:break-word;">${data.pelanggan.alamat}</span></div>
    </div>

    <div class="section">
        <table>
            <thead>
                <tr>
                    <th>Layanan</th>
                    <th>Berat</th>
                    <th>Harga</th>
                    <th style="text-align:right;">Subtotal</th>
                </tr>
            </thead>
            <tbody>
                ${layananRows}
            </tbody>
        </table>

        <div class="totals">
            <div class="total-row">
                <span>Subtotal</span>
                <span>Rp ${formatNumber(data.subtotal)}</span>
            </div>
            <div class="total-row">
                <span>Diskon</span>
                <span>- Rp ${formatNumber(data.discount)}</span>
            </div>
            <div class="total-row grand-total">
                <span>TOTAL</span>
                <span>Rp ${formatNumber(data.total)}</span>
            </div>
        </div>
    </div>

    <div class="footer">
        <p>Terima kasih telah mempercayakan</p>
        <p>laundry Anda kepada kami!</p>
        <p style="margin-top:6px;">*** Smart Wash Laundry ***</p>
    </div>

    <script>
        window.onload = function() {
            window.print();
            setTimeout(function() { window.close(); }, 500);
        };
    <\/script>
</body>
</html>`;

        const printWindow = window.open('', '_blank', 'width=400,height=600,scrollbars=yes');
        if (printWindow) {
            printWindow.document.write(notaHTML);
            printWindow.document.close();
        } else {
            alert('Popup diblokir browser. Harap izinkan popup untuk mencetak nota.');
        }
    }

    function formatNumber(val) {
        try { return Number(val).toLocaleString('id-ID', {maximumFractionDigits:0}); } catch(e) { return val; }
    }
});
