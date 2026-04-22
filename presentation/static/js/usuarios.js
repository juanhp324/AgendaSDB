async function cargarUsuarios() {
  const tbody = document.getElementById('usersBody');
  if (!tbody) return;
  
  tbody.style.opacity = '0.5';

  try {
    const res = await fetch('/get_usuarios');
    const data = await res.json();
    tbody.style.opacity = '1';
    
    if (!data.success) { 
        tbody.innerHTML = '<tr><td colspan="5" class="empty-state">Error al cargar usuarios</td></tr>'; 
        showToast(data.message || 'Error', 'error');
        return; 
    }
    
    // FILTRAR PROPIO USUARIO
    const filteredUsers = data.usuarios.filter(u => u._id !== window.currentUserId);
    window.allUsersData = filteredUsers;

    if (!filteredUsers.length) { 
        tbody.innerHTML = '<tr><td colspan="5" class="empty-state">No hay otros usuarios para gestionar</td></tr>'; 
        return; 
    }

    tbody.innerHTML = filteredUsers.map(u => `
      <tr class="${u.activo === false ? 'row-inactive' : ''}" onclick="verDetalleUsuario('${u._id}')" style="cursor: pointer;">
        <td data-label="Usuario">
            <div class="user-cell">
                <div class="table-avatar" style="${u.activo === false ? 'filter: grayscale(1); opacity: 0.5;' : ''}">${u.nombre[0].toUpperCase()}</div>
                <div style="display:flex; flex-direction:column;">
                    <span class="user-info-name" style="${u.activo === false ? 'text-decoration: line-through; color: var(--text-3);' : ''}">${u.nombre}</span>
                    ${u.activo === false ? '<span style="font-size: 0.7rem; color: var(--danger); font-weight: 700;">DESACTIVADO</span>' : ''}
                </div>
            </div>
        </td>
        <td data-label="Correo">${u.email}</td>
        <td data-label="Username"><code>${u.user}</code></td>
        <td data-label="Rol"><span class="badge badge-${u.rol}">${u.rol}</span></td>
      </tr>`).join('');
  } catch (err) {
    tbody.style.opacity = '1';
    showToast('Error de conexión', 'error');
  }
}

// --- Acciones de Usuario ---

function openUserModal(id = null) {
  const modal = document.getElementById('userModal');
  const title = document.getElementById('modalUserTitle');
  const formId = document.getElementById('edit_user_id');
  const hint = document.getElementById('passwordHint');

  if (id) {
    const u = window.allUsersData.find(x => x._id === id);
    if (!u) return;
    title.textContent = 'Editar';
    formId.value = u._id;
    document.getElementById('u_nombre').value = u.nombre;
    document.getElementById('u_email').value = u.email;
    document.getElementById('u_user').value = u.user;
    document.getElementById('u_password').value = '';
    document.getElementById('u_rol').value = u.rol;
    hint.textContent = '(dejar vacío para no cambiar)';
    if (document.getElementById('btnDeleteUser')) document.getElementById('btnDeleteUser').style.display = 'block';
  } else {
    title.textContent = 'Nuevo';
    formId.value = '';
    document.getElementById('u_nombre').value = '';
    document.getElementById('u_email').value = '';
    document.getElementById('u_user').value = '';
    document.getElementById('u_password').value = '';
    document.getElementById('u_rol').value = 'user';
    hint.textContent = '(requerida)';
    if (document.getElementById('btnDeleteUser')) document.getElementById('btnDeleteUser').style.display = 'none';
  }
  modal.classList.add('active');
  toggleBodyScroll();
}

function closeUserModal(e = null) {
  if (e && e.target !== e.currentTarget) return;
  document.getElementById('userModal').classList.remove('active');
  toggleBodyScroll();
}

function verDetalleUsuario(id) {
  const u = window.allUsersData.find(x => x._id === id);
  if (!u) return;

  document.getElementById('detalleUserFullNombre').textContent = u.nombre;
  document.getElementById('detalleUserNombreDisplay').textContent = u.nombre;
  document.getElementById('detalleUserEmail').textContent = u.email;
  document.getElementById('detalleUserUsername').textContent = u.user;
  
  const rolBadge = document.getElementById('detalleUserRol');
  rolBadge.textContent = u.rol;
  rolBadge.className = `badge badge-${u.rol}`;

  const avatar = document.getElementById('detalleUserAvatar');
  avatar.textContent = u.nombre[0].toUpperCase();

  // Configurar botones de acción en el modal
  const btnDesactivar = document.getElementById('btnDesactivarDesdeDetalle');
  const txtDesactivar = document.getElementById('txtBtnDesactivar');
  if (btnDesactivar) {
      txtDesactivar.textContent = u.activo === false ? 'Reactivar' : 'Desactivar';
      btnDesactivar.className = u.activo === false ? 'btn btn-secondary' : 'btn btn-secondary'; // Mantener estilo neutro o ajustar si se desea
  }

  const btn2FA = document.getElementById('btnDisable2FADetalle');
  if (btn2FA) btn2FA.style.display = u['2fa_enabled'] ? '' : 'none';

  window.currentDetailUserId = id;
  document.getElementById('userDetailModal').classList.add('active');
  toggleBodyScroll();
}

