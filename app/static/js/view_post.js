document.addEventListener('DOMContentLoaded', () => {
  const countdownEl = document.getElementById('countdown');
  const editBtn     = document.getElementById('edit-button');
  if (!countdownEl || !editBtn) return;

  // parse the ISO date from our data-attribute
  const createdAt = new Date(countdownEl.dataset.createdAt);
  const expiryMs  = 60 * 60 * 1000; // 1 hour
  const expiryTime = createdAt.getTime() + expiryMs;

  function updateCountdown() {
    const now  = Date.now();
    const diff = expiryTime - now;

    if (diff <= 0) {
      countdownEl.textContent = 'Edit period expired';
      editBtn.disabled = true;
      editBtn.classList.add('disabled');  // add a CSS rule for .disabled { opacity: .5; cursor: not-allowed; }
      clearInterval(timerInterval);
    } else {
      const hrs  = Math.floor(diff / 3600000);
      const mins = Math.floor((diff % 3600000) / 60000);
      const secs = Math.floor((diff % 60000) / 1000);
      countdownEl.textContent =
        `Time left to edit: ${String(hrs).padStart(2,'0')}:` +
        `${String(mins).padStart(2,'0')}:` +
        `${String(secs).padStart(2,'0')}`;
    }
  }

  // start immediately, then every second
  updateCountdown();
  const timerInterval = setInterval(updateCountdown, 1000);
});