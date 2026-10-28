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

console.log('[Komari] Pure Native React Node Manager active (Zero Iframe)');
