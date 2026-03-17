async function cargarUsuarios() {
  const res = await fetch('/get_usuarios');
  const data = await res.json();
  const tbody = document.getElementById('usersBody');
  if (!tbody) return;
  if (!data.success) { tbody.innerHTML = '<tr><td colspan="5" class="empty-state">Error al cargar usuarios</td></tr>'; return; }
  if (!data.usuarios.length) { tbody.innerHTML = '<tr><td colspan="5" class="empty-state">No hay usuarios</td></tr>'; return; }

  // Store users globally for local search/access if needed
  window.allUsersData = data.usuarios;

  tbody.innerHTML = data.usuarios.map(u => `
    <tr>
      <td data-label="Usuario"><div class="user-cell"><div class="table-avatar">${u.nombre[0].toUpperCase()}</div><span class="user-info-name">${u.nombre}</span></div></td>
      <td data-label="Correo">${u.email}</td>
      <td data-label="Username"><code>${u.user}</code></td>
      <td data-label="Rol"><span class="badge badge-${u.rol}">${u.rol}</span></td>
      <td data-label="Acciones">
        <button class="btn-icon" onclick='verDetalleUsuario("${u._id}")' title="Ver Detalles">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="11" y1="8" x2="11" y2="12"/><line x1="11" y1="14" x2="11.01" y2="14"/>
          </svg>
        </button>
      </td>
    </tr>`).join('');
}

let activeEditUser = null;

function verDetalleUsuario(id) {
  const u = window.allUsersData.find(x => x._id === id);
  if (!u) return;
  activeEditUser = u;

  document.getElementById('detalleUserFullNombre').textContent = u.nombre;
  document.getElementById('detalleUserEmail').textContent = u.email;
  document.getElementById('detalleUserUsername').textContent = u.user;
  
  const rolBadge = document.getElementById('detalleUserRol');
  rolBadge.textContent = u.rol;
  rolBadge.className = `badge badge-${u.rol}`;

  document.getElementById('userDetailModal').classList.add('active');
}

function closeUserDetailModal(e) {
  if (!e || e.target.id === 'userDetailModal') document.getElementById('userDetailModal').classList.remove('active');
}

function abrirEdicionUsuarioDesdeDetalle() {
  if (!activeEditUser) return;
  closeUserDetailModal();
  editarUsuario(activeEditUser);
}


function openUserModal(u=null) {
  document.getElementById('edit_user_id').value = '';
  document.getElementById('modalUserTitle').textContent = 'Nuevo Usuario';
  document.getElementById('passwordHint').textContent = '(requerida)';
  ['nombre','email','user','password'].forEach(f => document.getElementById('u_'+f).value = '');
  document.getElementById('u_rol').value = 'user';
  const btnDel = document.getElementById('btnDeleteUser');
  if(btnDel) btnDel.style.display = 'none';
  document.getElementById('userModal').classList.add('active');
}

function editarUsuario(u) {
  document.getElementById('edit_user_id').value = u._id;
  document.getElementById('modalUserTitle').textContent = 'Editar Usuario';
  document.getElementById('passwordHint').textContent = '(dejar vacío para no cambiar)';
  document.getElementById('u_nombre').value = u.nombre || '';
  document.getElementById('u_email').value = u.email || '';
  document.getElementById('u_user').value = u.user || '';
  document.getElementById('u_password').value = '';
  document.getElementById('u_rol').value = u.rol || 'user';
  
  // Bloquear cambio de rol si se edita a sí mismo
  const rolSelect = document.getElementById('u_rol');
  if (u._id === window.currentUserId) {
      rolSelect.disabled = true;
      rolSelect.title = "No puedes cambiar tu propio rol";
  } else {
      rolSelect.disabled = false;
      rolSelect.title = "";
  }

  const btnDel = document.getElementById('btnDeleteUser');
  if(btnDel) btnDel.style.display = 'inline-flex';
  document.getElementById('userModal').classList.add('active');
}

function closeUserModal(e) {
  if(!e || e.target.id==='userModal') document.getElementById('userModal').classList.remove('active');
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
  if(!id && !payload.password) { if(window.showToast) showToast('La contraseña es requerida', 'error'); return; }
  if(!payload.password) delete payload.password;

  const url = id ? `/update_usuario/${id}` : '/create_usuario';
  const method = id ? 'PUT' : 'POST';
  const res = await fetch(url, {method, headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
  const data = await res.json();
  if(data.success) { 
    closeUserModal(); 
    cargarUsuarios(); 
    if(window.showToast) showToast(data.message, 'success'); 
  }
  else if(window.showToast) showToast(data.message || 'Error', 'error');
}

async function eliminarUsuario() {
  const id = document.getElementById('edit_user_id').value;
  if(!id || !confirm('¿Eliminar este usuario?')) return;
  const res = await fetch(`/delete_usuario/${id}`, {method:'DELETE'});
  const data = await res.json();
  if(data.success) { 
    closeUserModal(); 
    cargarUsuarios(); 
    if(window.showToast) showToast(data.message, 'success'); 
  }
  else if(window.showToast) showToast(data.message || 'Error', 'error');
}

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('usersBody')) {
        cargarUsuarios();
    }
});
