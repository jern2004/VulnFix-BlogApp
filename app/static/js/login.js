document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.querySelector('.toggle-password');
  const passwordInput = document.querySelector('#password');

  if (toggle && passwordInput) {
    toggle.addEventListener('click', () => {
      const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
      passwordInput.setAttribute('type', type);
      // swap the icon
      toggle.innerHTML = type === 'password'
        ? '<i class="bi bi-eye-fill"></i>'
        : '<i class="bi bi-eye-slash-fill"></i>';
    });
  }
});
