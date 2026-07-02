/* Dashboard Chart.js Configuration */

let revenueChart = null;
let transactionChart = null;

document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
});

function initializeCharts() {
    loadRevenueChart();
    loadTransactionChart();
}

function loadRevenueChart() {
    // Fetch revenue data from API
    fetch('/owner/api/revenue-by-month')
        .then(response => response.json())
        .then(data => {
            renderRevenueChart(data);
        })
        .catch(error => console.error('Error loading revenue data:', error));
}

function renderRevenueChart(data) {
    const ctx = document.getElementById('revenueChart').getContext('2d');
    
    if (revenueChart) {
        revenueChart.destroy();
    }
    
    revenueChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Pendapatan (Rp)',
                data: data.data,
                borderColor: '#1f6fbd',
                backgroundColor: 'rgba(31, 111, 189, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 5,
                pointBackgroundColor: '#1f6fbd',
                pointBorderColor: 'white',
                pointBorderWidth: 2,
                pointHoverRadius: 7,
                pointHoverBackgroundColor: '#1f6fbd'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        font: {
                            size: 12,
                            weight: '500'
                        },
                        color: '#17212b',
                        usePointStyle: true,
                        padding: 15
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: { size: 13, weight: '600' },
                    bodyFont: { size: 12 },
                    cornerRadius: 6,
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += 'Rp ' + formatCurrency(context.parsed.y);
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: '#e9ecef',
                        drawBorder: false
                    },
                    ticks: {
                        font: { size: 12 },
                        color: '#6f7d8a',
                        callback: function(value) {
                            return 'Rp ' + formatCurrency(value);
                        }
                    }
                },
                x: {
                    grid: {
                        display: false,
                        drawBorder: false
                    },
                    ticks: {
                        font: { size: 12 },
                        color: '#6f7d8a'
                    }
                }
            }
        }
    });
}

function loadTransactionChart() {
    // Fetch transaction data from API
    fetch('/owner/api/transactions-by-day')
        .then(response => response.json())
        .then(data => {
            renderTransactionChart(data);
        })
        .catch(error => console.error('Error loading transaction data:', error));
}

function renderTransactionChart(data) {
    const ctx = document.getElementById('transactionChart').getContext('2d');
    
    if (transactionChart) {
        transactionChart.destroy();
    }
    
    transactionChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Jumlah Transaksi',
                data: data.data,
                backgroundColor: [
                    'rgba(31, 111, 189, 0.8)',
                    'rgba(31, 111, 189, 0.8)',
                    'rgba(31, 111, 189, 0.8)',
                    'rgba(31, 111, 189, 0.8)',
                    'rgba(31, 111, 189, 0.8)',
                    'rgba(31, 111, 189, 0.9)',
                    'rgba(242, 176, 27, 0.8)'
                ],
                borderColor: [
                    '#1f6fbd',
                    '#1f6fbd',
                    '#1f6fbd',
                    '#1f6fbd',
                    '#1f6fbd',
                    '#1f6fbd',
                    '#f2b01b'
                ],
                borderWidth: 2,
                borderRadius: 6,
                borderSkipped: false,
                barPercentage: 0.7,
                categoryPercentage: 0.8
            }]
        },
        options: {
            indexAxis: undefined,
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        font: {
                            size: 12,
                            weight: '500'
                        },
                        color: '#17212b',
                        usePointStyle: true,
                        padding: 15
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    padding: 12,
                    titleFont: { size: 13, weight: '600' },
                    bodyFont: { size: 12 },
                    cornerRadius: 6,
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.parsed.y + ' transaksi';
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: '#e9ecef',
                        drawBorder: false
                    },
                    ticks: {
                        font: { size: 12 },
                        color: '#6f7d8a',
                        stepSize: 1
                    }
                },
                x: {
                    grid: {
                        display: false,
                        drawBorder: false
                    },
                    ticks: {
                        font: { size: 12 },
                        color: '#6f7d8a'
                    }
                }
            }
        }
    });
}

function formatCurrency(value) {
    if (value >= 1000000) {
        return (value / 1000000).toFixed(1) + 'M';
    } else if (value >= 1000) {
        return (value / 1000).toFixed(0) + 'K';
    }
    return value.toFixed(0);
}
