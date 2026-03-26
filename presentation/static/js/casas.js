let tempObras = [];
let activeCasaId = null;
let activeObraId = null;
let isEditingObraDirectly = false;
let searchTimeout = null;

// --- Funciones Principales ---
async function cargarCasas(q = '') {
  const grid = document.getElementById('casasGrid');
  if (!grid) return;

  grid.style.opacity = '0.5'; // Smooth transition start

  const tipo = document.getElementById('genderFilter') ? document.getElementById('genderFilter').value : 'todos';
  const url = new URL('/get_casas', window.location.origin);
  if (q) url.searchParams.append('q', q);
  if (tipo !== 'todos') url.searchParams.append('tipo', tipo);

  try {
    const res = await fetch(url);
    const data = await res.json();
    grid.style.opacity = '1'; // Restore opacity
    if (!data.success) {
      grid.innerHTML = '<p class="empty-state">Error al cargar datos</p>';
      showToast(data.message || 'Error al cargar institutos', 'error');
      return;
    }
    casasData = data.casas;
    renderCasas(casasData);
    
    // Refresh AOS and Init Tilt after rendering (only for non-touch devices)
    setTimeout(() => {
      if (typeof AOS !== 'undefined') AOS.refresh();
      
      const isTouchDevice = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);
      if (typeof VanillaTilt !== 'undefined' && !isTouchDevice) {
        VanillaTilt.init(document.querySelectorAll(".casa-card"), {
          max: 5, 
          speed: 800, 
          glare: true,
          "max-glare": 0.1, 
          scale: 1.01, 
          gyroscope: false 
        });
      }
    }, 50);
  } catch (err) {
    grid.style.opacity = '1';
    showToast('Error de conexión', 'error');
  }
}

function renderCasas(casas) {
  const grid = document.getElementById('casasGrid');
  if (!casas.length) { grid.innerHTML = '<p class="empty-state animate-fade-up">No se encontraron institutos</p>'; return; }

  const limitedCasas = casas.slice(0, 12);
  grid.innerHTML = limitedCasas.map((c, index) => {
    const delay = index * 0.05;
    const genderIcon = c.tipo === 'femenino' ? '♀' : '♂';
    const genderColor = c.tipo === 'femenino' ? '#ec4899' : '#3b82f6';

    return `
    <div class="casa-card" 
         data-aos="fade" 
         data-aos-delay="${index * 30}"
         onclick="verDetalleCasa('${c._id}')">
      <div style="height: 6px; background: ${genderColor};"></div>
      <div style="padding: 24px; flex-grow: 1; display:flex; flex-direction:column;">
        <div style="display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:20px;">
          <div style="width: 75px; height: 75px; border-radius: 16px; background: #ffffff; box-shadow: 0 4px 15px rgba(0,0,0,0.08); display:flex; align-items:center; justify-content:center; padding: 6px; border: 1px solid var(--border); flex-shrink:0;">
            <img src="/static/img/logo_sdb.png" alt="Logo" style="width: 100%; height: 100%; object-fit: contain;">
          </div>
          <div style="display:flex; flex-direction:column; align-items:flex-end; gap: 8px;">
            <div style="display:flex; align-items:center; gap: 6px; background: var(--primary-light); border: 1px solid rgba(220, 30, 70, 0.2); color: var(--primary); padding: 6px 14px; border-radius: 20px; font-weight: 800; font-size: 0.8rem;">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
              ${c.obras ? c.obras.length : 0} Obras
            </div>
            <div style="font-size: 1.2rem; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));" title="${c.tipo === 'femenino' ? 'Femenino' : 'Masculino'}">
              ${genderIcon}
            </div>
          </div>
        </div>
        <h3 style="font-size: 1.3rem; font-weight: 800; color: var(--text); margin: 0 0 12px 0; line-height: 1.3; letter-spacing: -0.3px;">${c.nombre}</h3>
        <div style="margin-top: auto; padding-top: 10px;"></div>
      </div>
      <div style="padding: 16px 24px; background: var(--surface2); border-top: 1px solid var(--border); display:flex; justify-content:space-between; align-items:center;">
        <span style="color: #DC1E46; font-size: 0.85rem; font-weight: 700;">Ver detalles →</span>
      </div>
    </div>`;
  }).join('');
}

