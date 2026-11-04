(function () {
  var sheet = document.getElementById('sheet');
  var say = document.getElementById('press-say');
  var buttons = document.querySelectorAll('.steps button');
  var lines = [
    "Set: the type is set by hand from the shop's type cases.",
    'Proof: a proof is pulled on the Vandercook and approved before the run.',
    'First colour: printing is one colour at a time, one sheet at a time, on the Chandler & Price.',
    'Next colour: another pass. One colour at a time, one sheet at a time.'
  ];
  function go(n) {
    sheet.setAttribute('data-stage', String(n));
    say.textContent = lines[n];
    buttons.forEach(function (b) {
      b.setAttribute('aria-pressed', b.getAttribute('data-go') === String(n) ? 'true' : 'false');
    });
  }
  buttons.forEach(function (b) {
    b.addEventListener('click', function () { go(Number(b.getAttribute('data-go'))); });
  });
})();
