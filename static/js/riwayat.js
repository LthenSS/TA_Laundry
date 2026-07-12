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
            layananRows += `<tr>
                <td style="padding:8px 10px;border:1px solid #dee2e6;">${l.nama}</td>
                <td style="padding:8px 10px;border:1px solid #dee2e6;">${l.berat} Kg</td>
                <td style="padding:8px 10px;border:1px solid #dee2e6;">Rp ${formatNumber(l.harga)}</td>
                <td style="padding:8px 10px;border:1px solid #dee2e6;text-align:right;font-weight:600;">Rp ${formatNumber(l.sub_total)}</td>
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
            font-family: Arial, sans-serif;
            font-size: 14px;
            color: #212529;
            background: #fff;
            padding: 32px 40px;
            max-width: 720px;
            margin: 0 auto;
        }
        .nota-header {
            text-align: center;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 2px solid #dee2e6;
        }
        .nota-header h2 {
            font-size: 22px;
            font-weight: 700;
            letter-spacing: 1px;
            margin-bottom: 4px;
        }
        .nota-header p {
            font-size: 13px;
            color: #6c757d;
        }
        .info-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0 24px;
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 1px solid #dee2e6;
        }
        .info-block { margin-bottom: 12px; }
        .info-label {
            font-size: 12px;
            color: #6c757d;
            margin-bottom: 2px;
        }
        .info-value {
            font-size: 15px;
            font-weight: 600;
        }
        .info-value.nota-kode { color: #0d6efd; }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        thead th {
            background: #f8f9fa;
            padding: 10px 12px;
            text-align: left;
            font-size: 13px;
            font-weight: 600;
            border: 1px solid #dee2e6;
        }
        thead th:last-child { text-align: right; }
        tbody td {
            padding: 10px 12px;
            font-size: 14px;
            border: 1px solid #dee2e6;
            vertical-align: top;
        }
        tbody td:last-child { text-align: right; font-weight: 600; }
        .summary {
            display: flex;
            justify-content: flex-end;
        }
        .summary-box {
            width: 280px;
        }
        .summary-row {
            display: flex;
            justify-content: space-between;
            padding: 6px 0;
            font-size: 14px;
        }
        .summary-row.discount { color: #dc3545; }
        .summary-row.grand-total {
            border-top: 2px solid #dee2e6;
            padding-top: 10px;
            margin-top: 4px;
            font-size: 17px;
            font-weight: 700;
        }
        .nota-footer {
            text-align: center;
            margin-top: 32px;
            padding-top: 16px;
            border-top: 2px solid #dee2e6;
            font-size: 13px;
            color: #6c757d;
        }
        @media print {
            body { padding: 12px 16px; }
            @page { margin: 10mm; size: A4 portrait; }
        }
    </style>
</head>
<body>
    <div class="nota-header">
        <h2>SMART WASH LAUNDRY</h2>
        <p>Terima kasih sudah mempercayakan laundry Anda kepada kami.</p>
    </div>

    <div class="info-grid">
        <div class="info-block">
            <div class="info-label">Kode Transaksi</div>
            <div class="info-value nota-kode">${data.kode}</div>
        </div>
        <div class="info-block">
            <div class="info-label">Nama Pelanggan</div>
            <div class="info-value">${data.pelanggan.nama}</div>
        </div>
        <div class="info-block">
            <div class="info-label">Tanggal</div>
            <div class="info-value">${data.tanggal}</div>
        </div>
        <div class="info-block">
            <div class="info-label">No. HP</div>
            <div class="info-value">${data.pelanggan.no_hp}</div>
        </div>
        <div class="info-block">
            <div class="info-label">Status Laundry</div>
            <div class="info-value">${data.status_laundry}</div>
        </div>
        <div class="info-block">
            <div class="info-label">Status Bayar</div>
            <div class="info-value">${data.status_pembayaran}</div>
        </div>
        <div class="info-block">
            <div class="info-label">Alamat</div>
            <div class="info-value" style="font-size:13px;font-weight:400;">${data.pelanggan.alamat}</div>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>Layanan</th>
                <th>Berat</th>
                <th>Harga Satuan</th>
                <th>Sub Total</th>
            </tr>
        </thead>
        <tbody>
            ${layananRows}
        </tbody>
    </table>

    <div class="summary">
        <div class="summary-box">
            <div class="summary-row">
                <span>Subtotal</span>
                <span>Rp ${formatNumber(data.subtotal)}</span>
            </div>
            <div class="summary-row discount">
                <span>Diskon</span>
                <span>- Rp ${formatNumber(data.discount)}</span>
            </div>
            <div class="summary-row grand-total">
                <span>Grand Total</span>
                <span>Rp ${formatNumber(data.total)}</span>
            </div>
        </div>
    </div>

    <div class="nota-footer">
        <p>Terima kasih telah mempercayakan laundry Anda kepada kami!</p>
        <p style="margin-top:4px;">— Smart Wash Laundry —</p>
    </div>

    <script>
        window.onload = function() {
            window.print();
            setTimeout(function() { window.close(); }, 800);
        };
    <\/script>
</body>
</html>`;

        const printWindow = window.open('', '_blank', 'width=800,height=700,scrollbars=yes');
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

