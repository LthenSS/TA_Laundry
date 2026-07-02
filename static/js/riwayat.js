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

        // print button
        document.getElementById('printBtn').onclick = function () {
            window.print();
        };
    }

    function formatNumber(val) {
        try { return Number(val).toLocaleString('id-ID', {maximumFractionDigits:0}); } catch(e) { return val; }
    }
});
