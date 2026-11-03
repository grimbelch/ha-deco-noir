// Themed dropdown for input_select.dashboard_theme, styled with the Deco Noir variables
// (--deco-*). A native <select> popup is drawn by the OS and cannot be themed, so this
// renders its own listbox. Used inside the Deco lobby card.
class DecoThemePicker extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({mode: 'open'});
    this.open = false;
    this._outside = e => { if (!e.composedPath().includes(this)) this.close(); };
  }
  setConfig(config) {
    this.config = config;
    this.shadowRoot.innerHTML = `<style>
      :host{display:block}
      .wrap{position:relative;display:flex;justify-content:flex-end}
      button.trigger{display:inline-flex;align-items:center;gap:8px;padding:6px 11px 6px 9px;min-height:32px;cursor:pointer;
        border:1px solid var(--deco-hair-faint);background:rgba(255,255,255,.02);color:var(--deco-ivory);
        font:400 10px/1 var(--deco-label);letter-spacing:.18em;text-transform:uppercase;white-space:nowrap}
      button.trigger:hover,button.trigger[aria-expanded=true]{border-color:var(--deco-hair);background:rgba(255,255,255,.05)}
      button:focus-visible{outline:1px solid var(--deco-gold-hi);outline-offset:2px}
      ha-icon{--mdc-icon-size:15px;color:var(--deco-gold)}
      .lab{color:rgba(237,230,214,.6)}
      b{font-weight:600;letter-spacing:.12em;color:var(--deco-ivory)}
      .caret{width:0;height:0;margin-left:2px;border-left:4px solid transparent;border-right:4px solid transparent;border-top:5px solid var(--deco-gold);transition:transform .15s}
      .trigger[aria-expanded=true] .caret{transform:rotate(180deg)}
      ul{position:absolute;right:0;bottom:calc(100% + 6px);z-index:20;margin:0;padding:4px;list-style:none;min-width:210px;
        background:var(--deco-midnight,#11131C);border:1px solid var(--deco-hair);box-shadow:0 10px 28px rgba(0,0,0,.55)}
      ul:focus,ul:focus-visible{outline:none}
      ul[hidden]{display:none}
      li{display:flex;align-items:center;gap:10px;padding:9px 12px;cursor:pointer;color:rgba(237,230,214,.75);
        font:400 11px/1 var(--deco-label);letter-spacing:.2em;text-transform:uppercase;white-space:nowrap}
      li:before{content:'\\25C6';font-size:7px;color:transparent}
      li[aria-selected=true]{color:var(--deco-gold-hi)}li[aria-selected=true]:before{color:var(--deco-gold)}
      li.active,li:hover{background:rgba(201,164,76,.12);color:var(--deco-ivory)}
      @media(prefers-reduced-motion:reduce){.caret{transition:none}}
    </style>
    <div class="wrap">
      <button class="trigger" type="button" aria-haspopup="listbox" aria-expanded="false" aria-label="Dashboard theme">
        <ha-icon icon="mdi:palette-swatch-outline"></ha-icon><span class="lab">Theme</span><b></b><span class="caret" aria-hidden="true"></span>
      </button>
      <ul role="listbox" aria-label="Dashboard theme" tabindex="-1" hidden></ul>
    </div>`;
    this.trigger = this.shadowRoot.querySelector('button');
    this.value = this.shadowRoot.querySelector('b');
    this.list = this.shadowRoot.querySelector('ul');
    this.trigger.onclick = () => this.open ? this.close() : this.show();
    this.trigger.onkeydown = e => {
      if (['ArrowDown', 'ArrowUp', 'Enter', ' '].includes(e.key)) { e.preventDefault(); this.show(); }
    };
    this.list.onkeydown = e => this.key(e);
    this.render();
  }
  set hass(hass) { this._hass = hass; this.render(); }
  getCardSize() { return 1; }
  get state() { return this._hass && this._hass.states[this.config.entity]; }
  options() { return (this.state && this.state.attributes.options) || []; }
  render() {
    if (!this.list) return;
    const st = this.state;
    this.value.textContent = st ? st.state : '—';
    if (this.open) return;                       // do not rebuild the list while the user is choosing
    this.list.replaceChildren(...this.options().map(o => {
      const li = document.createElement('li');
      li.setAttribute('role', 'option');
      li.setAttribute('aria-selected', String(st && st.state === o));
      li.textContent = o;
      li.onclick = () => this.choose(o);
      return li;
    }));
  }
  show() {
    this.open = true;
    this.trigger.setAttribute('aria-expanded', 'true');
    this.list.hidden = false;
    const items = [...this.list.children];
    this.index = Math.max(0, items.findIndex(li => li.getAttribute('aria-selected') === 'true'));
    this.mark();
    this.list.focus();
    document.addEventListener('pointerdown', this._outside, true);
  }
  close(focus = false) {
    this.open = false;
    this.trigger.setAttribute('aria-expanded', 'false');
    this.list.hidden = true;
    document.removeEventListener('pointerdown', this._outside, true);
    if (focus) this.trigger.focus();
    this.render();
  }
  mark() {
    [...this.list.children].forEach((li, i) => li.classList.toggle('active', i === this.index));
  }
  key(e) {
    const n = this.list.children.length;
    if (e.key === 'ArrowDown') { this.index = (this.index + 1) % n; this.mark(); }
    else if (e.key === 'ArrowUp') { this.index = (this.index - 1 + n) % n; this.mark(); }
    else if (e.key === 'Home') { this.index = 0; this.mark(); }
    else if (e.key === 'End') { this.index = n - 1; this.mark(); }
    else if (e.key === 'Enter' || e.key === ' ') { this.choose(this.list.children[this.index].textContent); }
    else if (e.key === 'Escape' || e.key === 'Tab') { this.close(true); return; }
    else return;
    e.preventDefault();
  }
  async choose(option) {
    this.close(true);
    try {
      await this._hass.callService('input_select', 'select_option', {entity_id: this.config.entity, option});
    } catch (err) { console.warn('deco-theme-picker:', err); }
  }
  disconnectedCallback() { document.removeEventListener('pointerdown', this._outside, true); }
}
if (!customElements.get('deco-theme-picker')) customElements.define('deco-theme-picker', DecoThemePicker);
window.customCards = window.customCards || [];
window.customCards.push({type: 'deco-theme-picker', name: 'Deco theme picker', description: 'Themed dashboard theme dropdown'});