function buscarCasas() {
  const input = document.getElementById('searchInput');
  if (!input) return;
  const q = input.value.trim();

  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    if (q.length > 1 || q.length === 0) cargarCasas(q);
  }, 300); // 300ms debounce
}

// --- Modales Casa Detalle ---
function verDetalleCasa(id) {
  const c = casasData.find(x => x._id === id);
  if (!c) return;
  activeCasaId = id;

  document.getElementById('detalleCasaNombre').textContent = c.nombre;
  document.getElementById('detalleCasaHistoria').textContent = c.historia || 'Sin historia registrada.';

  // Badge y Sombras de Logo Dinámicas
  const badge = document.getElementById('detalleCasaTipoBadge');
  const logoCircle = document.querySelector('.modal-logo-circle');
  const logoImg = logoCircle ? logoCircle.querySelector('img') : null;

  if (c.tipo === 'femenino') {
    if (badge) {
      badge.textContent = '♀ Femenino';
      badge.className = 'badge-premium female';
    }
    document.querySelector('.modal-header-compact').classList.add('female-theme');
    document.querySelector('.modal-header-compact').classList.remove('male-theme');
  } else {
    if (badge) {
      badge.textContent = '♂ Masculino';
      badge.className = 'badge-premium male';
    }
    document.querySelector('.modal-header-compact').classList.add('male-theme');
    document.querySelector('.modal-header-compact').classList.remove('female-theme');
  }

  // Report button link
  const reportBtn = document.getElementById('btnReporteCasa');
  if (reportBtn) reportBtn.href = `/reporte_casa/${id}`;

  const reportBtnWord = document.getElementById('btnReporteCasaWord');
  if (reportBtnWord) reportBtnWord.href = `/reporte_casa_word/${id}`;

  // Reset search
  document.getElementById('searchInputObras').value = '';
  renderObrasDetalleGrid(c.obras || [], c.tipo);

  // Micro-delay para que el usuario perciba el estado ":active" (tactile feedback)
  setTimeout(() => {
    document.getElementById('casaDetalleModal').classList.add('active');
    toggleBodyScroll();
  }, 100);
}

function renderObrasDetalleGrid(obras, tipo = 'masculino') {
  const grid = document.getElementById('detalleObrasGrid');
  if (!grid) return;

  if (!obras || obras.length === 0) {
    grid.innerHTML = '<p class="empty-state animate-fade-up">No hay obras registradas para este instituto.</p>';
    return;
  }

  // Asegurar que el grid tenga la clase correcta
  grid.className = 'detalle-obras-grid';

  const limitedObras = obras.slice(0, 12);
  grid.innerHTML = limitedObras.map((o, idx) => {
    const delay = idx * 0.05;
    const telfs = Array.isArray(o.telefono) ? o.telefono : (o.telefono ? [o.telefono] : []);
    const dispTelf = telfs.length > 0 ? telfs[0] : '—';
    const extraTelfs = telfs.length > 1 ? ` (+${telfs.length - 1} más)` : '';

    const themeClass = tipo === 'femenino' ? 'female-theme' : 'male-theme';

    return `
      <div class="obra-card-premium ${themeClass} animate-fade-up" style="animation-delay: ${delay}s;" onclick="verDetalleObra('${o.id}')">
        <div class="obra-card-accent"></div>
        <div class="obra-card-body">
          <h4 class="obra-card-title">${o.nombre_obra}</h4>
          
          <div class="obra-card-info">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#DC1E46" stroke-width="2.5"><circle cx="12" cy="10" r="3"/><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/></svg> 
            <span>${o.ciudad || '—'}</span>
          </div>
          
          <div class="obra-card-info">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2.5"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 12 19.79 19.79 0 0 1 1.61 3.48 2 2 0 0 1 3.58.67h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L7.91 8.1a16 16 0 0 0 6 6l.92-1.92a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 21.5 14.5z"/></svg>
            <span>${dispTelf}${extraTelfs}</span>
          </div>
        </div>
        <div class="obra-card-footer">
          <span>Ver ficha completa</span>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
        </div>
      </div>`;
  }).join('');
}

