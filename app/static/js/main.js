$(document).ready(function () {
  // hero expansion (if you have it)
  setTimeout(() => $('.hero-section').addClass('expanded'), 100);

  // delayed CTA for non-logged-in users
  if (!window.isLoggedIn) {
    setTimeout(() => {
      const $cta = $(`
        <div class="alert alert-warning text-center shadow-sm fade show cta-popup" role="alert">
          <button type="button" class="btn-close btn-close-black cta-close" aria-label="Close"></button>
          👋 New here? <a href="/register" class="alert-link">Create an account</a> to get started!
        </div>
      `);

      // Append, fade in, and bind close handler
      $cta.hide()
          .appendTo("body")
          .fadeIn(400);

      $cta.on("click", ".cta-close", () => {
        $cta.fadeOut(300, () => $cta.remove());
      });
    }, 5000);
  }

  // live search
  $('#search-box').on('keyup', function () {
    const value = $(this).val().toLowerCase();
    $('.post-card').each(function () {
      $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1);
    });
  });
});
