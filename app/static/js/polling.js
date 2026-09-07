/**
 * Dapur Mamita — Polling Status Pesanan Customer
 * Auto-refresh via JS fetch() setiap 5 detik tanpa websocket
 */

document.addEventListener('DOMContentLoaded', () => {
    if (typeof POLL_URL === 'undefined') return;

    let currentStatus = null;
    let pollInterval = null;

    function updateProgressSteps(status) {
        const steps = document.querySelectorAll('.status-step');
        const lines = document.querySelectorAll('.status-line');

        // Reset
        steps.forEach(s => s.classList.remove('active'));
        lines.forEach(l => l.classList.remove('active'));

        if (status === 'menunggu') {
            if (steps[0]) steps[0].classList.add('active');
        } else if (status === 'diproses') {
            if (steps[0]) steps[0].classList.add('active');
            if (lines[0]) lines[0].classList.add('active');
            if (steps[1]) steps[1].classList.add('active');
        } else if (status === 'selesai') {
            steps.forEach(s => s.classList.add('active'));
            lines.forEach(l => l.classList.add('active'));
        }
    }

    function checkOrderStatus() {
        const pollingStatus = document.getElementById('pollingStatus');
        if (pollingStatus) {
            pollingStatus.innerHTML = '<i class="bi bi-arrow-repeat spin-slow me-1"></i> Memeriksa status terbaru...';
        }

        fetch(POLL_URL, {
            headers: {
                'Accept': 'application/json'
            }
        })
        .then(response => {
            if (response.status === 403) {
                throw new Error('Akses ditolak');
            }
            if (!response.ok) {
                throw new Error('Pesanan tidak ditemukan');
            }
            return response.json();
        })
        .then(data => {
            const labelElem = document.getElementById('statusLabel');
            const badgeElem = document.getElementById('statusBadge');

            if (labelElem && badgeElem) {
                // Periksa apakah status berubah
                if (currentStatus !== null && currentStatus !== data.status) {
                    // Beri efek highlight
                    badgeElem.classList.add('animate-pulse');
                    setTimeout(() => badgeElem.classList.remove('animate-pulse'), 1500);
                }

                currentStatus = data.status;
                labelElem.textContent = data.status_label;

                // Update warna badge
                badgeElem.className = `badge bg-${data.status_color} fs-5 px-4 py-2`;

                // Update icon
                let iconHtml = '';
                if (data.status === 'menunggu') {
                    iconHtml = '<i class="bi bi-hourglass-split me-1"></i>';
                } else if (data.status === 'diproses') {
                    iconHtml = '<i class="bi bi-fire me-1"></i>';
                } else if (data.status === 'selesai') {
                    iconHtml = '<i class="bi bi-check-circle-fill me-1"></i>';
                } else if (data.status === 'dibatalkan') {
                    iconHtml = '<i class="bi bi-x-circle-fill me-1"></i>';
                }
                badgeElem.innerHTML = iconHtml + `<span id="statusLabel">${data.status_label}</span>`;

                // Update visual progress stepper
                updateProgressSteps(data.status);

                if (pollingStatus) {
                    if (data.status === 'selesai') {
                        pollingStatus.innerHTML = '<i class="bi bi-check-circle-fill text-success me-1"></i> Pesanan selesai diantar. Selamat menikmati!';
                        if (pollInterval) clearInterval(pollInterval);
                    } else if (data.status === 'dibatalkan') {
                        pollingStatus.innerHTML = '<i class="bi bi-x-circle-fill text-danger me-1"></i> Pesanan telah dibatalkan.';
                        if (pollInterval) clearInterval(pollInterval);
                    } else {
                        pollingStatus.innerHTML = '<i class="bi bi-arrow-repeat spin-slow me-1"></i> Status otomatis diperbarui setiap beberapa detik...';
                    }
                }
            }
        })
        .catch(err => {
            console.error('Gagal polling status:', err);
            if (pollingStatus) {
                pollingStatus.innerHTML = '<span class="text-muted"><i class="bi bi-wifi-off me-1"></i> Gagal terhubung ke server...</span>';
            }
        });
    }

    // Polling pertama kali dijalankan 3 detik setelah halaman load, lalu tiap 6 detik
    setTimeout(() => {
        checkOrderStatus();
        pollInterval = setInterval(checkOrderStatus, 6000);
    }, 3000);
});
