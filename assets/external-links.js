/* Shared web-link policy. Relative/local navigation stays in this tab. */
(() => {
  if (window.P4A_LINKS) return;
  function isExternalHref(href, base = location.href) {
    let url, current;
    try { current = new URL(base); url = new URL(href, current); } catch { return false; }
    if (!['http:', 'https:'].includes(url.protocol)) return false;
    // The committees repository continues the same P4A journey across hosts.
    if (url.hostname === 'p4a.xyz') return false;
    if (url.origin !== current.origin) return true;
    // GitHub Pages sibling repositories share an origin but are distinct sites.
    if (current.hostname.endsWith('.github.io')) {
      const repository = current.pathname.split('/').filter(Boolean)[0];
      return Boolean(repository && url.pathname.split('/').filter(Boolean)[0] !== repository);
    }
    return false;
  }
  const managed = new WeakSet();
  function apply(link) {
    if (!link.matches?.('a[href]') || link.hasAttribute('download')) return;
    const href = link.getAttribute('href');
    if (isExternalHref(href)) {
      link.target = '_blank';
      link.relList.add('noopener', 'noreferrer');
      managed.add(link);
    } else if (managed.has(link)) {
      // A reused dynamic anchor may have changed from an external to internal URL.
      link.removeAttribute('target');
      managed.delete(link);
    }
  }
  function scan(root = document) {
    apply(root);
    root.querySelectorAll?.('a[href]').forEach(apply);
  }
  window.P4A_LINKS = { isExternalHref, apply, scan };
  scan();
  new MutationObserver(changes => {
    for (const change of changes) {
      if (change.type === 'attributes') apply(change.target);
      else change.addedNodes.forEach(scan);
    }
  }).observe(document.documentElement, { subtree: true, childList: true, attributes: true, attributeFilter: ['href', 'download'] });
  // Covers an anchor created and activated synchronously before the observer runs.
  for (const type of ['click', 'auxclick']) document.addEventListener(type, event => {
    const link = event.target.closest?.('a[href]');
    if (link) apply(link);
  }, true);
})();
