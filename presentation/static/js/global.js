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

// --- Global Notification (Toast) System ---
function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `premium-toast toast-${type}`;
    
    const icon = type === 'success' ? '✓' : (type === 'error' ? '✕' : '⚠');
    
    toast.innerHTML = `
        <div class="toast-icon" style="font-size: 1.2rem; font-weight: 900;">${icon}</div>
        <div class="toast-content">
            <div class="toast-title">${type.charAt(0).toUpperCase() + type.slice(1)}</div>
            <div class="toast-msg">${message}</div>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">✕</button>
    `;

    container.appendChild(toast);

    // Auto remove after 5s
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(20px)';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

// --- Global Status Modal (Animated) ---
function showStatusModal(type, customText = '') {
    const modal = document.getElementById('statusModal');
    const content = document.getElementById('statusContent');
    if (!modal || !content) return;

    let html = '';
    let title = '';

    if (type === 'saving') {
        title = customText || 'Guardando cambios...';
        html = `
            <div class="loader-ring"></div>
            <h2 style="margin: 0; color: var(--secondary); font-weight: 800; font-size: 1.5rem;">${title}</h2>
            <p style="color: var(--text-3); margin: 0;">Un momento, por favor.</p>
        `;
    } else if (type === 'deleting') {
        title = customText || 'Eliminando registro...';
        html = `
            <div class="loader-ring" style="border-top-color: var(--danger);"></div>
            <h2 style="margin: 0; color: var(--danger); font-weight: 800; font-size: 1.5rem;">${title}</h2>
            <p style="color: var(--text-3); margin: 0;">Eliminando permanentemente.</p>
        `;
    } else if (type === 'deactivating') {
        title = customText || 'Desactivando usuario...';
        html = `
            <div class="pulse-icon"><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18.36 6.64a9 9 0 1 1-12.73 0"/></svg></div>
            <h2 style="margin: 0; color: var(--accent); font-weight: 800; font-size: 1.5rem;">${title}</h2>
            <p style="color: var(--text-3); margin: 0;">Suspensión temporal en progreso.</p>
        `;
    }

    content.innerHTML = html;
    modal.classList.add('active');
}

function closeStatusModal() {
    const modal = document.getElementById('statusModal');
    if (modal) modal.classList.remove('active');
}

// --- Global Confirm Modal ---
let confirmCallback = null;

function showConfirmModal(title, message, onConfirm, btnType = 'primary') {
    const modal = document.getElementById('confirmModal');
    if (!modal) return;

    document.getElementById('confirmTitle').textContent = title;
    document.getElementById('confirmMessage').textContent = message;
    confirmCallback = onConfirm;

    const btn = document.getElementById('confirmBtn');
    // Sanitize classes before adding new ones
    btn.className = `btn btn-${btnType === 'danger' ? 'danger' : 'primary'}`;
    btn.onclick = () => {
        closeConfirmModal();
        if (confirmCallback) confirmCallback();
    };

    modal.classList.add('active');
}

function closeConfirmModal() {
    const modal = document.getElementById('confirmModal');
    if (modal) modal.classList.remove('active');
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

            modal.classList.add('active');
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
}

async function guardarPerfil() {
    const nombre = document.getElementById('perfil_nombre').value;
    const email = document.getElementById('perfil_email').value;
    const user = document.getElementById('perfil_user').value;
    const password = document.getElementById('perfil_password').value;
    
    showStatusModal('saving', 'Actualizando tu perfil...');

    try {
        const res = await fetch('/update_perfil', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
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
