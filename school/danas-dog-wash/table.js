// The 90-lb table. Every number here traces to FROZEN-INVENTORY.md (F9–F19).
(function () {
  var MAX = 90;                                   // F9
  var BATH = { small: 60, medium: 75, large: 90 }; // F16 (D18)

  function band(w) {                              // F10–F12
    if (w < 25) return 'small';
    if (w <= 60) return 'medium';
    return 'large';
  }

  function answer(svc, w) {
    if (!(w > 0)) return { kind: 'ask', head: 'Enter a weight', body: 'Type your dog’s weight in pounds.' };
    if (w > MAX) return { kind: 'no', head: 'Too big for the table',
      body: 'Dana’s table maxes out at 90 lbs, so she can’t take a ' + w + '-lb dog.' };
    var b = band(w);
    if (svc === 'bath') return { kind: 'yes', head: '$' + BATH[b],
      body: 'Bath & Brush for a ' + b + ' dog (' + w + ' lbs).' };
    if (svc === 'groom') return { kind: 'range', head: '$85–$110',
      body: 'Full Groom (bath, a cut, nails). The price depends on the coat.' };
    if (svc === 'nails') return { kind: 'yes', head: '$20', body: 'Nail Trim Only.' };
    return { kind: 'unpriced', head: 'No price yet',
      body: 'Puppy Intro (puppies under 6 months) doesn’t have a price yet. Ask Dana by email.' };
  }

  var form = document.getElementById('est');
  if (!form) return;
  var num = document.getElementById('lbs');
  var slide = document.getElementById('slide');
  var out = document.getElementById('answer');

  function render() {
    var svc = form.querySelector('input[name=svc]:checked').value;
    var w = parseFloat(num.value);
    var a = answer(svc, w);
    out.className = 'answer is-' + a.kind;
    out.innerHTML = '';
    var h = document.createElement('strong'); h.textContent = a.head;
    var p = document.createElement('span'); p.textContent = a.body;
    out.appendChild(h); out.appendChild(p);
    form.dataset.band = w > MAX ? 'x' : (w > 0 ? band(w)[0] : '');
  }

  num.addEventListener('input', function () {
    var v = parseFloat(num.value);
    if (v > 0) slide.value = Math.min(120, Math.round(v));
    render();
  });
  slide.addEventListener('input', function () { num.value = slide.value; render(); });
  form.addEventListener('change', render);
  render();
  window.__estimate = answer; // test hook for QA
})();
