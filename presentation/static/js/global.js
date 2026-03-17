/**
 * AgendaSDB - Global JavaScript
 * Handles topbar dropdowns, modals, and common UI interactions.
 */

// --- Dropbox / User Menu ---
function toggleUserMenu() {
    const dropdown = document.getElementById('userDropdown');
    const btn = document.getElementById('userMenuBtn');
    
    if (!dropdown || !btn) return;
    
    const isOpen = dropdown.classList.contains('open');
    
    // Close all other dropdowns if any (future proofing)
    
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

// --- Profile Modal ---
function openPerfilModal() {
    const modal = document.getElementById('perfilDetalleModal');
    if (!modal) return;
    
    fetch('/get_perfil')
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                document.getElementById('detallePerfilNombre').textContent = data.usuario.nombre || '—';
                document.getElementById('detallePerfilNombreHeader').textContent = data.usuario.nombre || 'Mi Perfil';
                document.getElementById('detallePerfilEmail').textContent = data.usuario.email || '—';
                document.getElementById('detallePerfilUser').textContent = data.usuario.user || '—';
                
                const avatar = document.getElementById('detallePerfilAvatar');
                if (avatar && data.usuario.nombre) {
                    avatar.textContent = data.usuario.nombre[0].toUpperCase();
                }

                const rolBadge = document.getElementById('detallePerfilRolBadge');
                if (rolBadge) {
                    rolBadge.textContent = data.usuario.rol || 'user';
                    rolBadge.className = `badge badge-${data.usuario.rol || 'user'}`;
                }

                // Pre-populate edit modal secretly
                document.getElementById('perfil_nombre').value = data.usuario.nombre || '';
                document.getElementById('perfil_email').value = data.usuario.email || '';
                document.getElementById('perfil_user').value = data.usuario.user || '';
                document.getElementById('perfil_rol').value = data.usuario.rol || '';
                document.getElementById('perfil_password').value = '';

                modal.classList.add('active');
                document.getElementById('userDropdown').classList.remove('open');
                document.getElementById('userMenuBtn').removeAttribute('data-open');
            }
        });
}

function closePerfilDetalleModal(e) {
    if (!e || e.target.id === 'perfilDetalleModal') document.getElementById('perfilDetalleModal').classList.remove('active');
}

function abrirEdicionPerfilDesdeDetalle() {
    closePerfilDetalleModal();
    document.getElementById('perfilModal').classList.add('active');
}

function closePerfilModal(e) {
    const modal = document.getElementById('perfilModal');
    if (!modal) return;
    
    // If e is provided, check if click was on overlay
    if (e && e.target !== modal) return;
    
    modal.classList.remove('active');
}

async function guardarPerfil() {
    const nombre = document.getElementById('perfil_nombre').value;
    const email = document.getElementById('perfil_email').value;
    const user = document.getElementById('perfil_user').value;
    const password = document.getElementById('perfil_password').value;
    
    const btn = document.querySelector('#perfilModal .btn-primary');
    const originalText = btn.textContent;
    btn.textContent = 'Guardando...';
    btn.disabled = true;

    try {
        const res = await fetch('/update_perfil', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nombre, email, user, password })
        });
        
        const data = await res.json();
        if (data.success) {
            location.reload(); // Reload to show new name/info
        } else {
            alert(data.message || 'Error al actualizar perfil');
        }
    } catch (err) {
        console.error(err);
        alert('Error de conexión');
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}
