const SESSIONS_KEY = 'agenda_sdb_sessions';

// Obfuscación simple para no guardar en texto plano (Base64 + Inversión)
const obfuscate = (str) => btoa(str).split('').reverse().join('');
const deobfuscate = (str) => atob(str.split('').reverse().join(''));

document.addEventListener('DOMContentLoaded', () => {
    renderSessions();
    const passInput = document.getElementById('password');
    if (passInput) {
        passInput.addEventListener('input', () => {
            // Si el usuario escribe algo, el valor ya no es el obfuscado
            delete passInput.dataset.isObfuscated;
        });
    }
});

function renderSessions() {
    const container = document.getElementById('recentSessions');
    if (!container) return;
    
    const sessions = JSON.parse(localStorage.getItem(SESSIONS_KEY) || '[]');
    container.innerHTML = '';
    
    if (sessions.length === 0) {
        container.style.display = 'none';
        return;
    }
    
    container.style.display = 'block';
    
    // Título de la sección
    const title = document.createElement('h3');
    title.textContent = 'Sesiones Recientes';
    title.style.fontSize = '0.9rem';
    title.style.fontWeight = '700';
    title.style.color = '#475569';
    title.style.marginBottom = '12px';
    container.appendChild(title);

    const scrollContainer = document.createElement('div');
    scrollContainer.className = 'sessions-scroll-wrapper';
    scrollContainer.style.display = 'flex';
    scrollContainer.style.gap = '16px';
    scrollContainer.style.overflowX = 'auto';
    scrollContainer.style.padding = '8px 4px 16px';
    scrollContainer.style.scrollbarWidth = 'none';

    sessions.forEach(sess => {
        const card = document.createElement('div');
        card.className = 'session-card';
        card.onclick = () => selectSession(sess.email, sess.pass);
        
        const firstLetter = sess.nombre.charAt(0).toUpperCase();
        const avatarStyle = sess.avatar ? `background-image: url(${sess.avatar})` : '';
        
        card.innerHTML = `
            <button class="btn-remove" onclick="event.stopPropagation(); removeSession('${sess.email}')">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </button>
            <div class="avatar" style="${avatarStyle}">${sess.avatar ? '' : firstLetter}</div>
            <div class="name">${sess.nombre}</div>
            <div class="email">${sess.email}</div>
        `;
        scrollContainer.appendChild(card);
    });
    container.appendChild(scrollContainer);
}

function selectSession(email, obfuscatedPass) {
    const emailInput = document.getElementById('email');
    const passInput = document.getElementById('password');
    
    emailInput.value = email;
    passInput.value = obfuscatedPass; // Llenamos con la versión "encriptada"
    passInput.dataset.isObfuscated = "true";
    
    // Feedback visual y foco
    document.querySelector('.btn-submit').focus();
}

function removeSession(email) {
    let sessions = JSON.parse(localStorage.getItem(SESSIONS_KEY) || '[]');
    sessions = sessions.filter(s => s.email !== email);
    localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions));
    renderSessions();
}

// Validación de email
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Validación de contraseña
function validatePassword(password) {
    return password.length >= 6; // Mínimo 6 caracteres
}

// Mostrar error de validación
function showValidationError(message) {
    const errorMsg = document.getElementById('errorMsg');
    if (errorMsg) {
        errorMsg.textContent = message;
        errorMsg.style.display = 'block';
    }
}

// Limpiar mensajes de error
function clearValidationErrors() {
    const errorMsg = document.getElementById('errorMsg');
    if (errorMsg) {
        errorMsg.style.display = 'none';
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const btn = document.querySelector('.btn-submit');
    const errorMsg = document.getElementById('errorMsg');
    const emailInput = document.getElementById('email');
    const passInput = document.getElementById('password');
    const remember = document.querySelector('input[name="remember"]').checked;

    if (btn) btn.disabled = true;
    clearValidationErrors();

    let email = emailInput.value.trim();
    let password = passInput.value;

    // Validación de frontend
    if (!email) {
        showValidationError('El correo electrónico es obligatorio');
        if (btn) btn.disabled = false;
        return;
    }

    if (!validateEmail(email)) {
        showValidationError('Por favor, ingresa un correo electrónico válido');
        if (btn) btn.disabled = false;
        return;
    }

    if (!password) {
        showValidationError('La contraseña es obligatoria');
        if (btn) btn.disabled = false;
        return;
    }

    if (!validatePassword(password)) {
        showValidationError('La contraseña debe tener al menos 6 caracteres');
        if (btn) btn.disabled = false;
        return;
    }

    // SEGURIDAD: Si el valor es el obfuscado, lo de-obfuscamos solo antes de enviar
    if (passInput.dataset.isObfuscated === "true") {
        password = deobfuscate(password);
    }

    try {
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        const csrfToken = csrfMeta ? csrfMeta.getAttribute('content') : '';
        
        if (!csrfToken) {
            console.error('CSRF Token not found');
            errorMsg.textContent = 'Error de seguridad (CSRF missing)';
            errorMsg.style.display = 'block';
            if (btn) btn.disabled = false;
            return;
        }

        const res = await fetch('/Login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrfToken
            },
            body: JSON.stringify({ email, password, remember })
        });

        const data = await res.json();
        if (data.success) {
            if (remember) {
                let sessions = JSON.parse(localStorage.getItem(SESSIONS_KEY) || '[]');
                sessions = sessions.filter(s => s.email !== email);
                sessions.unshift({
                    email: email,
                    pass: obfuscate(password),
                    nombre: data.user_info.nombre,
                    avatar: data.user_info.avatar
                });
                localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions.slice(0, 3)));
            }
            const overlay = document.getElementById('loginLoadingOverlay');
            if (overlay) {
                overlay.removeAttribute('aria-hidden');
                overlay.classList.add('visible');
            }
            setTimeout(() => { window.location.href = data.redirect; }, 900);
        } else {
            errorMsg.textContent = data.message || 'Credenciales incorrectas';
            errorMsg.style.display = 'block';
        }
    } catch(err) {
        errorMsg.textContent = 'Error de conexión';
        errorMsg.style.display = 'block';
    } finally {
        if (btn) btn.disabled = false;
    }
}

// Dark Mode Toggle for Login
function toggleTheme() {
    const root = document.documentElement;
    const isDark = root.getAttribute('data-theme') === 'dark';
    const newTheme = isDark ? 'light' : 'dark';
    
    root.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}
