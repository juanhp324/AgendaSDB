// --- CSRF Fetch Wrapper ---
const originalFetch = window.fetch;
window.fetch = function(url, options = {}) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    const method = (options.method || 'GET').toUpperCase();
    
    // Solo agregar el header en métodos que cambian el estado
    if (csrfToken && ['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
        options.headers = options.headers || {};
        // No sobrescribir si ya existe (para evitar conflictos con headers manuales)
        if (!options.headers['X-CSRF-Token']) {
            options.headers['X-CSRF-Token'] = csrfToken;
        }
    }
    return originalFetch(url, options);
};

// --- Global Notification (Toast) System (Powered by Toastify-js) ---
function showToast(message, type = 'success') {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    
    // Icon mapping
    const iconMap = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
    };

    // Modern colors matching our design system
    const colorMap = {
        success: '#10b981', // Emerald
        error: '#ef4444',   // Rose/Red
        warning: '#f59e0b', // Amber
        info: '#3b82f6'     // Blue
    };

    Toastify({
        text: `${iconMap[type] || '•'}  ${message}`,
        duration: 4000,
        gravity: "top", // Moved to top
        position: "right",
        close: true, // Allow manual closing
        stopOnFocus: true,
        style: {
            background: isDark ? "rgba(30, 41, 59, 0.95)" : "rgba(255, 255, 255, 0.95)",
            color: isDark ? "#f1f5f9" : "#0f172a",
            backdropFilter: "blur(12px)",
            borderLeft: `6px solid ${colorMap[type] || colorMap.success}`,
            boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.2), 0 10px 10px -5px rgba(0, 0, 0, 0.1)",
            borderRadius: "16px",
            padding: "16px 24px",
            fontSize: "1rem",
            fontWeight: "700",
            fontFamily: "'Plus Jakarta Sans', sans-serif"
        }
    }).showToast();
}

// --- Global Body Scroll Lock ---
function toggleBodyScroll() {
    const anyActive = !!document.querySelector('.modal-overlay.active');
    if (anyActive) {
        document.body.classList.add('modal-open');
        document.documentElement.classList.add('modal-open');
    } else {
        document.body.classList.remove('modal-open');
        document.documentElement.classList.remove('modal-open');
    }
}

// --- Global Status Modal (Animated) ---
// Note: We could use Swal for this but keeping it for now as a lightweight loader
function showStatusModal(type, title, message) {
    const modal = document.getElementById('statusModal');
    const content = document.getElementById('statusContent');
    if (!modal || !content) return;

    let iconHtml = '';
    if (type === 'saving') {
        iconHtml = '<div class="loader-ring"></div>';
    } else if (type === 'deleting') {
        iconHtml = '<div class="pulse-icon" style="color:var(--danger); background:var(--danger-light);">✕</div>';
    } else if (type === 'success') {
        iconHtml = '<div class="pulse-icon" style="color:var(--success); background:var(--success-light);">✓</div>';
    }

    content.innerHTML = `
        ${iconHtml}
        <h2 style="margin:0; font-size:1.5rem; font-weight:800; color:var(--text);">${title}</h2>
        ${message ? `<p style="margin:0; color:var(--text-2); font-weight:500;">${message}</p>` : ''}
    `;

    modal.classList.add('active');
    toggleBodyScroll();
}

function closeStatusModal() {
    const modal = document.getElementById('statusModal');
    if (modal) {
        modal.classList.remove('active');
        toggleBodyScroll();
    }
}

// --- Global Confirm Modal (Powered by SweetAlert2) ---
function showConfirmModal(title, message, onConfirm, btnType = 'primary') {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    
    Swal.fire({
        title: title,
        text: message,
        icon: btnType === 'danger' ? 'warning' : 'question',
        target: 'body',
        showCancelButton: true,
        confirmButtonColor: btnType === 'danger' ? '#ef4444' : '#DC1E46',
        cancelButtonColor: isDark ? '#334155' : '#94a3b8',
        confirmButtonText: 'Sí, continuar',
        cancelButtonText: 'Cancelar',
        background: isDark ? '#1e293b' : '#ffffff',
        color: isDark ? '#f1f5f9' : '#0f172a',
        borderRadius: '24px',
        padding: '2.5rem',
        reverseButtons: true, // Accessibility/Flow best practice
        showClass: {
            popup: 'animate__animated animate__fadeInUp animate__faster'
        },
        hideClass: {
            popup: 'animate__animated animate__fadeOutDown animate__faster'
        },
        customClass: {
            popup: 'premium-swal-popup',
            title: 'premium-swal-title',
            htmlContainer: 'premium-swal-content',
            confirmButton: 'premium-swal-confirm',
            cancelButton: 'premium-swal-cancel'
        }
    }).then((result) => {
        if (result.isConfirmed && onConfirm) {
            onConfirm();
        }
    });
}

