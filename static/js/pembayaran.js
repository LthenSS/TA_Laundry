document.addEventListener('DOMContentLoaded', function () {
    // Open payment modal and populate fields
    document.querySelectorAll('.btn-bayar').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var id = this.getAttribute('data-id');
            var kode = this.getAttribute('data-kode');
            var total = this.getAttribute('data-total');

            var payModalEl = document.getElementById('paymentModal');
            var payTransaksiId = document.getElementById('payTransaksiId');
            var payKode = document.getElementById('payKode');
            var payTotal = document.getElementById('payTotal');

            payTransaksiId.value = id;
            payKode.textContent = kode;
            payTotal.textContent = total ? formatCurrency(total) : '-';

            var modal = new bootstrap.Modal(payModalEl);
            modal.show();
        });
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
