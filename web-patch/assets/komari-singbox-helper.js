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

// Eliminate any legacy duplicate iframes created by cached chunk-plugin_page
function killDuplicateIframes() {
  document.querySelectorAll('iframe.km-plugin-frame').forEach(function(el) {
    try {
      el.remove();
    } catch (e) {}
  });
}
setInterval(killDuplicateIframes, 200);
document.addEventListener('DOMContentLoaded', killDuplicateIframes);

console.log('[Komari] Native React sing-box integration active (v5)');