function buscarObrasDetalle() {
  const c = casasData.find(x => x._id === activeCasaId);
  if (!c) return;
  const q = document.getElementById('searchInputObras').value.toLowerCase().trim();
  const obras = c.obras || [];
  const filtradas = q ? obras.filter(o => (o.nombre_obra || '').toLowerCase().includes(q) || (o.ciudad || '').toLowerCase().includes(q)) : obras;
  renderObrasDetalleGrid(filtradas);
}

function closeCasaDetalleModal(e) {
  if (e && e.target.id !== 'casaDetalleModal') return;
  document.getElementById('casaDetalleModal').classList.remove('active');
  toggleBodyScroll();
}

// --- Modales Obra Detalle ---
function verDetalleObra(obraId) {
  const c = casasData.find(x => x._id === activeCasaId);
  if (!c) return;
  const o = (c.obras || []).find(x => x.id === obraId);
  if (!o) return;
  activeObraId = obraId;

  document.getElementById('detalleObraNombre').textContent = o.nombre_obra;
  document.getElementById('detalleObraCiudad').textContent = o.ciudad || '—';
  document.getElementById('detalleObraApartadoPostal').textContent = o.apartado_postal || '—';

  const telfs = Array.isArray(o.telefono) ? o.telefono : (o.telefono ? [o.telefono] : []);
  document.getElementById('detalleObraTelefonos').innerHTML = telfs.map(t => `<span>${t}</span>`).join('') || '—';

  document.getElementById('detalleObraDireccion').textContent = o.direccion || '—';

  const webLink = document.getElementById('detalleObraWeb');
  if (o.web) {
    webLink.href = o.web.startsWith('http') ? o.web : `https://${o.web}`;
    webLink.textContent = o.web;
    webLink.style.display = 'inline';
  } else {
    webLink.textContent = '—';
    webLink.href = '#';
  }

  const correos = Array.isArray(o.correo) ? o.correo : (o.correo ? [o.correo] : []);
  document.getElementById('detalleObraCorreos').innerHTML = correos.map(c => `<span>${c}</span>`).join('') || '—';

  document.getElementById('detalleObraContacto').textContent = o.contacto || '—';
  document.getElementById('detalleObraTelefonoContacto').textContent = o.telefono_contacto || '—';

  // Report button link
  const reportBtn = document.getElementById('btnReporteObra');
  if (reportBtn) reportBtn.href = `/reporte_obra/${activeCasaId}/${obraId}`;

  const reportBtnWord = document.getElementById('btnReporteObraWord');
  if (reportBtnWord) reportBtnWord.href = `/reporte_obra_word/${activeCasaId}/${obraId}`;

  setTimeout(() => {
    document.getElementById('obraDetalleModal').classList.add('active');
    toggleBodyScroll();
  }, 100);
}

function closeObraDetalleModal(e) {
  if (e && e.target.id !== 'obraDetalleModal') return;
  document.getElementById('obraDetalleModal').classList.remove('active');
  toggleBodyScroll();
}

function abrirEdicionObraDesdeDetalle() {
  if (!activeObraId) return;
  closeObraDetalleModal();

  isEditingObraDirectly = true;

  const c = casasData.find(x => x._id === activeCasaId);
  const o = c.obras.find(x => x.id === activeObraId);

  openObraModal(o.id, o);
}

// --- Modales Casa Form ---
function abrirEdicionDesdeDetalle() {
  if (!activeCasaId) return;
  closeCasaDetalleModal();
  openEditCasa(activeCasaId);
}

function openCasaModal(c = null) {
  document.getElementById('casa_id').value = c ? c._id : '';
  document.getElementById('modalCasaTitle').textContent = c ? 'Editar Instituto' : 'Nuevo Instituto';

  document.getElementById('casa_nombre').value = c ? (c.nombre || '') : '';
  document.getElementById('casa_historia').value = c ? (c.historia || '') : '';
  setGender(c ? (c.tipo || 'masculino') : 'masculino');

  // Clone obras array
  tempObras = c && c.obras ? JSON.parse(JSON.stringify(c.obras)) : [];
  renderFormObrasList();

  document.getElementById('btnEliminarCasa').style.display = 'none';
  document.getElementById('casaModal').classList.add('active');
  toggleBodyScroll();
}

