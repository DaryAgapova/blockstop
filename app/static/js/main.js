/* МИР ПОЖАРНОЙ БЕЗОПАСНОСТИ — main.js */

document.addEventListener('DOMContentLoaded', function () {

  // Auto-dismiss flash alerts after 5s
  document.querySelectorAll('.alert.alert-dismissible').forEach(function (el) {
    setTimeout(function () {
      var bsAlert = bootstrap.Alert.getOrCreateInstance(el);
      if (bsAlert) bsAlert.close();
    }, 5000);
  });

  // Cart quantity: live update remove when 0
  document.querySelectorAll('.qty-field').forEach(function (inp) {
    inp.addEventListener('change', function () {
      if (parseInt(this.value) === 0) {
        this.closest('tr').style.opacity = '0.4';
      } else {
        this.closest('tr').style.opacity = '1';
      }
    });
  });

  // Navbar: active link highlight
  var path = window.location.pathname;
  document.querySelectorAll('.main-nav .nav-link').forEach(function (link) {
    var href = link.getAttribute('href');
    if (href && path.startsWith(href) && href !== '/') {
      link.classList.add('active');
    } else if (href === '/' && path === '/') {
      link.classList.add('active');
    }
  });

  // Product page: qty +/- buttons (global helper used inline too)
  window.changeQty = function (delta) {
    var inp = document.getElementById('qty');
    if (!inp) return;
    var v = parseInt(inp.value || 1) + delta;
    if (v < 1) v = 1;
    inp.value = v;
  };

  // Admin: price inputs — live grand total preview
  var priceInputs = document.querySelectorAll('.price-input');
  if (priceInputs.length > 0) {
    priceInputs.forEach(function (inp) {
      inp.addEventListener('input', recalcTotal);
    });
    recalcTotal();
  }

  function recalcTotal() {
    var rows = document.querySelectorAll('tbody tr');
    var total = 0;
    var allPriced = true;

    rows.forEach(function (row) {
      var priceInp = row.querySelector('.price-input');
      var qtyCell  = row.cells ? row.cells[1] : null;
      var subtotalCell = row.querySelector('.subtotal-cell');

      if (!priceInp || !qtyCell) return;

      var price = parseFloat(priceInp.value);
      var qty   = parseInt(qtyCell.textContent.trim()) || 1;

      if (!isNaN(price) && price > 0) {
        var sub = price * qty;
        total += sub;
        if (subtotalCell) {
          subtotalCell.textContent = formatMoney(sub) + ' ₽';
          subtotalCell.style.color = '#1a2744';
        }
      } else {
        allPriced = false;
        if (subtotalCell) {
          subtotalCell.textContent = '—';
          subtotalCell.style.color = '#9ca3af';
        }
      }
    });

    var totalEl = document.getElementById('grandTotal');
    if (totalEl) {
      if (allPriced && total > 0) {
        totalEl.textContent = formatMoney(total) + ' ₽';
        totalEl.style.color = '#dc2626';
      } else {
        totalEl.textContent = 'По запросу';
        totalEl.style.color = '#9ca3af';
      }
    }
  }

  function formatMoney(n) {
    return Math.round(n).toLocaleString('ru-RU');
  }

});
