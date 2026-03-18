let casasData = [];

async function cargarCasas(q='') {
  const grid = document.getElementById('casasGrid');
  if (!grid) return;
  grid.innerHTML = '<div class="loading-spinner">Cargando...</div>';
  const url = q ? `/get_casas?q=${encodeURIComponent(q)}` : '/get_casas';
  const res = await fetch(url);
  const data = await res.json();
  if (!data.success) { grid.innerHTML = '<p class="empty-state">Error al cargar datos</p>'; return; }
  casasData = data.casas;
  renderCasas(casasData);
}

function renderCasas(casas) {
  const grid = document.getElementById('casasGrid');
  if (!casas.length) { grid.innerHTML = '<p class="empty-state">No se encontraron casas</p>'; return; }
  
  grid.innerHTML = casas.map(c => `
    <div class="casa-card" onclick="verDetalleCasa('${c._id}')">
      <div class="card-logo">
        ${c.logo_filename
          ? `<img src="/static/uploads/logos/${c.logo_filename}" alt="${c.nombre}" onerror="this.parentElement.innerHTML='🏠'"/>`
          : '<span class="logo-placeholder-icon">🏠</span>'}
      </div>
      <div class="card-body">
        <h3 class="card-title">${c.nombre}</h3>
        <p class="card-meta"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg> ${c.ciudad || '—'}</p>
        <p class="card-meta"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 12 19.79 19.79 0 0 1 1.61 3.48 2 2 0 0 1 3.58.67h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L7.91 8.1a16 16 0 0 0 6 6l.92-1.92a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 21.5 14.5z"/></svg> ${c.telefono || '—'}</p>
        ${c.contacto ? `<p class="card-contact">Contacto: ${c.contacto}</p>` : ''}
      </div>
    </div>`).join('');
}

function buscarCasas() {
  const q = document.getElementById('searchInput').value.trim();
  if (q.length > 1 || q.length === 0) cargarCasas(q);
}

let activeCasaId = null;

function verDetalleCasa(id) {
  const c = casasData.find(x => x._id === id);
  if (!c) return;
  activeCasaId = id;

  document.getElementById('detalleCasaNombre').textContent = c.nombre;
  document.getElementById('detalleCasaCiudadHero').textContent = c.ciudad || '—';
  document.getElementById('detalleCasaCiudad').textContent = c.ciudad || '—';
  document.getElementById('detalleCasaTelefono').textContent = c.telefono || '—';
  document.getElementById('detalleCasaDireccion').textContent = c.direccion || '—';
  
  const webLink = document.getElementById('detalleCasaWeb');
  if (c.web) {
    webLink.href = c.web.startsWith('http') ? c.web : `https://${c.web}`;
    webLink.textContent = c.web;
    webLink.style.display = 'inline';
  } else {
    webLink.textContent = '—';
    webLink.href = '#';
  }

  document.getElementById('detalleCasaCorreo').textContent = c.correo || '—';
  document.getElementById('detalleCasaContacto').textContent = c.contacto || '—';
  document.getElementById('detalleCasaTelefonoContacto').textContent = c.telefono_contacto || '—';
  document.getElementById('detalleCasaHistoria').textContent = c.historia || 'Sin historia registrada.';

  // Report button link
  const reportBtn = document.getElementById('btnReporteCasa');
  if (reportBtn) reportBtn.href = `/reporte_casa/${id}`;

  const logoImg = document.getElementById('detalleCasaLogo');
  const placeholder = document.getElementById('detalleCasaLogoPlaceholder');
  const heroBg = document.getElementById('detalleHeroBg');
  const heroHeader = document.querySelector('.modal-header-hero');
  
  if (c.logo_filename) {
    const logoSrc = `/static/uploads/logos/${c.logo_filename}`;
    logoImg.src = logoSrc;
    logoImg.style.display = 'block';
    placeholder.style.display = 'none';
    heroBg.style.backgroundImage = `linear-gradient(rgba(44, 62, 80, 0.4), rgba(44, 62, 80, 0.9)), url('${logoSrc}')`;
    if (heroHeader) heroHeader.classList.remove('no-logo');
  } else {
    logoImg.style.display = 'none';
    placeholder.style.display = 'flex';
    if (heroHeader) heroHeader.classList.add('no-logo');
    // Premium Mesh Gradient Placeholder
    heroBg.style.backgroundImage = `
      radial-gradient(at 0% 0%, rgba(220, 30, 70, 0.4) 0px, transparent 50%),
      radial-gradient(at 50% 0%, rgba(44, 62, 80, 0.4) 0px, transparent 50%),
      radial-gradient(at 100% 0%, rgba(220, 30, 70, 0.4) 0px, transparent 50%),
      radial-gradient(at 50% 100%, rgba(44, 62, 80, 0.6) 0px, transparent 50%),
      #f8f9fa
    `;
  }

  // Reset historia
  const histContainer = document.getElementById('detalleCasaHistoriaContainer');
  histContainer.classList.remove('active');
  const toggleBtnText = document.getElementById('historyToggleText');
  const toggleBtnIcon = document.getElementById('historyToggleIcon');
  toggleBtnText.textContent = 'Ver Historia';
  toggleBtnIcon.textContent = '📖';

  document.getElementById('casaDetalleModal').classList.add('active');
}