function openEditCasa(id) {
  const c = casasData.find(x => x._id === id);
  if (!c) return;
  openCasaModal(c);
  if (['admin', 'superadmin'].includes(window.userRol)) {
    document.getElementById('btnEliminarCasa').style.display = 'inline-flex';
  }
}

function closeCasaModal(e) {
  if (e && e.target.id !== 'casaModal') return;
  document.getElementById('casaModal').classList.remove('active');
  toggleBodyScroll();
}

// --- Modales Obra Form (Interno al crear/editar Casa) ---
function renderFormObrasList() {
  const container = document.getElementById('formObrasList');
  if (!container) return;

  if (!tempObras.length) {
    container.innerHTML = '<p style="font-size:0.9rem; color:#888; text-align:center; padding:10px 0;">No hay obras añadidas aún.</p>';
    return;
  }

  container.innerHTML = tempObras.map(o => `
        <div class="form-obra-card animate-fade-up">
            <div class="form-obra-info">
                <div class="form-obra-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M3 21h18"/><path d="M9 21V9l3-3 3 3v12"/><path d="M2 21h4V12h3"/><path d="M15 12h3v9h4"/></svg>
                </div>
                <div class="form-obra-text">
                    <span class="form-obra-name">${o.nombre_obra}</span>
                    <span class="form-obra-meta">${o.ciudad || 'Sin ciudad'}</span>
                </div>
            </div>
            <div class="form-obra-actions">
                <button type="button" class="btn btn-ghost btn-icon-sq" title="Editar Obra" onclick="openObraModal('${o.id}')">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                </button>
                <button type="button" class="btn btn-danger btn-icon-sq" title="Eliminar Obra" onclick="eliminarObraTemp('${o.id}')">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </button>
            </div>
        </div>
    `).join('');
}

function openObraModal(obraId = null, directObraObj = null) {
  if (!directObraObj) {
    isEditingObraDirectly = false;
  }

  const o = directObraObj || (obraId ? tempObras.find(x => x.id === obraId) : null);

  document.getElementById('modalObraTitle').textContent = o ? 'Editar' : 'Agregar';
  document.getElementById('obra_temp_id').value = o ? o.id : '';

  document.getElementById('obra_nombre').value = o ? (o.nombre_obra || '') : '';
  document.getElementById('obra_apartado_postal').value = o ? (o.apartado_postal || '') : '';
  document.getElementById('obra_ciudad').value = o ? (o.ciudad || '') : '';
  document.getElementById('obra_direccion').value = o ? (o.direccion || '') : '';
  document.getElementById('obra_web').value = o ? (o.web || '') : '';
  document.getElementById('obra_contacto').value = o ? (o.contacto || '') : '';
  document.getElementById('obra_telefono_contacto').value = o ? (o.telefono_contacto || '') : '';

  // Handle multiple emails
  const emailContainer = document.getElementById('obraEmailsContainer');
  emailContainer.innerHTML = '';
  const correos = o && Array.isArray(o.correo) ? o.correo : (o && o.correo ? [o.correo] : []);
  if (correos.length === 0) {
    addEmailInput();
  } else {
    correos.forEach(c => addEmailInput(c));
  }

  // Handle multiple phones
  const phoneContainer = document.getElementById('obraPhonesContainer');
  phoneContainer.innerHTML = '';
  const telfs = o && Array.isArray(o.telefono) ? o.telefono : (o && o.telefono ? [o.telefono] : []);
  if (telfs.length === 0) {
    addPhoneInput();
  } else {
    telfs.forEach(t => addPhoneInput(t));
  }

  document.getElementById('obraModal').classList.add('active');
  toggleBodyScroll();
}

function addEmailInput(val = '') {
  const container = document.getElementById('obraEmailsContainer');
  const div = document.createElement('div');
  div.style.display = 'flex';
  div.style.gap = '8px';
  div.innerHTML = `
    <input type="email" class="form-input obra-email-input" value="${val}" placeholder="contacto@ejemplo.com" style="flex:1;"/>
    <button type="button" class="btn btn-danger" style="width: 44px; height: 44px; flex-shrink:0; border-radius: 12px; display:flex; align-items:center; justify-content:center; padding:0;" onclick="removeEmailInput(this)">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
    </button>
  `;
  container.appendChild(div);
}

