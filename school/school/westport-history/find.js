// Find an object — runs only on window.__collection.
(function () {
  var C = window.__collection;
  var FILE = { 'River Room': 'river-room.html', 'Rails Room': 'rails-room.html', 'Sound Room': 'sound-room.html', 'Home Room': 'home-room.html' };
  var SLUG = { 'River Room': 'river', 'Rails Room': 'rails', 'Sound Room': 'sound', 'Home Room': 'home' };
  function yearOf(o) { return parseInt(o.year.match(/\d{4}/)[0], 10); }
  function match(q) {
    q = q.trim();
    if (!q) return C.slice();
    var m;
    if ((m = q.match(/^(\d{4})$/))) { var y = +m[1]; return C.filter(function (o) { return yearOf(o) === y; }); }
    if ((m = q.match(/^(\d{3})0s$/i))) { var d = +m[1] * 10; return C.filter(function (o) { var y = yearOf(o); return y >= d && y <= d + 9; }); }
    var s = q.toLowerCase();
    return C.filter(function (o) {
      return [o.name, o.maker, o.donor, o.category].some(function (f) { return f.toLowerCase().indexOf(s) !== -1; });
    });
  }
  window.__find = match;
  var q = document.getElementById('q'), list = document.getElementById('results'), count = document.getElementById('count');
  function pad(n) { return n < 10 ? '0' + n : '' + n; }
  function el(tag, cls, text) { var x = document.createElement(tag); if (cls) x.className = cls; if (text != null) x.textContent = text; return x; }
  function render() {
    var r = match(q.value);
    count.textContent = r.length ? r.length + (r.length === 1 ? ' object' : ' objects') : 'No objects match.';
    list.textContent = '';
    r.forEach(function (o) {
      var li = el('li', 'row room-' + SLUG[o.room]); li.setAttribute('data-obj', o.number);
      li.appendChild(el('span', 'rn', 'No. ' + pad(o.number)));
      var nm = el('span', 'rname'), a = el('a', null, o.name); a.href = FILE[o.room] + '#obj-' + o.number; a.setAttribute('data-f', 'name'); nm.appendChild(a); li.appendChild(nm);
      var y = el('span', 'ryear', o.year); y.setAttribute('data-f', 'year'); li.appendChild(y);
      var rm = el('span', 'rroom', o.room); rm.setAttribute('data-f', 'room'); li.appendChild(rm);
      list.appendChild(li);
    });
  }
  q.addEventListener('input', render);
  document.getElementById('clear').addEventListener('click', function () { q.value = ''; render(); q.focus(); });
  [].forEach.call(document.querySelectorAll('[data-try]'), function (b) {
    b.addEventListener('click', function () { q.value = b.getAttribute('data-try'); render(); });
  });
  var u = new URLSearchParams(location.search).get('q'); if (u) { q.value = u; document.getElementById('find-h').scrollIntoView(); }
  render();
})();