function toggleHistoriaDetalle() {
  const container = document.getElementById('detalleCasaHistoriaContainer');
  const btnText = document.getElementById('historyToggleText');
  const btnIcon = document.getElementById('historyToggleIcon');
  
  const isActive = container.classList.toggle('active');
  btnText.textContent = isActive ? 'Ocultar Historia' : 'Ver Historia';
  btnIcon.textContent = isActive ? '📕' : '📖';
}

function closeCasaDetalleModal(e) {
  if (!e || e.target.id === 'casaDetalleModal') document.getElementById('casaDetalleModal').classList.remove('active');
}

function abrirEdicionDesdeDetalle() {
  if (!activeCasaId) return;
  closeCasaDetalleModal();
  openEditCasa(activeCasaId);
}

function openCasaModal(c=null) {
  document.getElementById('casa_id').value = '';
  document.getElementById('modalCasaTitle').textContent = 'Nueva Casa Salesiana';
  ['nombre','telefono','ciudad','direccion','web','correo','contacto','telefono_contacto','historia','logo_filename'].forEach(f => {
    const el = document.getElementById('casa_'+f);
    if(el) el.value = c ? (c[f]||'') : '';
  });
  document.getElementById('logoPreview').style.display = 'none';
  document.getElementById('logoPlaceholder').style.display = 'flex';
  document.getElementById('btnQuitarLogo').style.display = 'none';
  document.getElementById('btnEliminarCasa').style.display = 'none';
  document.getElementById('casaModal').classList.add('active');
}

function openEditCasa(id) {
  const c = casasData.find(x=>x._id===id);
  if(!c) return;
  openCasaModal(c);
  document.getElementById('casa_id').value = id;
  document.getElementById('modalCasaTitle').textContent = 'Editar Casa Salesiana';
  if(c.logo_filename){
    const preview = document.getElementById('logoPreview');
    preview.src = `/static/uploads/logos/${c.logo_filename}`;
    preview.style.display = 'block';
    document.getElementById('logoPlaceholder').style.display = 'none';
    document.getElementById('btnQuitarLogo').style.display = 'flex';
  } else {
    document.getElementById('btnQuitarLogo').style.display = 'none';
  }
  
  if (['admin','superadmin'].includes(window.userRol)) {
    document.getElementById('btnEliminarCasa').style.display = 'inline-flex';
  }
}

function closeCasaModal(e) {
  if(!e || e.target.id==='casaModal') document.getElementById('casaModal').classList.remove('active');
}

function previewLogo(event) {
  const file = event.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = e => {
    const preview = document.getElementById('logoPreview');
    preview.src = e.target.result;
    preview.style.display = 'block';
    document.getElementById('logoPlaceholder').style.display = 'none';
    document.getElementById('btnQuitarLogo').style.display = 'flex';
  };
  reader.readAsDataURL(file);
  uploadLogo(file);
}

function quitarLogoSeleccionado(e) {
  if (e) e.stopPropagation();
  document.getElementById('casa_logo_filename').value = '';
  document.getElementById('logoPreview').style.display = 'none';
  document.getElementById('logoPreview').src = '';
  document.getElementById('logoPlaceholder').style.display = 'flex';
  document.getElementById('btnQuitarLogo').style.display = 'none';
  document.getElementById('logoFile').value = '';
}

async function uploadLogo(file) {
  const formData = new FormData();
  formData.append('logo', file);
  const res = await fetch('/upload_logo', {method:'POST', body: formData});
  const data = await res.json();
  if(data.success) document.getElementById('casa_logo_filename').value = data.filename;
}

async function guardarCasa() {
  const id = document.getElementById('casa_id').value;
  const payload = {
    nombre: document.getElementById('casa_nombre').value.trim(),
    telefono: document.getElementById('casa_telefono').value.trim(),
    ciudad: document.getElementById('casa_ciudad').value.trim(),
    direccion: document.getElementById('casa_direccion').value.trim(),
    web: document.getElementById('casa_web').value.trim(),
    correo: document.getElementById('casa_correo').value.trim(),
    contacto: document.getElementById('casa_contacto').value.trim(),
    telefono_contacto: document.getElementById('casa_telefono_contacto').value.trim(),
    historia: document.getElementById('casa_historia').value.trim(),
    logo_filename: document.getElementById('casa_logo_filename').value.trim(),
  };
  if (!payload.nombre) { alert('El nombre es obligatorio'); return; }

  const btn = document.getElementById('btnGuardarCasa');
  btn.disabled = true; btn.textContent = 'Guardando...';

  const url = id ? `/update_casa/${id}` : '/create_casa';
  const method = id ? 'PUT' : 'POST';
  const res = await fetch(url, {method, headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
  const data = await res.json();
  btn.disabled = false; btn.textContent = 'Guardar';

  if(data.success) { 
    closeCasaModal(); 
    cargarCasas(); 
    if (window.showToast) showToast(data.message, 'success'); 
  }
  else if (window.showToast) showToast(data.message || 'Error', 'error');
}

async function eliminarCasa() {
  const id = document.getElementById('casa_id').value;
  if(!id || !confirm('¿Estás seguro de eliminar esta casa?')) return;
  const res = await fetch(`/delete_casa/${id}`, {method:'DELETE'});
  const data = await res.json();
  if(data.success) { 
    closeCasaModal(); 
    cargarCasas(); 
    if (window.showToast) showToast(data.message, 'success'); 
  }
  else if (window.showToast) showToast(data.message || 'Error al eliminar', 'error');
}

document.addEventListener('DOMContentLoaded', () => {
    cargarCasas();
});
