// Hartline CSA share checker. Computed on the page; sends nothing, stores nothing.
(function () {
  var CAPACITY = 60, TAKEN = 41.5, LAST_WEEK = 20;
  var PRICE = { full: 28, half: 16 }, EQUIV = { full: 1, half: 0.5 };
  var MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];

  // Week 1: Wed June 3 2026 (farm) / Sat June 6 2026 (River Market). Every week after.
  function pickupDate(point, week) {
    var d = new Date(Date.UTC(2026, 5, point === 'farm' ? 3 : 6));
    d.setUTCDate(d.getUTCDate() + 7 * (week - 1));
    return (point === 'farm' ? 'Wednesday' : 'Saturday') + ', ' + MONTHS[d.getUTCMonth()] + ' ' + d.getUTCDate() + ', ' + d.getUTCFullYear();
  }
  function fmt(n) { return (n % 1 ? n.toFixed(1) : String(n)); }

  function check(req, remaining) {
    if (remaining === undefined) remaining = CAPACITY - TAKEN;
    var start = Math.min(4, Math.max(1, req.start | 0));
    var count = req.count === 2 ? 2 : 1;
    var size = req.size === 'half' ? 'half' : 'full';
    var need = EQUIV[size] * count;
    var weeks = LAST_WEEK - start + 1;
    var out = { size: size, count: count, start: start, point: req.point, need: need, remaining: remaining, weeks: weeks };
    if (need > remaining) {
      out.ok = false;
      out.roomInShares = Math.floor(remaining / EQUIV[size]);
      return out;
    }
    out.ok = true;
    out.perWeek = PRICE[size] * count;
    out.total = PRICE[size] * count * weeks;
    out.first = pickupDate(req.point, start);
    out.last = pickupDate(req.point, LAST_WEEK);
    return out;
  }

  if (typeof module !== 'undefined') { module.exports = { check: check, pickupDate: pickupDate }; return; }

  var form = document.getElementById('checker'), ans = document.getElementById('answer');
  function read() {
    var g = function (n) { return form.querySelector('input[name=' + n + ']:checked').value; };
    return { size: g('size'), count: +g('count'), point: g('point'), start: +g('start') };
  }
  function furrows(r) {
    var h = '<div class="furrows" aria-hidden="true">';
    for (var w = 1; w <= LAST_WEEK; w++) h += '<i class="' + (r.ok && w >= r.start ? 'on' : '') + '"></i>';
    return h + '</div><div class="furrows-k" aria-hidden="true"><span>Week 1</span><span>Week 20</span></div>';
  }
  function bar(r) {
    var pct = function (x) { return (x / CAPACITY * 100) + '%'; };
    var taken = CAPACITY - r.remaining, shown = Math.min(r.need, r.remaining);
    return '<div class="cap" role="img" aria-label="Capacity: ' + fmt(taken) + ' of 60 full-share equivalents spoken for, ' + fmt(r.remaining) + ' remain; this request needs ' + fmt(r.need) + '.">' +
      '<span class="taken" style="width:' + pct(taken) + '"></span><span class="req' + (r.ok ? '' : ' over') + '" style="width:' + pct(r.ok ? r.need : r.remaining) + '"></span></div>' +
      '<div class="cap-k"><span><i class="k1"></i>' + fmt(taken) + ' spoken for</span>' + (r.ok
        ? '<span><i class="k2"></i>your ' + fmt(r.need) + '</span><span><i class="k3"></i>' + fmt(r.remaining - r.need) + ' still open</span>'
        : '<span><i class="k2" style="background:var(--barn)"></i>' + fmt(shown) + ' left — less than the ' + fmt(r.need) + ' asked for</span>') + '<span>of 60</span></div>';
  }
  function label(r) { return r.count + ' ' + r.size + ' share' + (r.count > 1 ? 's' : ''); }
  function render() {
    var r = check(read(), window.__CSA_REMAINING_FIXTURE);
    var h;
    if (r.ok) {
      h = '<p class="verdict yes">Yes — there is room for ' + label(r) + '.</p>' +
        '<dl class="figs"><div><dt>Season total</dt><dd>$' + r.total + '</dd></div>' +
        '<div><dt>Weeks you pay for</dt><dd>' + r.weeks + ' (week ' + r.start + '–20)</dd></div>' +
        '<div class="wide"><dt>First pickup</dt><dd>' + r.first + (r.point === 'farm' ? ' · at the farm' : ' · River Market stand') + '</dd></div>' +
        '<div class="wide"><dt>How to pay</dt><dd>Check or cash at your first pickup</dd></div></dl>' +
        '<p class="math">$' + (r.perWeek / r.count) + ' × ' + r.count + ' share' + (r.count > 1 ? 's' : '') + ' × ' + r.weeks + ' weeks = $' + r.total + '. Last pickup: ' + r.last + '.</p>';
    } else {
      h = '<p class="verdict no">No — not enough room for ' + label(r) + '.</p>' +
        '<p>This request needs ' + fmt(r.need) + ' full-share equivalent' + (r.need === 1 ? '' : 's') + '. Only <strong>' + fmt(r.remaining) + '</strong> remain' +
        (r.size === 'half' || r.remaining % 1 === 0 ? '' : '') + ' — room for <strong>' + r.roomInShares + ' ' + r.size + ' share' + (r.roomInShares === 1 ? '' : 's') + '</strong>' + (r.roomInShares === 0 ? ', none of this size' : '') + '.</p>';
    }
    ans.innerHTML = h + furrows(r) + bar(r) + '<p class="sendsnothing">Worked out on this page. Nothing is sent or saved, and this does not reserve a share.</p>';
  }
  form.addEventListener('change', render);
  window.__csaRender = render;
  render();
})();
