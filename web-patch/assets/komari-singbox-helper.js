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

// Inject mobile & card optimization styles
(function() {
  function injectStyles() {
    if (document.getElementById('km-style-override')) return;
    const style = document.createElement('style');
    style.id = 'km-style-override';
    style.textContent = `
      .km-server-card {
        border-radius: 20px !important;
        border: 1px solid rgba(226, 232, 240, 0.9) !important;
        box-shadow: 0 2px 14px rgba(0, 0, 0, 0.04) !important;
        margin-bottom: 14px !important;
        transition: all 0.2s ease !important;
        overflow: hidden !important;
      }
      .dark .km-server-card {
        border-color: rgba(63, 63, 70, 0.7) !important;
        background: #18181b !important;
      }
      .km-card-actions {
        display: flex !important;
        align-items: center !important;
        gap: 4px !important;
      }
      .km-card-actions button {
        padding: 4px !important;
        width: 30px !important;
        height: 30px !important;
      }
      @media (max-width: 640px) {
        .rt-BaseDialogScrollPadding {
          padding: 8px !important;
        }
        .rt-DialogContent, .rt-BaseDialogContent {
          max-height: 88vh !important;
          overflow-y: auto !important;
          border-radius: 20px !important;
          width: calc(100vw - 20px) !important;
          max-width: 520px !important;
          margin: auto !important;
          padding: 16px !important;
          box-shadow: 0 16px 40px rgba(0,0,0,0.18) !important;
        }
      }
    `;
    (document.head || document.documentElement).appendChild(style);
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectStyles);
  } else {
    injectStyles();
  }
})();

console.log('[Komari] Node Manager active v10');
