/**
 * Dapur Mamita — Cart Logic (Client-side enhancements)
 * Note: State utama keranjang tersimpan aman di server-side session Flask.
 * Script ini menangani feedback visual, badge animasi, dan konfirmasi.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Animasi tombol tambah ke keranjang
    const addForms = document.querySelectorAll('form[action*="/order/tambah"]');
    addForms.forEach(form => {
        form.addEventListener('submit', (e) => {
            const btn = form.querySelector('button[type="submit"]');
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status"></span> Menambah...';
            }
        });
    });

    // Animate badge cart bila ada perubahan
    const cartBadge = document.getElementById('cartBadge');
    if (cartBadge && cartBadge.textContent.trim() !== '') {
        cartBadge.classList.add('animate-bounce');
    }
});
