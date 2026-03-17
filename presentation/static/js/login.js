document.addEventListener('DOMContentLoaded', () => {
  const rememberCheckbox = document.querySelector('input[name="remember"]');
  const emailInput = document.getElementById('email');

  if (rememberCheckbox && localStorage.getItem('rememberUser') === 'true') {
    rememberCheckbox.checked = true;
    if (localStorage.getItem('savedEmail')) {
      emailInput.value = localStorage.getItem('savedEmail');
    }
  }
});


async function handleLogin(e) {
  e.preventDefault();
  const btn = document.querySelector('.btn-submit');
  const errorMsg = document.getElementById('errorMsg');
  if (btn) btn.disabled = true;

  errorMsg.style.display = 'none';

  const rememberCheckbox = document.querySelector('input[name="remember"]');
  const rememberValue = rememberCheckbox ? rememberCheckbox.checked : false;
  const emailVal = document.getElementById('email').value;

  // Persist preference and email in localStorage
  if (rememberCheckbox) {
      if (rememberValue) {
          localStorage.setItem('rememberUser', 'true');
          localStorage.setItem('savedEmail', emailVal);
      } else {
          // Si el usuario desmarca explícitamente, lo quitamos todo
          localStorage.removeItem('rememberUser');
          localStorage.removeItem('savedEmail');
      }
  }


  // The final remember decision is purely what's in localStorage at this point,
  // honoring the user's previous requests per their requirement
  const finalRemember = localStorage.getItem('rememberUser') === 'true';

  try {
    const res = await fetch('/Login', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        email: document.getElementById('email').value,
        password: document.getElementById('password').value,
        remember: finalRemember
      })
    });

    const data = await res.json();
    if (data.success) {
      window.location.href = data.redirect;
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

function togglePassword() {
  const input = document.getElementById('password');
  input.type = input.type === 'password' ? 'text' : 'password';
}