function closeUserDetailModal(e = null) {
  if (e && e.target !== e.currentTarget) return;
  document.getElementById('userDetailModal').classList.remove('active');
  toggleBodyScroll();
}

function abrirEdicionUsuarioDesdeDetalle() {
  const id = window.currentDetailUserId;
  closeUserDetailModal();
  setTimeout(() => openUserModal(id), 100); // Pequeño delay para suavizar transición
}

function manejadorDesactivarDesdeDetalle() {
    if (!window.currentDetailUserId) return;
    confirmarDesactivar(window.currentDetailUserId);
}

function manejadorEliminarDesdeDetalle() {
    if (!window.currentDetailUserId) return;
    confirmarEliminarUsuario(window.currentDetailUserId);
}

async function manejadorDisable2FA() {
    if (!window.currentDetailUserId) return;
    if (!confirm('¿Desactivar 2FA para este usuario?')) return;
    try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
        const res = await fetch(`/disable_2fa_usuario/${window.currentDetailUserId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken }
        });
        const data = await res.json();
        if (data.success) {
            showToast('2FA desactivado para el usuario', 'success');
            document.getElementById('btnDisable2FADetalle').style.display = 'none';
            const u = window.allUsersData.find(x => x._id === window.currentDetailUserId);
            if (u) u['2fa_enabled'] = false;
        } else {
            showToast(data.message || 'Error', 'error');
        }
    } catch { showToast('Error de conexión', 'error'); }
}

function confirmarDesactivar(id) {
    const u = window.allUsersData.find(x => x._id === id);
    if (!u) return;
    const action = u.activo === false ? 'Reactivar' : 'Desactivar';
    
    showConfirmModal(
        `¿${action} Usuario?`,
        `¿Estás seguro de que deseas ${action.toLowerCase()} a ${u.nombre}?`,
        async () => {
            showStatusModal('deactivating', `${u.activo === false ? 'Reactivando' : 'Desactivando'}...`);
            try {
                const res = await fetch(`/update_usuario/${id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ activo: u.activo === false })
                });
                const data = await res.json();
                if (data.success) {
                    showToast(data.message || `Usuario ${action.toLowerCase()}do`, 'success');
                    cargarUsuarios();
                } else {
                    showToast(data.message || 'Error', 'error');
                }
            } catch (err) {
                showToast('Error de red', 'error');
            } finally {
                closeStatusModal();
            }
        },
        'danger'
    );
}

function confirmarEliminarUsuario(id) {
    const u = window.allUsersData.find(x => x._id === id);
    if (!u) return;

    showConfirmModal(
        '¿Eliminar Usuario?',
        `¿Estás seguro de que deseas eliminar permanentemente a ${u.nombre}? Esta acción no se puede deshacer.`,
        async () => {
            showStatusModal('deleting', 'Borrando usuario...');
            try {
                const res = await fetch(`/delete_usuario/${id}`, { method: 'DELETE' });
                const data = await res.json();
                if (data.success) {
                    showToast(data.message || 'Usuario eliminado', 'success');
                    cargarUsuarios();
                    closeUserDetailModal();
                } else {
                    showToast(data.message || 'Error', 'error');
                }
            } catch (err) {
                showToast('Error de red', 'error');
            } finally {
                closeStatusModal();
            }
        },
        'danger'
    );
}

async function guardarUsuario() {
  const id = document.getElementById('edit_user_id').value;
  const payload = {
    nombre: document.getElementById('u_nombre').value.trim(),
    email: document.getElementById('u_email').value.trim(),
    user: document.getElementById('u_user').value.trim(),
    password: document.getElementById('u_password').value,
    rol: document.getElementById('u_rol').value,
  };
  if(!id && !payload.password) { showToast('La contraseña es requerida', 'warning'); return; }
  if(!payload.password) delete payload.password;

  showStatusModal('saving', id ? 'Actualizando usuario...' : 'Creando usuario...');

  try {
    const url = id ? `/update_usuario/${id}` : '/create_usuario';
    const method = id ? 'PUT' : 'POST';
    const res = await fetch(url, {method, headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
    const data = await res.json();
    if(data.success) { 
        closeUserModal(); 
        showToast(data.message, 'success');
        cargarUsuarios(); 
    } else {
        showToast(data.message || 'Error', 'error');
    }
  } catch (err) {
    showToast('Error de red', 'error');
  } finally {
    closeStatusModal();
  }
}

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('usersBody')) {
        cargarUsuarios();
    }
    
    // Move modals to body to escape .main-content stacking context
    ['userModal', 'userDetailModal'].forEach(id => {
        const modal = document.getElementById(id);
        if (modal) {
            document.body.appendChild(modal);
        }
    });
});
