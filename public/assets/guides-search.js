/* Guides page: instant search and audience filter.
   Full guide text is loaded from /news/search.json only when someone starts typing. */
(function () {
  var input = document.getElementById('guide-q');
  if (!input) return;
  var cards = Array.prototype.slice.call(document.querySelectorAll('.guide-group .news-card'));
  var groups = Array.prototype.slice.call(document.querySelectorAll('.guide-group'));
  var chips = Array.prototype.slice.call(document.querySelectorAll('.chip[data-aud]'));
  var count = document.getElementById('guide-count');
  var empty = document.getElementById('guide-empty');
  var index = null, loading = null, aud = '';

  function norm(s) {
    return (s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[’']/g, "'");
  }
  var cardText = {};
  cards.forEach(function (c) { cardText[c.dataset.slug] = norm(c.textContent); });

  function loadIndex() {
    if (index || loading) return loading;
    loading = fetch('/news/search.json', { cache: 'no-cache' })
      .then(function (r) { return r.ok ? r.json() : []; })
      .then(function (data) {
        index = {};
        data.forEach(function (a) {
          if (a.category === 'Guide') index[a.slug] = norm([a.title, a.description, a.text].join(' '));
        });
        apply();
      })
      .catch(function () { index = {}; });
    return loading;
  }

  function apply() {
    var words = norm(input.value).split(/\s+/).filter(Boolean);
    var shown = 0;
    cards.forEach(function (c) {
      var hay = cardText[c.dataset.slug] + ' ' + ((index && index[c.dataset.slug]) || '');
      var ok = (!aud || c.dataset.aud === aud) &&
               words.every(function (w) { return hay.indexOf(w) !== -1; });
      c.hidden = !ok;
      if (ok) shown++;
    });
    groups.forEach(function (g) {
      g.hidden = !g.querySelector('.news-card:not([hidden])');
    });
    empty.hidden = shown !== 0;
    count.textContent = (words.length || aud)
      ? shown + (shown === 1 ? ' guide' : ' guides') + (words.length ? ' matching “' + input.value.trim() + '”' : '')
      : '';
    var params = new URLSearchParams();
    if (input.value.trim()) params.set('q', input.value.trim());
    if (aud) params.set('for', aud);
    var qs = params.toString();
    history.replaceState(null, '', location.pathname + (qs ? '?' + qs : ''));
  }

  function setAud(value) {
    aud = value;
    chips.forEach(function (ch) { ch.setAttribute('aria-pressed', String(ch.dataset.aud === aud)); });
    apply();
  }

  input.addEventListener('input', function () { loadIndex(); apply(); });
  input.addEventListener('focus', loadIndex);
  chips.forEach(function (ch) { ch.addEventListener('click', function () { setAud(ch.dataset.aud); }); });

  // Shareable links such as /guides/?q=rental or /guides/?for=business
  var start = new URLSearchParams(location.search);
  if (start.get('q')) { input.value = start.get('q'); loadIndex(); }
  if (start.get('for') === 'individuals' || start.get('for') === 'business') setAud(start.get('for'));
  else if (start.get('q')) apply();
})();
