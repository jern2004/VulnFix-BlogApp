document.addEventListener('DOMContentLoaded', () => {
  const title = document.getElementById('title');
  const content = document.getElementById('content');
  const titleCount = document.getElementById('title-count');
  const contentCount = document.getElementById('content-count');
  const submitBtn = document.getElementById('submit-btn');

  function updateCounts() {
    titleCount.textContent = `${title.value.length}/100`;
    contentCount.textContent = `${content.value.length}`;
    submitBtn.disabled = !(title.value.trim() && content.value.trim());
  }

  function autoResize() {
    content.style.height = 'auto';
    content.style.height = `${content.scrollHeight}px`;
  }

  title.addEventListener('input', () => {
    updateCounts();
  });
  content.addEventListener('input', () => {
    updateCounts();
    autoResize();
  });

  // initialize counts and sizes
  updateCounts();
  autoResize();
});