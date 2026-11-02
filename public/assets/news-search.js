/* News page: instant search and topic filter.
   Article text is loaded from /news/search.json only when someone starts typing. */
(function () {
  var input = document.getElementById('news-q');
  var list = document.getElementById('news-list');
  if (!input || !list) return;
  var cards = Array.prototype.slice.call(list.querySelectorAll('.news-card'));
  var chips = Array.prototype.slice.call(document.querySelectorAll('.chip'));
  var count = document.getElementById('news-count');
  var empty = document.getElementById('news-empty');
  var index = null, loading = null, cat = '';

  function norm(s) {
    return (s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[’']/g, "'");
  }
  // Text available before search.json loads: what is on the card itself.
  var cardText = {};
  cards.forEach(function (c) { cardText[c.dataset.slug] = norm(c.textContent); });

  function loadIndex() {
    if (index || loading) return loading;
    loading = fetch('/news/search.json', { cache: 'no-cache' })
      .then(function (r) { return r.ok ? r.json() : []; })
      .then(function (data) {
        index = {};
        data.forEach(function (a) {
          index[a.slug] = norm([a.title, a.description, a.category, a.text].join(' '));
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
      var hay = (index && index[c.dataset.slug]) || cardText[c.dataset.slug] || '';
      var ok = (!cat || c.dataset.category === cat) &&
               words.every(function (w) { return hay.indexOf(w) !== -1; });
      c.hidden = !ok;
      if (ok) shown++;
    });
    empty.hidden = shown !== 0;
    if (words.length || cat) {
      count.textContent = shown + (shown === 1 ? ' article' : ' articles') +
        (cat ? ' in ' + cat : '') + (words.length ? ' matching “' + input.value.trim() + '”' : '');
    } else {
      count.textContent = '';
    }
    var params = new URLSearchParams();
    if (input.value.trim()) params.set('q', input.value.trim());
    if (cat) params.set('topic', cat);
    var qs = params.toString();
    history.replaceState(null, '', location.pathname + (qs ? '?' + qs : ''));
  }

  function setCat(value) {
    cat = value;
    chips.forEach(function (ch) { ch.setAttribute('aria-pressed', String(ch.dataset.cat === cat)); });
    apply();
  }

  input.addEventListener('input', function () { loadIndex(); apply(); });
  input.addEventListener('focus', loadIndex);
  chips.forEach(function (ch) { ch.addEventListener('click', function () { setCat(ch.dataset.cat); }); });

  // Support shareable links such as /news/?topic=Newcomers or /news/?q=RRSP
  var start = new URLSearchParams(location.search);
  if (start.get('q')) { input.value = start.get('q'); loadIndex(); }
  var topic = start.get('topic');
  if (topic && chips.some(function (ch) { return ch.dataset.cat === topic; })) setCat(topic);
  else if (start.get('q')) apply();
})();