function removeEmailInput(btn) {
  const container = document.getElementById('obraEmailsContainer');
  if (container.children.length > 1) {
    btn.parentElement.remove();
  } else {
    btn.parentElement.querySelector('input').value = '';
  }
}

function addPhoneInput(val = '') {
  const container = document.getElementById('obraPhonesContainer');
  const div = document.createElement('div');
  div.style.display = 'flex';
  div.style.gap = '8px';
  div.innerHTML = `
    <input type="text" class="form-input obra-phone-input" value="${val}" placeholder="+58 212 000 0000" style="flex:1;"/>
    <button type="button" class="btn btn-danger" style="width: 44px; height: 44px; flex-shrink:0; border-radius: 12px; display:flex; align-items:center; justify-content:center; padding:0;" onclick="removePhoneInput(this)">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
    </button>
  `;
  container.appendChild(div);
}

function removePhoneInput(btn) {
  const container = document.getElementById('obraPhonesContainer');
  if (container.children.length > 1) {
    btn.parentElement.remove();
  } else {
    btn.parentElement.querySelector('input').value = '';
  }
}

function closeObraModal(e) {
  if (e && e.target.id !== 'obraModal') return;
  document.getElementById('obraModal').classList.remove('active');
  toggleBodyScroll();
}

async function guardarObraInterna() {
  const n_obra = document.getElementById('obra_nombre').value.trim();
  if (!n_obra) { alert('El nombre de la Obra es obligatorio'); return; }

  const telfInputs = document.querySelectorAll('.obra-phone-input');
  const telfs = Array.from(telfInputs).map(i => i.value.trim()).filter(v => v !== '');

  const emailInputs = document.querySelectorAll('.obra-email-input');
  const emails = Array.from(emailInputs).map(i => i.value.trim()).filter(v => v !== '');

  const data = {
    nombre_obra: n_obra,
    telefono: telfs,
    apartado_postal: document.getElementById('obra_apartado_postal').value.trim(),
    ciudad: document.getElementById('obra_ciudad').value.trim(),
    direccion: document.getElementById('obra_direccion').value.trim(),
    web: document.getElementById('obra_web').value.trim(),
    correo: emails,
    contacto: document.getElementById('obra_contacto').value.trim(),
    telefono_contacto: document.getElementById('obra_telefono_contacto').value.trim(),
  };

  const currentId = document.getElementById('obra_temp_id').value;

  // Si estamos editando directamente desde el detalle de la obra:
  if (isEditingObraDirectly) {
    data.id = currentId || 'obra_' + Date.now();
    const c = casasData.find(x => x._id === activeCasaId);

    const payload = {
      nombre: c.nombre,
      historia: c.historia,
      obras: JSON.parse(JSON.stringify(c.obras || []))
    };

    const idx = payload.obras.findIndex(x => x.id === data.id);
    if (idx > -1) {
      payload.obras[idx] = data;
    } else {
      payload.obras.push(data);
    }

    const btn = document.querySelector('#obraModal .btn-primary');
    const originalText = btn.textContent;
    btn.disabled = true; btn.textContent = 'Guardando...';

    try {
      const res = await fetch(`/update_casa/${activeCasaId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const resData = await res.json();
      btn.disabled = false; btn.textContent = originalText;

      if (resData.success) {
        closeObraModal();
        cargarCasas();
        if (window.showToast) showToast('Obra actualizada exitosamente en la base de datos', 'success');
      } else {
        if (window.showToast) showToast(resData.message || 'Error al guardar la obra', 'error');
      }
    } catch (e) {
      btn.disabled = false; btn.textContent = originalText;
      console.error(e);
    }
    return;
  }

  // Flujo normal dentro del modal principal de Casa
  if (currentId) {
    const idx = tempObras.findIndex(x => x.id === currentId);
    if (idx > -1) {
      data.id = currentId;
      tempObras[idx] = data;
    }
  } else {
    data.id = 'obra_' + Date.now() + Math.floor(Math.random() * 1000);
    tempObras.push(data);
  }

  renderFormObrasList();
  closeObraModal();
}

function eliminarObraTemp(id) {
  showConfirmModal(
    '¿Eliminar Obra?',
    '¿Estás seguro de que deseas quitar esta obra de la lista temporal?',
    () => {
      tempObras = tempObras.filter(x => x.id !== id);
      renderFormObrasList();
      showToast('Obra removida de la lista', 'success');
    },
    'danger'
  );
}

// --- API Calls Guardar/Eliminar Casa ---
async function guardarCasa() {
  const id = document.getElementById('casa_id').value;
  const nombre = document.getElementById('casa_nombre').value.trim();
  const historia = document.getElementById('casa_historia').value.trim();

  if (!nombre) {
    showToast('El nombre del Instituto es obligatorio', 'warning');
    return;
  }

  const payload = {
    nombre: nombre,
    historia: historia,
    tipo: document.getElementById('casa_tipo').value,
    obras: tempObras
  };

  showStatusModal('saving', id ? 'Actualizando instituto...' : 'Creando nuevo instituto...');

  const url = id ? `/update_casa/${id}` : '/create_casa';
  const method = id ? 'PUT' : 'POST';
  try {
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    closeStatusModal();

    if (data.success) {
      closeCasaModal();
      cargarCasas();
      showToast(data.message, 'success');
    }
    else {
      showToast(data.message || 'Error', 'error');
    }
  } catch (e) {
    closeStatusModal();
    showToast('Error de conexión', 'error');
    console.error(e);
  }
}

async function eliminarCasa() {
  const id = document.getElementById('casa_id').value;
  if (!id) return;

  showConfirmModal(
    '¿Eliminar Instituto?',
    '¿Estás seguro de eliminar este instituto con todas sus obras? Esta acción es irreversible.',
    async () => {
      showStatusModal('deleting', 'Eliminando registro del instituto...');
      try {
        const res = await fetch(`/delete_casa/${id}`, { method: 'DELETE' });
        const data = await res.json();
        closeStatusModal();
        if (data.success) {
          closeCasaModal();
          cargarCasas();
          showToast(data.message, 'success');
        }
        else showToast(data.message || 'Error al eliminar', 'error');
      } catch (e) {
        closeStatusModal();
        showToast('Error de red', 'error');
        console.error(e);
      }
    },
    'danger'
  );
}

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
  cargarCasas();
  initCustomSelect();
});

function initCustomSelect() {
  const trigger = document.getElementById('genderSelectTrigger');
  const dropdown = document.getElementById('genderDropdown');
  const hiddenInput = document.getElementById('genderFilter');
  const selectedText = document.getElementById('selectedGenderText');
  const options = document.querySelectorAll('.gender-option');


  const closeDropdown = () => {
    dropdown.classList.remove('open');
    trigger.classList.remove('active');
  };

  trigger.onclick = (e) => {
    e.stopPropagation();
    dropdown.classList.contains('open') ? closeDropdown() : (dropdown.classList.add('open'), trigger.classList.add('active'));
  };

  options.forEach(opt => {
    opt.onclick = () => {
      hiddenInput.value = opt.getAttribute('data-value');
      selectedText.textContent = opt.textContent.trim();
      closeDropdown();
      cargarCasas();
    };
  });

  document.addEventListener('click', closeDropdown);
}

function setGender(val) {
  const input = document.getElementById('casa_tipo');
  if (!input) return;

  input.value = val;

  const btnMale = document.getElementById('genderBtnMale');
  const btnFemale = document.getElementById('genderBtnFemale');

  if (val === 'masculino') {
    btnMale.classList.add('active');
    btnFemale.classList.remove('active');
  } else {
    btnFemale.classList.add('active');
    btnMale.classList.remove('active');
  }
}

// Move modals to body to escape .main-content stacking context
document.addEventListener('DOMContentLoaded', () => {
    ['casaModal', 'obraModal', 'casaDetalleModal', 'obraDetalleModal'].forEach(id => {
        const modal = document.getElementById(id);
        if (modal) {
            document.body.appendChild(modal);
        }
    });
});
