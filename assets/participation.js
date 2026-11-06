/* Progressive enhancement: every record and link is present without JavaScript. */
(() => {
  const panel = document.querySelector('[data-mobile-index]');
  const toggle = document.querySelector('[data-index-toggle]');
  const close = document.querySelector('[data-index-close]');
  let returnFocus;
  function closeIndex() {
    panel.hidden = true; toggle.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = ''; returnFocus?.focus();
  }
  if (panel && toggle) {
    toggle.addEventListener('click', () => {
      returnFocus = document.activeElement; panel.hidden = false;
      toggle.setAttribute('aria-expanded', 'true'); document.body.style.overflow = 'hidden'; close.focus();
    });
    close.addEventListener('click', closeIndex);
    panel.addEventListener('keydown', e => {
      if (e.key === 'Escape') closeIndex();
      if (e.key === 'Tab') {
        const links = [...panel.querySelectorAll('button,a[href]')];
        const first = links[0], last = links.at(-1);
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
        if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    });
  }
  document.querySelectorAll('a[href^="https://"]').forEach(link => {
    if (new URL(link.href).origin !== location.origin && new URL(link.href).hostname !== 'p4a.xyz') {
      link.target = '_blank'; link.rel = 'noopener noreferrer';
    }
  });
  const places = document.querySelector('.participation-place-menu');
  document.addEventListener('click',e=>{if(places?.open && !places.contains(e.target))places.open=false;});
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&places?.open){places.open=false;places.querySelector('summary').focus();}});
  const form = document.querySelector('[data-filters]');
  if (!form) return;
  form.hidden = false;
  const cards = [...document.querySelectorAll('[data-record]')];
  const container = document.querySelector('[data-records]');
  const count = document.querySelector('[data-results-count]');
  const empty = document.querySelector('[data-empty]');
  const search = form.querySelector('[name=search]');
  const status = form.querySelector('[name=status]');
  const jurisdiction = form.querySelector('[name=jurisdiction]');
  const order = form.querySelector('[name=order]');
  const connected = form.querySelector('[name=connected]');
  const params = new URLSearchParams(location.search);
  for (const field of [search, status, order]) {
    if (params.has(field.name)) field.value = params.get(field.name);
  }
  connected.checked = params.get('connected') === 'yes';
  function update(save = true) {
    const text = search.value.trim().toLocaleLowerCase('en-AU');
    let shown = 0;
    const sorted = [...cards].sort((a,b) => {
      const priority = Number(b.dataset.priority) - Number(a.dataset.priority);
      const dates = (a.dataset.deadline || '9999').localeCompare(b.dataset.deadline || '9999');
      if (order.value === 'deadline') return dates || priority;
      if (order.value === 'title') return a.dataset.title.localeCompare(b.dataset.title);
      return priority || dates || a.dataset.title.localeCompare(b.dataset.title);
    });
    for (const card of sorted) {
      const matchStatus = status.value === 'all' || (status.value === 'available' ? ['open','upcoming'].includes(card.dataset.status) : card.dataset.status === status.value);
      const matchJurisdiction = !jurisdiction.value || jurisdiction.value === card.dataset.jurisdiction && (jurisdiction.value === 'federal' || card.dataset.level === 'state');
      const visible = matchStatus && matchJurisdiction
        && (!connected.checked || Number(card.dataset.priority) > 0)
        && (!text || card.dataset.search.includes(text));
      card.hidden = !visible; if (visible) shown++;
      container.append(card);
    }
    const unverifiedCount = cards.filter(card=>card.dataset.status==='unverified').length;
    const hiddenStatusNote = status.value==='available' && unverifiedCount ? ` ${unverifiedCount} uncertain record${unverifiedCount===1?' is':'s are'} hidden by your selected status filter. Select All records to show everything in this jurisdiction.` : '';
    count.textContent = `${shown} of ${cards.length} records shown in this jurisdiction.${hiddenStatusNote} ${connected.checked ? 'Showing P4A topic matches.' : ''}`;
    empty.hidden = shown !== 0;
    if (save) {
      const query = new URLSearchParams();
      for (const field of [search,status,jurisdiction,order]) if (field.value && field.value !== field.dataset.default) query.set(field.name, field.value);
      if (connected.checked) query.set('connected','yes');
      history.replaceState(null,'',location.pathname + (query.size ? '?' + query : '') + location.hash);
    }
  }
  form.addEventListener('submit',e => e.preventDefault());
  form.addEventListener('input',() => update());
  form.addEventListener('change',() => update());
  form.querySelector('[data-reset]').addEventListener('click',() => {
    search.value='';status.value=status.dataset.default;jurisdiction.value=jurisdiction.dataset.default;order.value='priority';connected.checked=false;update();
  });
  window.addEventListener('popstate',() => location.reload());
  update(false);
})();