// --- Dropbox / User Menu ---
function toggleUserMenu() {
    const dropdown = document.getElementById('userDropdown');
    const btn = document.getElementById('userMenuBtn');
    
    if (!dropdown || !btn) return;
    
    const isOpen = dropdown.classList.contains('open');
    
    if (isOpen) {
        dropdown.classList.remove('open');
        btn.removeAttribute('data-open');
    } else {
        dropdown.classList.add('open');
        btn.setAttribute('data-open', 'true');
    }
}

// Close dropdown when clicking outside
window.addEventListener('click', (e) => {
    const dropdown = document.getElementById('userDropdown');
    const btn = document.getElementById('userMenuBtn');
    
    if (dropdown && btn && !btn.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.classList.remove('open');
        btn.removeAttribute('data-open');
    }
});

// --- Profile Modal & Logic ---
async function openPerfilModal() {
    const modal = document.getElementById('perfilModal');
    if (!modal) return;
    
    try {
        const res = await fetch('/get_perfil');
        const data = await res.json();
        if (data.success) {
            document.getElementById('perfil_nombre').value = data.usuario.nombre || '';
            document.getElementById('perfil_email').value = data.usuario.email || '';
            document.getElementById('perfil_user').value = data.usuario.user || '';
            document.getElementById('perfil_rol').value = data.usuario.rol || '';
            document.getElementById('perfil_password').value = '';
            const twofa = data.usuario['2fa_enabled'] || false;
            document.getElementById('twofa-badge').textContent = twofa ? 'Activado' : 'Desactivado';
            document.getElementById('twofa-badge').style.background = twofa ? '#dcfce7' : '#fee2e2';
            document.getElementById('twofa-badge').style.color = twofa ? '#16a34a' : '#dc2626';
            document.getElementById('twofa-off-view').style.display = twofa ? 'none' : '';
            document.getElementById('twofa-on-view').style.display = twofa ? '' : 'none';
            document.getElementById('twofa-setup-view').style.display = 'none';
            loadTrustedDevices();
            modal.classList.add('active');
            toggleBodyScroll();
            document.getElementById('userDropdown').classList.remove('open');
            document.getElementById('userMenuBtn').removeAttribute('data-open');
        } else {
            showToast('No pudimos cargar tu perfil: ' + (data.message || 'Error del servidor'), 'error');
        }
    } catch (err) {
        showToast("Error de red al intentar abrir el perfil.", "error");
    }
}

function closePerfilModal(e) {
    const modal = document.getElementById('perfilModal');
    if (!modal) return;
    if (e && e.target !== modal && !e.target.classList.contains('modal-close') && !e.target.classList.contains('btn-ghost')) return;
    modal.classList.remove('active');
    toggleBodyScroll();
}

async function guardarPerfil() {
    const nombre = document.getElementById('perfil_nombre').value;
    const email = document.getElementById('perfil_email').value;
    const user = document.getElementById('perfil_user').value;
    const password = document.getElementById('perfil_password').value;
    
    showStatusModal('saving', 'Actualizando tu perfil...');

    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
        const res = await fetch('/update_perfil', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
            body: JSON.stringify({ nombre, email, user, password })
        });
        
        const data = await res.json();
        if (data.success) {
            showToast('Perfil actualizado con éxito', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            closeStatusModal();
            showToast(data.message || 'Error al actualizar perfil', 'error');
        }
    } catch (err) {
        closeStatusModal();
        showToast('Error de conexión', 'error');
    }
}

