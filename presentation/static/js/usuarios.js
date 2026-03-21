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
      <tr class="${u.activo === false ? 'row-inactive' : ''}">
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
        <td data-label="Acciones">
          <div style="display:flex; gap: 8px;">
            <button class="btn-icon" onclick='verDetalleUsuario("${u._id}")' title="Ver Detalles">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            </button>
            <button class="btn-icon" onclick='confirmarDesactivar("${u._id}")' title="${u.activo === false ? 'Reactivar' : 'Desactivar'}" style="color: var(--accent);">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18.36 6.64a9 9 0 1 1-12.73 0"/></svg>
            </button>
            <button class="btn-icon" onclick='confirmarEliminarUsuario("${u._id}")' title="Eliminar" style="color: var(--danger);">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18m-2 0v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6m3 0V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg>
            </button>
          </div>
        </td>
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
    title.textContent = 'Editar Usuario';
    formId.value = u._id;
    document.getElementById('u_nombre').value = u.nombre;
    document.getElementById('u_email').value = u.email;
    document.getElementById('u_user').value = u.user;
    document.getElementById('u_password').value = '';
    document.getElementById('u_rol').value = u.rol;
    hint.textContent = '(dejar vacío para no cambiar)';
    if (document.getElementById('btnDeleteUser')) document.getElementById('btnDeleteUser').style.display = 'block';
  } else {
    title.textContent = 'Nuevo Usuario';
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
}

function closeUserModal(e = null) {
  if (e && e.target !== e.currentTarget) return;
  document.getElementById('userModal').classList.remove('active');
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

  window.currentDetailUserId = id;
  document.getElementById('userDetailModal').classList.add('active');
}

function closeUserDetailModal(e = null) {
  if (e && e.target !== e.currentTarget) return;
  document.getElementById('userDetailModal').classList.remove('active');
}

function abrirEdicionUsuarioDesdeDetalle() {
  const id = window.currentDetailUserId;
  closeUserDetailModal();
  openUserModal(id);
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
});
