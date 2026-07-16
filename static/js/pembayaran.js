document.addEventListener('DOMContentLoaded', function () {
    var payModalEl = document.getElementById('paymentModal');
    var payTransaksiId = document.getElementById('payTransaksiId');
    var payKode = document.getElementById('payKode');
    var payTotal = document.getElementById('payTotal');
    var payMetode = document.getElementById('payMetode');
    var qrisDetails = document.getElementById('qrisDetails');
    var qrisNote = document.getElementById('qrisNote');
    var qrisUrlContainer = document.getElementById('qrisUrlContainer');
    var qrisResponse = document.getElementById('qrisResponse');

    function resetQrisDetails() {
        qrisDetails.classList.add('d-none');
        qrisNote.textContent = '';
        qrisUrlContainer.innerHTML = '';
        qrisResponse.textContent = '';
    }

    function setQrisDetails(data) {
        qrisDetails.classList.remove('d-none');
        qrisNote.textContent = data.note || 'QRIS API respons siap.';
        qrisUrlContainer.innerHTML = '';
        if (data.qris_url) {
            if (data.qris_url.includes('qrserver') || data.qris_url.match(/\.(jpeg|jpg|gif|png)$/) != null) {
                qrisUrlContainer.innerHTML = '<div class="text-center mt-3 mb-3"><img src="' + data.qris_url + '" alt="QRIS" class="img-fluid border rounded shadow-sm" style="max-width: 250px; cursor: pointer;" title="Klik untuk simulasi sukses pembayaran" onclick="Swal.fire({icon:\'success\',title:\'Pembayaran Berhasil\',text:\'Pembayaran telah diterima.\',confirmButtonText:\'Lanjutkan\',confirmButtonColor:\'#28a745\'})"></div><p class="text-muted small text-center"><em>* Scan dengan kamera HP atau klik gambar QR di atas untuk simulasi pembayaran berhasil.</em></p>';
            } else {
                qrisUrlContainer.innerHTML = '<strong>Link QRIS:</strong> <a href="' + data.qris_url + '" target="_blank" rel="noopener noreferrer">' + data.qris_url + '</a>';
            }
        }
        if (data.provider_response) {
            try {
                qrisResponse.textContent = JSON.stringify(data.provider_response, null, 2);
            } catch (e) {
                qrisResponse.textContent = String(data.provider_response);
            }
        } else if (!data.qris_url) {
            qrisResponse.textContent = 'Tidak ada data QRIS tersedia.';
        }
    }

    function fetchQrisData(transaksiId) {
        if (!transaksiId) {
            return;
        }

        resetQrisDetails();
        qrisNote.textContent = 'Memuat data QRIS...';
        qrisDetails.classList.remove('d-none');

        fetch(qrisEndpointUrl + '?transaksi_id=' + encodeURIComponent(transaksiId), {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        }).then(function (response) {
            if (!response.ok) {
                throw new Error('Gagal memuat QRIS.');
            }
            return response.json();
        }).then(function (data) {
            if (data.success && data.qris) {
                setQrisDetails(data.qris);
            } else {
                setQrisDetails({ note: data.message || 'QRIS tidak tersedia.', provider_response: null });
            }
        }).catch(function (error) {
            qrisNote.textContent = 'Terjadi kesalahan saat memuat QRIS.';
            qrisResponse.textContent = error.message;
        });
    }

    // Open payment modal and populate fields
    document.querySelectorAll('.btn-bayar').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var id = this.getAttribute('data-id');
            var kode = this.getAttribute('data-kode');
            var total = this.getAttribute('data-total');

            payTransaksiId.value = id;
            payKode.textContent = kode;
            payTotal.textContent = total ? formatCurrency(total) : '-';
            payMetode.value = '';
            resetQrisDetails();

            var modal = new bootstrap.Modal(payModalEl);
            modal.show();
        });
    });

    payMetode.addEventListener('change', function () {
        if (this.value === 'QRIS') {
            fetchQrisData(payTransaksiId.value);
        } else {
            resetQrisDetails();
        }
    });

    // Show toast if server provided a message
    var toastTrigger = document.getElementById('payment-toast');
    if (toastTrigger) {
        var msg = toastTrigger.getAttribute('data-message');
        if (msg) {
            document.getElementById('paymentToastBody').textContent = msg;
            var toastEl = document.getElementById('paymentToast');
            var toast = new bootstrap.Toast(toastEl);
            toast.show();
        }
    }

    function formatCurrency(value) {
        try {
            var num = parseFloat(value);
            return 'Rp ' + num.toLocaleString('id-ID', {maximumFractionDigits:0});
        } catch (e) {
            return value;
        }
    }
});