// ── Trusted Devices ──
async function loadTrustedDevices() {
    const list = document.getElementById('trusted-devices-list');
    const btnAll = document.getElementById('btn-revoke-all-td');
    if (!list) return;
    try {
        const res = await fetch('/perfil/trusted-devices');
        const data = await res.json();
        if (!data.success) { list.innerHTML = '<span>Error al cargar dispositivos.</span>'; return; }
        if (data.devices.length === 0) {
            list.innerHTML = '<span>No hay dispositivos de confianza activos.</span>';
            if (btnAll) btnAll.style.display = 'none';
        } else {
            list.innerHTML = data.devices.map(d => `
                <div style="display:flex;align-items:center;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--border,#f1f5f9)">
                  <div><strong>${d.device_name}</strong><br>
                    <span style="color:var(--text-muted,#94a3b8)">${d.ip} &nbsp;·&nbsp; Creado ${d.created_at} &nbsp;·&nbsp; Expira ${d.expires_at}</span>
                  </div>
                  <button onclick="revokeTrustedDevice('${d.id}')" class="btn btn-ghost" style="font-size:0.75rem;padding:2px 8px">✕</button>
                </div>`).join('');
            if (btnAll) btnAll.style.display = '';
        }
    } catch { list.innerHTML = '<span>Error de conexión.</span>'; }
}

async function revokeTrustedDevice(deviceId) {
    try {
        const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
        const res = await fetch(`/perfil/trusted-devices/${deviceId}/revoke`, {
            method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf }
        });
        const data = await res.json();
        if (data.success) { showToast('Dispositivo revocado', 'success'); loadTrustedDevices(); }
        else showToast(data.message || 'Error', 'error');
    } catch { showToast('Error de conexión', 'error'); }
}

async function revokeAllTrustedDevices() {
    if (!confirm('¿Revocar todos los dispositivos de confianza?')) return;
    try {
        const csrf = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
        const res = await fetch('/perfil/trusted-devices/revoke-all', {
            method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf }
        });
        const data = await res.json();
        if (data.success) { showToast('Todos los dispositivos revocados', 'success'); loadTrustedDevices(); }
    } catch { showToast('Error de conexión', 'error'); }
}

// ── 2FA ──
async function init2FASetup() {
    console.log('init2FASetup called');
    try {
        const res = await fetch('/perfil/2fa/setup');
        const data = await res.json();
        console.log('2FA setup response:', data);
        if (data.success) {
            document.getElementById('twofa-qr-img').src = data.qr_code;
            document.getElementById('twofa-code-input').value = '';
            document.getElementById('twofa-off-view').style.display = 'none';
            document.getElementById('twofa-setup-view').style.display = '';
        } else {
            showToast(data.message || 'Error al iniciar 2FA', 'error');
        }
    } catch (e) { console.error('2FA setup error:', e); showToast('Error de conexión', 'error'); }
}

async function verify2FACode() {
    const code = document.getElementById('twofa-code-input').value.trim();
    if (code.length !== 6) { showToast('Ingresa el código de 6 dígitos', 'warning'); return; }
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
        const res = await fetch('/perfil/2fa/enable', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken },
            body: JSON.stringify({ code })
        });
        const data = await res.json();
        if (data.success) {
            showToast('2FA activado correctamente 🔐', 'success');
            document.getElementById('twofa-setup-view').style.display = 'none';
            document.getElementById('twofa-on-view').style.display = '';
            document.getElementById('twofa-badge').textContent = 'Activado';
            document.getElementById('twofa-badge').style.background = '#dcfce7';
            document.getElementById('twofa-badge').style.color = '#16a34a';
        } else {
            showToast(data.message || 'Código incorrecto', 'error');
        }
    } catch { showToast('Error de conexión', 'error'); }
}

function cancel2FASetup() {
    document.getElementById('twofa-setup-view').style.display = 'none';
    document.getElementById('twofa-off-view').style.display = '';
}

async function disable2FA() {
    if (!confirm('¿Seguro que deseas desactivar 2FA?')) return;
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
        const res = await fetch('/perfil/2fa/disable', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken }
        });
        const data = await res.json();
        if (data.success) {
            showToast('2FA desactivado', 'success');
            document.getElementById('twofa-on-view').style.display = 'none';
            document.getElementById('twofa-off-view').style.display = '';
            document.getElementById('twofa-badge').textContent = 'Desactivado';
            document.getElementById('twofa-badge').style.background = '#fee2e2';
            document.getElementById('twofa-badge').style.color = '#dc2626';
        } else {
            showToast(data.message || 'Error al desactivar 2FA', 'error');
        }
    } catch { showToast('Error de conexión', 'error'); }
}

// ── DARK MODE ──
function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    // Animate button
    const btn = document.getElementById('themeToggle');
    if (btn) { btn.style.transform = 'scale(1.2) rotate(20deg)'; setTimeout(() => btn.style.transform = '', 250); }
}
