// ---------------------------------------------------------------- 0.95: the installed builds tell when a newer version is out
// The Windows / Linux exe (IS_APP: 'rs://') and the APK (window.RSAndroid) ask GitHub for the public repository's
// releases (C.update.repo, at most every C.update.hours: GitHub allows 60 calls an hour per address) and, when one is
// newer than BUILD, the main menu says so: a window once a day per version, and a button under the menu until it is
// installed. Its button opens the release's page in the browser (the files are there: zip, APK, AppImage, manuals).
// The web version is always the latest: nothing. No answer (offline, the repository still private): nothing either.
Object.assign(UI, {
  updApp() { return (typeof IS_APP !== 'undefined' && IS_APP) || typeof window.RSAndroid !== 'undefined' || !!(Game.debug && Game.debug.updtest); },
  verNum(v) { return String(v || '').replace(/^v/i, '').split('.').map(n => parseInt(n, 10) || 0); },
  newer(a, b) { const x = this.verNum(a), y = this.verNum(b); for (let i = 0; i < Math.max(x.length, y.length); i++) { const d = (x[i] || 0) - (y[i] || 0); if (d) return d > 0; } return false; },
  // the newest release (pre-releases too: the game is a beta), from the cache when it is recent
  async updFetch() {
    const U = Game.C.update || {}, St = Store.data.settings, c = St.upd;
    if (c && Date.now() - c.at < (U.hours || 6) * 3600e3) return c.tag ? c : null;
    let rel = null;
    try {
      const api = (Game.debug && Game.debug.updapi) || `https://api.github.com/repos/${U.repo}/releases?per_page=10`;
      const r = await fetch(api, { headers: { Accept: 'application/vnd.github+json' }, cache: 'no-store' });
      if (!r.ok) throw 0;
      rel = (await r.json()).filter(x => x && !x.draft && x.tag_name).sort((a, b) => this.newer(a.tag_name, b.tag_name) ? -1 : this.newer(b.tag_name, a.tag_name) ? 1 : 0)[0] || null;
    } catch (e) { return null; }   // (offline or refused: asked again at the next launch)
    St.upd = Object.assign({}, c, { at: Date.now(), tag: rel ? rel.tag_name : '', url: rel ? rel.html_url : '' }); Store.save();
    return rel ? St.upd : null;
  },
  async updateCheck(menu) {
    if (!this.updApp() || this._updBusy) return; this._updBusy = true;
    const u = await this.updFetch().catch(() => null); this._updBusy = false;
    if (!u || !this.newer(u.tag, BUILD) || this.screen !== 'main' || !menu.isConnected) return;
    const v = u.tag.replace(/^v/i, ''), foot = menu.querySelector('.main-foot');
    if (foot && !foot.querySelector('.upd-badge')) foot.append(h('button', { class: 'upd-badge', onclick: () => { Audio2.blip('click'); this.updateNotice(u); } }, '⬆ ', T('upd_badge', { v })));
    const St = Store.data.settings, day = new Date().toDateString();
    if (this.modal || (St.updSeen && St.updSeen.tag === u.tag && St.updSeen.day === day)) return;   // (once a day per version)
    St.updSeen = { tag: u.tag, day }; Store.save(); this.updateNotice(u);
  },
  updateNotice(u) {
    const v = u.tag.replace(/^v/i, ''), close = () => { Audio2.blip('click'); this.closeModal(); };
    const go = h('a', { class: 'btn orange big', href: u.url, target: '_blank', rel: 'noopener', 'data-nav-first': '', onclick: (e) => {
      Audio2.blip('click'); setTimeout(() => this.closeModal(), 50);
      // (a controller's A clicks it by script: open it ourselves — the desktop app opens the browser from main.js)
      if (!e.isTrusted) { e.preventDefault(); const w = window.open(u.url, '_blank'); if (w) w.opener = null; }
    } }, '⬇ ', T('upd_get'));
    const el = h('div', { class: 'window modal upd-win' }, h('div', { class: 'title' }, '⬆ ', T('upd_title'), h('button', { class: 'close', onclick: close }, '×')),
      h('div', { class: 'content' }, h('p', { class: 'upd-txt' }, T('upd_text', { v, cur: BUILD })), h('p', { class: 'upd-how' }, T('upd_how')),
        h('div', { class: 'start-row' }, btn(T('later'), close), go)));
    this.openModal(el);
  },
});
