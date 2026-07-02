document.addEventListener('DOMContentLoaded', () => {
    const customerSearch = document.getElementById('customerSearch');
    const customerSuggestions = document.getElementById('customerSuggestions');
    const customerInfo = document.getElementById('customerInfo');
    const selectedCustomerName = document.getElementById('selectedCustomerName');
    const selectedCustomerPhone = document.getElementById('selectedCustomerPhone');
    const selectedCustomerType = document.getElementById('selectedCustomerType');
    const selectedCustomerPoint = document.getElementById('selectedCustomerPoint');
    const selectedCustomerLastTransaction = document.getElementById('selectedCustomerLastTransaction');
    const pelangganIdInput = document.getElementById('pelanggan_id');
    const beratInput = document.getElementById('berat');
    const layananSelect = document.getElementById('layanan_id');
    const servicePrice = document.getElementById('servicePrice');
    const serviceEstimate = document.getElementById('serviceEstimate');
    const promoName = document.getElementById('promoName');
    const subtotalText = document.getElementById('subtotalText');
    const discountText = document.getElementById('discountText');
    const totalText = document.getElementById('totalText');
    const transactionForm = document.getElementById('transactionForm');
    const redeemPointSection = document.getElementById('redeemPointSection');
    const redeemPointCheckbox = document.getElementById('use_redeem');
    const redeemPointInput = document.getElementById('redeem_point');
    const redeemPointCount = document.getElementById('redeemPointCount');
    const redeemPointMessage = document.getElementById('redeemPointMessage');
    const redeemPointPreview = document.getElementById('redeemPointPreview');
    const submitTransactionBtn = document.getElementById('submitTransactionBtn');
    const newCustomerForm = document.getElementById('newCustomerForm');

    let selectedCustomer = null;

    setRedeemPointInputState();

    function formatRupiah(number) {
        return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', maximumFractionDigits: 0 }).format(number);
    }

    function debounce(fn, delay = 300) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => fn.apply(this, args), delay);
        };
    }

    async function searchCustomers(query) {
        if (!query) {
            customerSuggestions.innerHTML = '';
            return;
        }

        const response = await fetch(`/karyawan/api/pelanggan?q=${encodeURIComponent(query)}`);
        if (!response.ok) {
            return;
        }

        const data = await response.json();
        customerSuggestions.innerHTML = '';

        if (!data || data.length === 0) {
            const noneItem = document.createElement('div');
            noneItem.className = 'list-group-item d-flex align-items-center justify-content-between gap-3';
            noneItem.innerHTML = '<span>Pelanggan tidak ditemukan.</span><button type="button" class="btn btn-sm btn-primary">Tambah Pelanggan Baru</button>';
            noneItem.querySelector('button').addEventListener('click', () => {
                const modal = new bootstrap.Modal(document.getElementById('newCustomerModal'));
                modal.show();
            });
            customerSuggestions.appendChild(noneItem);
            return;
        }

        data.forEach(customer => {
            const item = document.createElement('button');
            item.type = 'button';
            item.className = 'list-group-item list-group-item-action';
            const badgeClass = customer.is_member ? 'bg-success' : 'bg-secondary';
            item.innerHTML = `
                <div class="d-flex justify-content-between gap-3">
                    <div>
                        <strong>${customer.nama}</strong><br>
                        <small>${customer.no_hp}</small>
                    </div>
                    <div class="text-end">
                        <span class="badge ${badgeClass}">${customer.jenis_pelanggan}</span><br>
                        <small>Point : ${customer.total_point}</small>
                    </div>
                </div>
            `;
            item.addEventListener('click', () => selectCustomer(customer));
            customerSuggestions.appendChild(item);
        });
    }

    function setRedeemPointInputState() {
        const isSelectableMember = !!selectedCustomer?.is_member;
        const canUseRedeem = isSelectableMember && redeemPointCheckbox.checked && !redeemPointCheckbox.disabled;

        redeemPointInput.disabled = !canUseRedeem;
        redeemPointInput.readOnly = !canUseRedeem;
        redeemPointInput.removeAttribute('aria-disabled');
        redeemPointInput.setAttribute('aria-disabled', String(!canUseRedeem));
        redeemPointInput.classList.toggle('is-invalid', false);

        if (!canUseRedeem) {
            redeemPointInput.value = '0';
            redeemPointMessage.textContent = '';
            redeemPointPreview.textContent = '';
        }
    }

    function selectCustomer(customer) {
        selectedCustomer = customer;
        pelangganIdInput.value = customer.id_pelanggan;
        selectedCustomerName.textContent = customer.nama;
        selectedCustomerPhone.textContent = customer.no_hp;
        selectedCustomerType.textContent = customer.jenis_pelanggan;
        selectedCustomerPoint.textContent = `${customer.total_point} Poin`;
        selectedCustomerLastTransaction.textContent = customer.last_transaction_date || '-';
        
        if (customer.is_member) {
            redeemPointSection.style.display = 'block';
            redeemPointCheckbox.disabled = false;
            redeemPointCheckbox.checked = false;
            redeemPointCount.textContent = customer.total_point;
            redeemPointMessage.textContent = '';
            redeemPointPreview.textContent = '';
        } else {
            redeemPointSection.style.display = 'none';
            redeemPointCheckbox.checked = false;
            redeemPointCheckbox.disabled = true;
            redeemPointMessage.textContent = '';
            redeemPointPreview.textContent = '';
        }

        setRedeemPointInputState();
        
        customerInfo.style.display = 'block';
        customerSuggestions.innerHTML = '';
        customerSearch.value = `${customer.nama} (${customer.no_hp})`;
        calculateTotals();
    }

    const toastElement = document.getElementById('transaksiToast');
    const toastBody = document.getElementById('transaksiToastBody');
    const toastInstance = toastElement && window.bootstrap?.Toast ? new window.bootstrap.Toast(toastElement) : null;

    function showToast(message) {
        if (!toastInstance || !toastBody) {
            window.alert(message);
            return;
        }
        toastBody.textContent = message;
        toastInstance.show();
    }

    async function submitNewCustomer(event) {
        event.preventDefault();

        const name = document.getElementById('newCustomerName').value.trim();
        const phone = document.getElementById('newCustomerPhone').value.trim();
        const address = document.getElementById('newCustomerAddress').value.trim();

        if (!name || !phone || !address) {
            showToast('Nama, Nomor HP, dan Alamat wajib diisi.');
            return;
        }

        const response = await fetch('/karyawan/api/pelanggan/tambah', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nama: name, no_hp: phone, alamat: address })
        });

        const data = await response.json();
        if (!response.ok) {
            showToast(data.error || 'Gagal menyimpan pelanggan.');
            return;
        }

        selectCustomer(data);
        const modal = bootstrap.Modal.getInstance(document.getElementById('newCustomerModal'));
        modal.hide();
        newCustomerForm.reset();
        showToast('Pelanggan baru berhasil ditambahkan.');
    }

    function validateRedeemPoints() {
        if (!selectedCustomer?.is_member || !redeemPointCheckbox.checked) {
            redeemPointMessage.textContent = '';
            redeemPointPreview.textContent = '';
            return { valid: true, points: 0, discount: 0 };
        }

        const availablePoints = Number(selectedCustomer.total_point || 0);
        const redeemPoints = parseInt(redeemPointInput.value || '0', 10);

        if (!Number.isInteger(redeemPoints) || redeemPoints < 0) {
            redeemPointMessage.textContent = 'Point harus kelipatan 20.';
            redeemPointPreview.textContent = '';
            return { valid: false, points: 0, discount: 0 };
        }

        if (redeemPoints < 20) {
            redeemPointMessage.textContent = 'Minimal redeem adalah 20 point.';
            redeemPointPreview.textContent = '';
            return { valid: false, points: 0, discount: 0 };
        }

        if (redeemPoints > availablePoints) {
            redeemPointMessage.textContent = 'Point yang digunakan melebihi saldo.';
            redeemPointPreview.textContent = '';
            return { valid: false, points: 0, discount: 0 };
        }

        if (redeemPoints % 20 !== 0) {
            redeemPointMessage.textContent = 'Point harus kelipatan 20.';
            redeemPointPreview.textContent = '';
            return { valid: false, points: 0, discount: 0 };
        }

        const discount = (redeemPoints / 20) * 10000;
        redeemPointMessage.textContent = `Redeem ${redeemPoints} poin akan mengurangi total.`;
        redeemPointPreview.textContent = `Diskon redeem: ${formatRupiah(discount)}`;
        return { valid: true, points: redeemPoints, discount };
    }

    async function calculateTotals() {
        const selectedOption = layananSelect.options[layananSelect.selectedIndex];
        const estimasi = selectedOption?.dataset?.estimasi;
        const harga = Number(selectedOption?.dataset?.harga || 0);

        servicePrice.textContent = formatRupiah(harga);
        serviceEstimate.textContent = estimasi ? `${estimasi} Hari` : '-';

        const response = await fetch('/karyawan/api/transaksi/hitung', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ layanan_id: layananSelect.value, berat: beratInput.value || '0' })
        });

        if (!response.ok) {
            subtotalText.textContent = 'Rp 0';
            discountText.textContent = '- Rp 0';
            totalText.textContent = 'Rp 0';
            promoName.textContent = 'Tidak ada promo';
            return;
        }

        const data = await response.json();
        const redeemValidation = validateRedeemPoints();
        const subtotal = Number(data.subtotal || 0);
        const promoDiscount = Number(data.discount || 0);
        const totalDiscount = promoDiscount + (redeemValidation.valid ? redeemValidation.discount : 0);
        const finalTotal = Math.max(0, subtotal - totalDiscount);

        subtotalText.textContent = formatRupiah(subtotal);
        discountText.textContent = `- ${formatRupiah(totalDiscount)}`;
        totalText.textContent = formatRupiah(finalTotal);
        promoName.textContent = data.promo ? `${data.promo.nama} (${data.promo.nilai})` : 'Tidak ada promo';

        const canSubmit = !!pelangganIdInput.value && !!layananSelect.value && (parseFloat(beratInput.value) || 0) > 0 && (!redeemPointCheckbox.checked || redeemValidation.valid);
        submitTransactionBtn.disabled = !canSubmit;
        if (!canSubmit && redeemPointCheckbox.checked) {
            submitTransactionBtn.textContent = 'Konfirmasi Pesanan';
        }
    }

    function validateAndSubmit(event) {
        if (!pelangganIdInput.value) {
            event.preventDefault();
            showToast('Pilih pelanggan terlebih dahulu.');
            return;
        }
        if (!layananSelect.value) {
            event.preventDefault();
            showToast('Pilih layanan laundry terlebih dahulu.');
            return;
        }
        if ((parseFloat(beratInput.value) || 0) <= 0) {
            event.preventDefault();
            showToast('Berat harus lebih dari 0 kg.');
            return;
        }
        const redeemValidation = validateRedeemPoints();
        if (redeemPointCheckbox.checked && !redeemValidation.valid) {
            event.preventDefault();
            showToast(redeemPointMessage.textContent || 'Redeem poin tidak valid.');
            return;
        }
        submitTransactionBtn.disabled = true;
        submitTransactionBtn.textContent = 'Menyimpan...';
    }

    customerSearch.addEventListener('input', debounce(() => {
        const query = customerSearch.value.trim();
        searchCustomers(query);
    }));
    beratInput.addEventListener('input', calculateTotals);
    layananSelect.addEventListener('change', calculateTotals);
    redeemPointCheckbox.addEventListener('change', () => {
        setRedeemPointInputState();
        if (redeemPointCheckbox.checked) {
            redeemPointInput.focus();
        }
        calculateTotals();
    });
    redeemPointInput.addEventListener('input', () => {
        redeemPointInput.value = redeemPointInput.value.replace(/[^0-9]/g, '');
        calculateTotals();
    });
    newCustomerForm.addEventListener('submit', submitNewCustomer);
    transactionForm.addEventListener('submit', validateAndSubmit);
});