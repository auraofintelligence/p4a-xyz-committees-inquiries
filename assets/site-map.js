/* Navigation review: 17 October 2026. Filtering changes no content or source dates. */
(() => {
  const root = document.querySelector('.human-site-map');
  if (!root) return;
  const input = root.querySelector('#site-map-search');
  const filter = root.querySelector('[data-site-filter]');
  const status = root.querySelector('[data-site-search-status]');
  const groups = [...root.querySelectorAll('[data-site-group]')];
  const items = [...root.querySelectorAll('[data-site-page]')];
  const initial = new Map(groups.map(group => [group, group.open]));
  if (!input || !filter) return;
  filter.hidden = false;
  function update() {
    const words = input.value.toLocaleLowerCase('en-AU').trim().split(/\s+/).filter(Boolean);
    let matches = 0;
    items.forEach(item => {
      item.hidden = !words.every(word => item.dataset.search.includes(word));
      if (!item.hidden) matches++;
    });
    groups.forEach(group => {
      group.hidden = ![...group.querySelectorAll('[data-site-page]')].some(item => !item.hidden);
      group.open = words.length ? !group.hidden : initial.get(group);
    });
    status.textContent = words.length ? `${matches} of ${items.length} pages match. ${matches ? 'Matching groups are open below.' : 'Try a shorter phrase or clear the search.'}` : `${items.length} pages available. Open a group to browse.`;
  }
  input.addEventListener('input', update);
  root.querySelector('[data-site-clear]').addEventListener('click', () => { input.value = ''; update(); input.focus(); });
  root.querySelectorAll('a[href^="#"]').forEach(link => link.addEventListener('click', () => {
    const target = document.getElementById(link.hash.slice(1));
    if (target && target.tagName === 'DETAILS') target.open = true;
  }));
  const hashTarget = document.getElementById(location.hash.slice(1));
  if (hashTarget && hashTarget.tagName === 'DETAILS') hashTarget.open = true;
  update();
})();
