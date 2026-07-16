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
        const isMember = document.getElementById('newCustomerIsMember').checked;

        if (!name || !phone || !address) {
            showToast('Nama, Nomor HP, dan Alamat wajib diisi.');
            return;
        }

        const response = await fetch('/karyawan/api/pelanggan/tambah', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nama: name, no_hp: phone, alamat: address, is_member: isMember })
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

    function validateRedeemPoints(maxDiscount = 0) {
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
        if (maxDiscount > 0 && discount > maxDiscount) {
            const maxPoints = Math.floor(maxDiscount / 10000) * 20;
            redeemPointMessage.textContent = `Point terlalu banyak untuk subtotal ini. Maksimum ${maxPoints} point.`;
            redeemPointPreview.textContent = '';
            return { valid: false, points: 0, discount: 0 };
        }

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
        const subtotal = Number(data.subtotal || 0);
        const promoDiscount = Number(data.discount || 0);
        const addonTotal = calculateAddonTotal();
        const maxRedeemDiscount = Math.max(0, subtotal - promoDiscount);
        
        const redeemValidation = validateRedeemPoints(maxRedeemDiscount);
        const totalDiscount = promoDiscount + (redeemValidation.valid ? redeemValidation.discount : 0);
        const totalSubtotal = subtotal + addonTotal;
        const finalTotal = Math.max(0, totalSubtotal - totalDiscount);

        subtotalText.textContent = formatRupiah(totalSubtotal);
        discountText.textContent = `- ${formatRupiah(totalDiscount)}`;
        totalText.textContent = formatRupiah(finalTotal);
        promoName.textContent = data.promo ? `${data.promo.nama} (${data.promo.nilai})` : 'Tidak ada promo';

        const canSubmit = !!pelangganIdInput.value && !!layananSelect.value && (parseFloat(beratInput.value) || 0) > 0 && (!redeemPointCheckbox.checked || redeemValidation.valid);
        submitTransactionBtn.disabled = !canSubmit;
        if (!canSubmit && redeemPointCheckbox.checked) {
            submitTransactionBtn.textContent = 'Konfirmasi Pesanan';
        }

        const metodePembayaran = document.getElementById('metode_pembayaran');
        const statusPembayaran = document.getElementById('status_pembayaran');
        if (metodePembayaran && metodePembayaran.value === 'QRIS' && statusPembayaran && statusPembayaran.value === 'Lunas' && finalTotal > 0 && canSubmit) {
            generateQrisCode(finalTotal);
        } else {
            const qrisContainer = document.getElementById('qrisContainer');
            if (qrisContainer) qrisContainer.style.display = 'none';
        }
    }

    // ---- ADD-ON LOGIC ----
    function calculateAddonTotal() {
        let total = 0;
        document.querySelectorAll('.addon-checkbox:checked').forEach(cb => {
            const harga = parseFloat(cb.dataset.harga || 0);
            const addonId = cb.value;
            const qtyInput = document.querySelector(`.addon-qty[data-addon-id='${addonId}']`);
            const qty = qtyInput ? (parseInt(qtyInput.value) || 1) : 1;
            total += harga * qty;
        });
        const addonTotalEl = document.getElementById('addonTotal');
        if (addonTotalEl) addonTotalEl.textContent = formatRupiah(total);
        return total;
    }

    const addonSection = document.getElementById('addonSection');
    layananSelect.addEventListener('change', function() {
        if (addonSection) {
            addonSection.style.display = this.value ? 'block' : 'none';
        }
    });

    document.querySelectorAll('.addon-checkbox').forEach(cb => {
        cb.addEventListener('change', function() {
            const wrap = document.getElementById(`qty_wrap_${this.value}`);
            const card = this.closest('.addon-card');
            if (this.checked) {
                if (wrap) wrap.style.display = 'block';
                if (card) card.style.borderColor = '#f59e0b';
            } else {
                if (wrap) wrap.style.display = 'none';
                if (card) card.style.borderColor = '';
            }
            calculateAddonTotal();
            calculateTotals();
        });
    });

    document.querySelectorAll('.addon-qty').forEach(inp => {
        inp.addEventListener('input', function() {
            if (parseInt(this.value) < 1 || !this.value) this.value = 1;
            calculateAddonTotal();
            calculateTotals();
        });
    });

    async function generateQrisCode(amount) {
        const qrisContainer = document.getElementById('qrisContainer');
        const qrisImage = document.getElementById('qrisImage');
        const qrisLoading = document.getElementById('qrisLoading');
        
        if (!qrisContainer || !qrisImage || !qrisLoading) return;
        
        qrisContainer.style.display = 'block';
        qrisLoading.classList.remove('d-none');
        qrisImage.classList.add('d-none');
        
        try {
            const response = await fetch('/karyawan/api/qris/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ amount: amount })
            });
            const data = await response.json();
            if (data.success && data.qris_url) {
                qrisImage.src = data.qris_url;
                qrisImage.title = "Klik untuk simulasi sukses pembayaran";
                qrisImage.style.cursor = "pointer";
                qrisImage.onclick = function() {
                    Swal.fire({
                        icon: 'success',
                        title: 'Pembayaran Berhasil',
                        text: 'Pembayaran telah diterima.',
                        confirmButtonText: 'Lanjutkan',
                        confirmButtonColor: '#28a745'
                    });
                };
                // add instruction text
                if (!document.getElementById('qris-instruction')) {
                    const inst = document.createElement('p');
                    inst.id = 'qris-instruction';
                    inst.className = 'text-muted small mt-2';
                    inst.innerHTML = '<em>* Scan dengan kamera HP atau klik gambar QR di atas untuk simulasi pembayaran berhasil.</em>';
                    qrisContainer.appendChild(inst);
                }
                qrisImage.onload = () => {
                    qrisLoading.classList.add('d-none');
                    qrisImage.classList.remove('d-none');
                };
            } else {
                qrisContainer.style.display = 'none';
            }
        } catch (e) {
            qrisContainer.style.display = 'none';
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
        if (redeemPointCheckbox.checked && redeemPointMessage.textContent.includes('terlalu banyak')) {
            event.preventDefault();
            showToast(redeemPointMessage.textContent);
            return;
        }
        if (redeemPointCheckbox.checked && redeemPointMessage.textContent.includes('kelipatan 20')) {
            event.preventDefault();
            showToast(redeemPointMessage.textContent);
            return;
        }
        if (redeemPointCheckbox.checked && redeemPointMessage.textContent.includes('melebihi saldo')) {
            event.preventDefault();
            showToast(redeemPointMessage.textContent);
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
    layananSelect.addEventListener('change', calculateTotals); // also triggers addon visibility above
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
    
    const metodePembayaran = document.getElementById('metode_pembayaran');
    const statusPembayaran = document.getElementById('status_pembayaran');
    
    function checkQrisDisplay() {
        const finalTotalStr = totalText.textContent.replace(/[^0-9]/g, '');
        const finalTotal = parseInt(finalTotalStr, 10) || 0;
        const canSubmit = !submitTransactionBtn.disabled;
        
        if (metodePembayaran && metodePembayaran.value === 'QRIS' && statusPembayaran && statusPembayaran.value === 'Lunas' && finalTotal > 0 && canSubmit) {
            generateQrisCode(finalTotal);
        } else {
            const qrisContainer = document.getElementById('qrisContainer');
            if (qrisContainer) qrisContainer.style.display = 'none';
        }
    }
    
    if (metodePembayaran) {
        metodePembayaran.addEventListener('change', checkQrisDisplay);
    }
    if (statusPembayaran) {
        statusPembayaran.addEventListener('change', checkQrisDisplay);
    }

    newCustomerForm.addEventListener('submit', submitNewCustomer);
    transactionForm.addEventListener('submit', validateAndSubmit);
});