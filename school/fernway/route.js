(function () {
  var svg = document.querySelector('.draw');
  var cap = document.querySelector('.cap-route');
  var text = {
    seed: 'From seed: sown in the greenhouse, potted on, then out to the bench.',
    cutting: 'From a cutting: taken from Fernway’s own stock plant, potted on, then out to the bench.'
  };
  document.querySelectorAll('.switch__b').forEach(function (b) {
    b.addEventListener('click', function () {
      var r = b.getAttribute('data-route');
      svg.setAttribute('data-route', r);
      cap.textContent = text[r];
      document.querySelectorAll('.switch__b').forEach(function (o) {
        o.setAttribute('aria-pressed', o === b ? 'true' : 'false');
      });
    });
  });
})();
