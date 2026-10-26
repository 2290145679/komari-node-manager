// Clear Service Worker and PWA cache to ensure fresh code
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.getRegistrations().then(function(registrations) {
    for (let r of registrations) { r.unregister(); }
  });
}
if ('caches' in window) {
  caches.keys().then(function(names) {
    for (let name of names) { caches.delete(name); }
  });
}

// Ensure plugin iframes are never served from stale browser cache
function ensureFreshIframes() {
  document.querySelectorAll('iframe.km-plugin-frame').forEach(function(iframe) {
    try {
      var src = iframe.getAttribute('src');
      if (src && src.indexOf('/api/admin/plugin/node-manager/') !== -1 && src.indexOf('v=') === -1) {
        iframe.src = src + (src.indexOf('?') !== -1 ? '&' : '?') + 'v=1.2';
      }
    } catch (e) {}
  });
}
setInterval(ensureFreshIframes, 300);
document.addEventListener('DOMContentLoaded', ensureFreshIframes);

console.log('[Komari] Native React sing-box integration active (v4)');