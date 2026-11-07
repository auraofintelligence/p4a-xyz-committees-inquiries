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
  const places = document.querySelector('.participation-parliament-menu');
  document.addEventListener('click',e=>{if(places?.open && !places.contains(e.target))places.open=false;});
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&places?.open){places.open=false;places.querySelector('summary').focus();}});
  const fold = value => value.toLocaleLowerCase('en-AU').normalize('NFKD').replace(/\p{M}/gu,'');
  const words = value => fold(value).split(/[^\p{L}\p{N}]+/u).filter(Boolean);
  document.querySelector('.council-sections')?.addEventListener('click',event=>{
    const link=event.target.closest('a[href^="#"]');
    const target=link&&document.getElementById(link.hash.slice(1));
    if(!target)return;
    event.preventDefault();
    if(location.hash!==link.hash)history.pushState(null,'',link.hash);
    target.tabIndex=-1;target.focus({preventScroll:true});
    target.scrollIntoView({block:'start',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});
  });
  const bodySearch=document.querySelector('[data-council-body-search]');
  if(bodySearch){
    bodySearch.hidden=false;
    const bodies=[...document.querySelectorAll('[data-council-body]')];
    const updateBodies=()=>{
      const terms=words(bodySearch.elements.search.value);let shown=0;
      for(const body of bodies){body.hidden=!terms.every(term=>fold(body.textContent).includes(term));if(!body.hidden)shown++;}
      for(const group of document.querySelectorAll('[data-body-group]'))group.hidden=![...group.querySelectorAll('[data-council-body]')].some(body=>!body.hidden);
      document.querySelector('[data-body-count]').textContent=`${shown} of ${bodies.length} named bodies shown; inventory may be incomplete.`;
    };
    bodySearch.addEventListener('submit',e=>e.preventDefault());
    bodySearch.addEventListener('input',updateBodies);
    bodySearch.addEventListener('reset',()=>{bodySearch.elements.search.value='';updateBodies();});
    updateBodies();
  }
  const directoryForm = document.querySelector('[data-directory-search]');
  if (directoryForm) {
    directoryForm.hidden=false;
    const entries=[...document.querySelectorAll('[data-directory-row]')];
    const list=document.querySelector('.body-directory');
    const field=directoryForm.elements.search, sort=directoryForm.elements.sort;
    const updateDirectory=()=>{
      let shown=0;
      const terms=words(field.value);
      const sorted=[...entries].sort((a,b)=>(sort.value==='priority'?Number(b.dataset.priority)-Number(a.dataset.priority)||Number(b.dataset.participation)-Number(a.dataset.participation):sort.value==='participation'?Number(b.dataset.participation)-Number(a.dataset.participation):0)||a.dataset.name.localeCompare(b.dataset.name));
      for(const entry of sorted){entry.hidden=!terms.every(term=>fold(entry.dataset.search).includes(term));if(!entry.hidden)shown++;list.append(entry);}
      document.querySelector('[data-directory-count]').textContent=`${shown} of ${entries.length} entries shown.`;
      document.querySelector('[data-directory-empty]').hidden=shown!==0;
    };
    directoryForm.addEventListener('submit',e=>e.preventDefault());
    directoryForm.addEventListener('input',updateDirectory);
    directoryForm.addEventListener('change',updateDirectory);
    directoryForm.addEventListener('reset',()=>{field.value='';sort.value='name';updateDirectory();});
    updateDirectory();
  }
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
  const topic=form.querySelector('[name=topic]'), method=form.querySelector('[name=method]'), body=form.querySelector('[name=body]');
  const params = new URLSearchParams(location.search);
  for (const field of [search, status, order, topic, method, body]) {
    if (params.has(field.name)) field.value = params.get(field.name);
  }
  connected.checked = params.get('connected') === 'yes';
  if(!['all','available','open','upcoming','ongoing','unverified','closed'].includes(status.value))status.value=status.dataset.default;
  function update(save = true) {
    const terms = words(search.value);
    let shown = 0;
    const candidates={all:0};
    const sorted = [...cards].sort((a,b) => {
      const priority = Number(b.dataset.priority) - Number(a.dataset.priority);
      const dates = (a.dataset.deadline || '9999').localeCompare(b.dataset.deadline || '9999');
      if (order.value === 'deadline') return dates || priority;
      if (order.value === 'title') return a.dataset.title.localeCompare(b.dataset.title);
      if (order.value === 'checked') return b.dataset.checked.localeCompare(a.dataset.checked)||priority||dates;
      return priority || dates || a.dataset.title.localeCompare(b.dataset.title);
    });
    for (const card of sorted) {
      const matchStatus = status.value === 'all' || (status.value === 'available' ? ['open','upcoming'].includes(card.dataset.status) : card.dataset.status === status.value);
      const matchJurisdiction = (!jurisdiction.value || jurisdiction.value === card.dataset.jurisdiction) && (!form.dataset.level || form.dataset.level===card.dataset.level);
      const matchesOtherFilters = matchJurisdiction
        && (!connected.checked || Number(card.dataset.priority) > 0)
        && (!topic.value || card.dataset.topics.split(' ').includes(topic.value))
        && (!method.value || method.value===card.dataset.method)
        && (!body.value || body.value===card.dataset.body)
        && terms.every(term=>fold(card.dataset.search).includes(term));
      if(matchesOtherFilters){candidates.all++;candidates[card.dataset.status]=(candidates[card.dataset.status]||0)+1;}
      const visible=matchStatus&&matchesOtherFilters;
      card.hidden = !visible; if (visible) shown++;
      container.append(card);
    }
    const unverifiedCount = candidates.unverified||0;
    const hiddenStatusNote = status.value==='available' && unverifiedCount ? ` ${unverifiedCount} uncertain record${unverifiedCount===1?' is':'s are'} hidden by your selected status filter. Select All records to show everything in this jurisdiction.` : '';
    const active=[];
    if(search.value.trim())active.push(`Search: ${search.value.trim()}`);
    if(status.value!=='all')active.push('Status: '+({available:'Open and upcoming',open:'Open',upcoming:'Upcoming',ongoing:'Standing routes',unverified:'Uncertain',closed:'Closed'}[status.value]));
    for(const [field,label] of [[topic,'Topic'],[method,'Route']])if(field.value)active.push(label+': '+field.selectedOptions[0].text.replace(/ \(\d+\)$/,''));
    if(body.value)active.push('Body: '+body.value);
    if(connected.checked)active.push('P4A matches only');
    count.textContent = `${shown} of ${cards.length} records shown in ${form.dataset.scopeLabel}.${hiddenStatusNote} ${active.length?'Filters: '+active.join('; ')+'.':'All records in this view are visible.'}`;
    form.querySelectorAll('[data-status-choice]').forEach(button=>{button.setAttribute('aria-pressed',String(button.dataset.statusChoice===status.value));button.querySelector('span').textContent=candidates[button.dataset.statusChoice]||0;});
    empty.hidden = shown !== 0;
    if (save) {
      const query = new URLSearchParams();
      for (const field of [search,status,order,topic,method,body]) if (field.value && field.value !== field.dataset.default) query.set(field.name, field.value);
      if (connected.checked) query.set('connected','yes');
      history.replaceState(null,'',location.pathname + (query.size ? '?' + query : '') + location.hash);
    }
  }
  form.addEventListener('submit',e => e.preventDefault());
  form.addEventListener('input',() => update());
  form.addEventListener('change',() => update());
  form.querySelectorAll('[data-status-choice]').forEach(button=>button.addEventListener('click',()=>{status.value=button.dataset.statusChoice;update();}));
  form.querySelector('[data-reset]').addEventListener('click',() => {
    search.value='';status.value=status.dataset.default;jurisdiction.value=jurisdiction.dataset.default;order.value='priority';topic.value='';method.value='';body.value='';connected.checked=false;update();
  });
  window.addEventListener('popstate',() => location.reload());
  update(false);
})();
