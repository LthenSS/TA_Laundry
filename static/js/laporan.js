// LAPORAN (REPORTING) PAGE SCRIPTS

document.addEventListener('DOMContentLoaded', function() {
    setupFilterHandlers();
    setupSearchHandler();
    setupSortHandlers();
    renderCharts();
    setupExportHandlers();
});

/**
 * Setup filter radio button handlers
 */
function setupFilterHandlers() {
    const filterOptions = document.querySelectorAll('input[name="filter"]');
    const customDateRange = document.getElementById('custom-date-range');
    const customDateRangeEnd = document.getElementById('custom-date-range-end');
    const applyFilterBtn = document.getElementById('apply-filter');

    filterOptions.forEach(option => {
        option.addEventListener('change', function() {
            const isCustom = this.value === 'custom';
            customDateRange.style.display = isCustom ? 'block' : 'none';
            customDateRangeEnd.style.display = isCustom ? 'block' : 'none';
        });
    });

    applyFilterBtn.addEventListener('click', function() {
        const selectedFilter = document.querySelector('input[name="filter"]:checked').value;
        let url = `${window.location.pathname}?filter=${selectedFilter}`;

        if (selectedFilter === 'custom') {
            const startDate = document.getElementById('start-date').value;
            const endDate = document.getElementById('end-date').value;
            
            if (!startDate || !endDate) {
                alert('Silakan pilih tanggal mulai dan tanggal akhir untuk filter custom');
                return;
            }
            
            url += `&start=${startDate}&end=${endDate}`;
        }

        // Get search and sort parameters
        const searchInput = document.getElementById('search-input');
        if (searchInput && searchInput.value) {
            url += `&search=${encodeURIComponent(searchInput.value)}`;
        }

        window.location.href = url;
    });
}

/**
 * Setup search handler
 */
function setupSearchHandler() {
    const searchInput = document.getElementById('search-input');
    
    if (searchInput) {
        searchInput.addEventListener('keyup', debounce(function() {
            const query = this.value.trim();
            let url = window.location.pathname + '?';
            
            // Add existing filter
            const selectedFilter = document.querySelector('input[name="filter"]:checked').value;
            url += `filter=${selectedFilter}`;
            
            if (query) {
                url += `&search=${encodeURIComponent(query)}`;
            }
            
            window.location.href = url;
        }, 500));
    }
}

/**
 * Setup sort link handlers
 */
function setupSortHandlers() {
    const sortLinks = document.querySelectorAll('.sort-link');
    
    sortLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const sortBy = this.dataset.sort;
            const selectedFilter = document.querySelector('input[name="filter"]:checked').value;
            const searchInput = document.getElementById('search-input');
            
            let url = `${window.location.pathname}?filter=${selectedFilter}&sort=${sortBy}`;
            
            if (searchInput && searchInput.value) {
                url += `&search=${encodeURIComponent(searchInput.value)}`;
            }
            
            window.location.href = url;
        });
    });
}

/**
 * Render Chart.js charts
 */
function renderCharts() {
    renderMemberChart();
    renderRevenueChart();
    renderTransactionChart();
}

/**
 * Member vs Non-Member Pie Chart
 */
function renderMemberChart() {
    const memberChartCanvas = document.getElementById('memberChart');
    if (!memberChartCanvas) return;

    // Extract member/non-member counts from container data attributes
    const container = document.querySelector('.laporan-container');
    const memberCount = parseInt(container?.dataset.memberCount || 0);
    const nonMemberCount = parseInt(container?.dataset.nonMemberCount || 0);

    // If both are 0, show placeholder
    const ctx = memberChartCanvas.getContext('2d');
    const chartData = memberCount + nonMemberCount > 0 
        ? {
            labels: ['Member', 'Non-Member'],
            datasets: [{
                data: [memberCount, nonMemberCount],
                backgroundColor: ['#198754', '#6c757d'],
                borderColor: ['#146c43', '#545b62'],
                borderWidth: 2
            }]
        }
        : {
            labels: ['Tidak ada data'],
            datasets: [{
                data: [1],
                backgroundColor: ['#e9ecef'],
                borderColor: ['#dee2e6'],
                borderWidth: 1
            }]
        };

    new Chart(ctx, {
        type: 'doughnut',
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

/**
 * Revenue by Month Bar Chart
 */
function renderRevenueChart() {
    const revenueChartCanvas = document.getElementById('revenueChart');
    if (!revenueChartCanvas) return;

    // Placeholder data - in production, this would come from AJAX
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'];
    const currentMonth = new Date().getMonth();
    const revenueData = Array(currentMonth + 1).fill(0).map(() => Math.floor(Math.random() * 5000000) + 1000000);

    const ctx = revenueChartCanvas.getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: months.slice(0, currentMonth + 1),
            datasets: [{
                label: 'Pendapatan (Rp)',
                data: revenueData,
                backgroundColor: '#0d6efd',
                borderColor: '#0b5ed7',
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            indexAxis: 'x',
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return 'Rp ' + (value / 1000000).toFixed(1) + 'M';
                        }
                    }
                }
            }
        }
    });
}

/**
 * Transactions by Day Line Chart
 */
function renderTransactionChart() {
    const transactionChartCanvas = document.getElementById('transactionChart');
    if (!transactionChartCanvas) return;

    const days = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu'];
    const today = new Date();
    const dayOfWeek = today.getDay();
    const relevantDays = days.slice(0, dayOfWeek === 0 ? 7 : dayOfWeek);
    
    // Placeholder data
    const transactionData = relevantDays.map(() => Math.floor(Math.random() * 50) + 5);

    const ctx = transactionChartCanvas.getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: relevantDays,
            datasets: [{
                label: 'Jumlah Transaksi',
                data: transactionData,
                borderColor: '#198754',
                backgroundColor: 'rgba(25, 135, 84, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#198754',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 10
                    }
                }
            }
        }
    });
}

/**
 * Setup print and PDF export handlers
 */
function setupExportHandlers() {
    const printBtn = document.getElementById('print-btn');
    const exportBtn = document.getElementById('export-btn');

    if (printBtn) {
        printBtn.addEventListener('click', function() {
            window.print();
        });
    }

    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            // Build export URL with current filter parameters
            const selectedFilter = document.querySelector('input[name="filter"]:checked').value;
            const searchInput = document.getElementById('search-input');
            
            let url = `/laporan/export?filter=${selectedFilter}`;
            
            const currentUrl = new URL(window.location.href);
            const sortParam = currentUrl.searchParams.get('sort');
            if (sortParam) {
                url += `&sort=${encodeURIComponent(sortParam)}`;
            }
            
            // Add custom date range if applicable
            if (selectedFilter === 'custom') {
                const startDate = document.getElementById('start-date').value;
                const endDate = document.getElementById('end-date').value;
                if (startDate && endDate) {
                    url += `&start=${startDate}&end=${endDate}`;
                } else {
                    alert('Silakan pilih tanggal mulai dan tanggal akhir untuk export');
                    return;
                }
            }
            
            // Add search parameter if present
            if (searchInput && searchInput.value) {
                url += `&search=${encodeURIComponent(searchInput.value)}`;
            }
            
            // Trigger download
            window.location.href = url;
        });
    }
}

/**
 * Utility function to debounce search input
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func.apply(this, args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
