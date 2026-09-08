/* Frontend-only bootstrap for panel_web. No backend or bot connection is performed here. */

(async () => {
  try {
    loadStylesheet('assets/ui.css');

    const [{ initAccessibility }, { initModals }, { initNavigation }, { initServers }, { initActions }] = await Promise.all([
      import('./accessibility.js'),
      import('./modals.js'),
      import('./navigation.js'),
      import('./servers.js'),
      import('./actions.js'),
    ]);

    initAccessibility();
    initModals();
    initNavigation();
    initServers();
    initActions();
  } catch (error) {
    console.error('v-bot panel initialization failed:', error);
  }
})();

function loadStylesheet(path) {
  if (document.querySelector(`link[href="${path}"]`)) return;
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = path;
  document.head.appendChild(link);
}
