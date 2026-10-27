// Client information forms (T1, T2): section toggles, repeatable entries, and submission.
// The form element carries data-endpoint (where to POST) and data-done (id of the thank-you panel).
(function () {
  var form = document.querySelector('form.intake[data-endpoint]');
  if (!form) return;
  var note = form.querySelector('.form-note');
  var btn = form.querySelector('button[type=submit]');
  var btnText = btn.textContent;
  var done = document.getElementById(form.getAttribute('data-done'));

  // ---- Repeatable entries (T4 slips, schools, loans, properties, dependants) ----
  function renumber(repeat) {
    var items = repeat.querySelectorAll(':scope > .repeat-items > .repeat-item');
    var name = repeat.getAttribute('data-repeat');
    items.forEach(function (item, i) {
      item.querySelector('.repeat-label').textContent = name + ' ' + (i + 1);
    });
  }

  function addItem(repeat, focus) {
    var tpl = repeat.querySelector(':scope > template');
    var list = repeat.querySelector(':scope > .repeat-items');
    var node = tpl.content.firstElementChild.cloneNode(true);
    list.appendChild(node);
    renumber(repeat);
    if (focus) {
      var first = node.querySelector('input, select, textarea');
      if (first) first.focus();
    }
  }

  document.querySelectorAll('.repeat').forEach(function (repeat) {
    var start = parseInt(repeat.getAttribute('data-start') || '0', 10);
    for (var i = 0; i < start; i++) addItem(repeat, false);
    repeat.querySelector(':scope > .add').addEventListener('click', function () { addItem(repeat, true); });
    repeat.addEventListener('click', function (e) {
      if (e.target.classList.contains('remove')) {
        e.target.closest('.repeat-item').remove();
        renumber(repeat);
      }
    });
  });

  // ---- Section toggles ----
  document.querySelectorAll('.toggle input[data-target]').forEach(function (box) {
    var section = document.getElementById(box.getAttribute('data-target'));
    function sync() { section.hidden = !box.checked; }
    box.addEventListener('change', sync);
    sync();
  });

  // ---- Collect answers ----
  function labelOf(q) {
    if (q.tagName === 'FIELDSET') return q.querySelector('legend').textContent.trim();
    var span = q.querySelector(':scope > span');
    return span ? span.textContent.replace(/\s*\*$/, '').trim() : '';
  }

  function valueOf(q) {
    if (q.tagName === 'FIELDSET') {
      return Array.prototype.map.call(q.querySelectorAll('input[type=checkbox]:checked'), function (c) { return c.value; }).join(', ');
    }
    var el = q.querySelector('input, select, textarea');
    if (!el) return '';
    var v = (el.value || '').trim();
    if (v && el.getAttribute('placeholder') === '$' && v.charAt(0) !== '$') v = '$' + v;
    if (el.type === 'date' && v) {
      var d = new Date(v + 'T12:00:00');
      if (!isNaN(d)) v = d.toLocaleDateString('en-CA', { year: 'numeric', month: 'short', day: 'numeric' });
    }
    return v;
  }

  function rowsIn(container) {
    var rows = [];
    container.querySelectorAll('.q').forEach(function (q) {
      if (q.closest('.repeat') && !container.classList.contains('repeat-item')) return;
      var v = valueOf(q);
      if (v) rows.push({ label: labelOf(q), value: v });
    });
    return rows;
  }

  function collectSection(section) {
    var items = [];
    // Walk the section's direct building blocks in page order.
    section.querySelectorAll(':scope > .form-grid, :scope > .checks-group, :scope > .repeat, :scope > h3').forEach(function (block) {
      if (block.tagName === 'H3') {
        items.push({ heading: block.textContent.trim() });
      } else if (block.classList.contains('repeat')) {
        block.querySelectorAll(':scope > .repeat-items > .repeat-item').forEach(function (item) {
          var rows = rowsIn(item);
          if (rows.length) items.push({ group: item.querySelector('.repeat-label').textContent, rows: rows });
        });
      } else if (block.classList.contains('checks-group')) {
        var v = valueOf(block);
        if (v) items.push({ rows: [{ label: labelOf(block), value: v }] });
      } else {
        var rows = rowsIn(block);
        if (rows.length) items.push({ rows: rows });
      }
    });
    // Drop headings that have nothing after them.
    return items.filter(function (it, i) {
      if (!it.heading) return true;
      var next = items[i + 1];
      return next && !next.heading;
    });
  }

  function collect() {
    var sections = [];
    form.querySelectorAll('.intake-section[data-section]').forEach(function (section) {
      if (section.hidden) return;
      var items = collectSection(section);
      if (items.length) sections.push({ title: section.getAttribute('data-section'), items: items });
    });
    return sections;
  }

  // ---- Submit ----
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var first = form.querySelector('[name=first_name]');
    var last = form.querySelector('[name=last_name]');
    var email = form.querySelector('[name=email]');
    var consent = form.querySelector('.consent input');
    var company = form.querySelector('[name=company]');

    var requiredCompany = company && company.required ? company : null;
    var missing = [requiredCompany, first, last, email].filter(function (el) { return el && !el.value.trim(); });
    if (missing.length || !email.checkValidity()) {
      var companyLabel = company ? company.closest('label').querySelector('span').textContent.replace(/\s*\*$/, '').trim().toLowerCase() : '';
      note.textContent = requiredCompany
        ? 'Please fill in the ' + companyLabel + ', your first and last name, and a valid email address.'
        : 'Please fill in your first name, last name and a valid email address.';
      (missing[0] || email).focus();
      return;
    }
    var badPattern = Array.prototype.find.call(form.querySelectorAll('input[pattern]'), function (el) {
      return !el.closest('[hidden]') && el.value.trim() && !el.checkValidity();
    });
    if (badPattern) {
      note.textContent = 'For your security, please enter only the last 3 digits of a SIN.';
      badPattern.focus();
      return;
    }
    if (!consent.checked) {
      note.textContent = 'Please tick the confirmation box before submitting.';
      consent.focus();
      return;
    }

    var applies = Array.prototype.map.call(form.querySelectorAll('.toggle input:checked'), function (c) {
      return c.closest('.toggle').querySelector('b').textContent;
    });

    var payload = {
      firstName: first.value.trim(),
      lastName: last.value.trim(),
      email: email.value.trim(),
      phone: (form.querySelector('[name=phone]').value || '').trim(),
      company: company ? company.value.trim() : '',
      applies: applies,
      sections: collect(),
      website: (form.querySelector('.hp input') || {}).value || ''
    };

    btn.disabled = true;
    btn.textContent = 'Submitting…';
    note.textContent = '';

    fetch(form.getAttribute('data-endpoint'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
      .then(function (res) { return res.json().catch(function () { return { ok: false }; }); })
      .then(function (data) {
        if (!data.ok) throw new Error(data.error || '');
        form.hidden = true;
        done.hidden = false;
        done.focus();
        window.scrollTo({ top: done.getBoundingClientRect().top + window.scrollY - 100 });
      })
      .catch(function (err) {
        btn.disabled = false;
        btn.textContent = btnText;
        var generic = 'Sorry, something went wrong. Please try again, or email us at info@calcitax.com.';
        note.textContent = (err && err.message && !(err instanceof TypeError)) ? err.message : generic;
      });
  });
})();
