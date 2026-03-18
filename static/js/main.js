$(document).ready(function () {

  // Auto-dismiss alerts after 4 seconds
  setTimeout(function () {
    $('.alert').fadeOut(400);
  }, 4000);

  // Confirm delete
  $(document).on('submit', '.confirm-delete', function (e) {
    if (!confirm('Are you sure you want to delete this? This cannot be undone.')) {
      e.preventDefault();
    }
  });

  // Select all / deselect all checkboxes helper
  $('#select-all-members').on('change', function () {
    $('.member-checkbox').prop('checked', $(this).is(':checked'));
  });

  // Amount formatting: keep 2 decimal places on blur
  $('input[type="number"][step="0.01"]').on('blur', function () {
    var val = parseFloat($(this).val());
    if (!isNaN(val)) {
      $(this).val(val.toFixed(2));
    }
  });

  // Highlight active nav link
  var path = window.location.pathname;
  $('.navbar-nav a').each(function () {
    if ($(this).attr('href') === path) {
      $(this).addClass('active');
    }
  });

  // Personal expense form toggle (mobile accordion)
  $('#toggle-pe-form').on('click', function () {
    $('#pe-form-section').slideToggle(250);
    var icon = $(this).find('.toggle-icon');
    icon.text(icon.text() === '▼' ? '▲' : '▼');
  });

});
