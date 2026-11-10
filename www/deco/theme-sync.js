// Per-user dashboard theme.
// Each person picks a theme in their own input_select.dashboard_theme_<name>. This module (loaded as a
// Lovelace resource) applies that choice to the signed-in user only, via the frontend's own `settheme`
// event, which HA also saves to that user's profile. It replaces the old automation that set the
// server-wide default theme and so changed everyone's theme at once.
(() => {
  if (window.__decoThemeSync) return;
  window.__decoThemeSync = true;
  const THEMES = {'Deco Noir': 'deco_noir', 'Deco Noir Lite': 'deco_noir_lite',
                  'Les Saisons': 'les_saisons', 'Cogitator': 'cogitator'};
  let sent = null;
  const tick = () => {
    const app = document.querySelector('home-assistant');
    const hass = app && app.hass;
    if (!hass || !hass.user || !hass.themes || !hass.themes.themes) return;
    const helper = 'input_select.dashboard_theme_' + hass.user.name.toLowerCase().replace(/[^a-z0-9]+/g, '_');
    const want = THEMES[hass.states[helper] && hass.states[helper].state];
    if (!want || !hass.themes.themes[want]) return;
    const have = hass.selectedTheme && hass.selectedTheme.theme;
    if (have === want) { sent = null; return; }
    if (sent === want) return;          // already asked; wait for the frontend to catch up
    sent = want;
    app.dispatchEvent(new CustomEvent('settheme', {detail: {theme: want}}));
  };
  setInterval(tick, 1000);
  tick();
})();
