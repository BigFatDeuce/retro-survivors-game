'use strict';
// ---------------------------------------------------------------- 0.99: the daily challenge (défi du jour)
// A new challenge every day at 12:00 (local time): a zone among the ones the profile has opened, a class, and 3 maluses
// drawn among the character's (10 to 20 %) and the monsters' (5 to 10 %), the character's max HP always halved, always in
// Endless mode. Surviving C.daily.goal
// seconds pays C.daily.reward kamas (Normal) or C.daily.rewardHard (Difficile), once per challenge; it can be tried again
// as often as wanted, each try in the leaderboard (its own table, with its maluses). The same day gives the same
// challenge (a seeded draw: the date, the profile's opened zones). Daily: the draw; Run: the maluses; UI: its window.
const DAILY_MODS = {   // k: [who, min %, max %] — 'p' the character, 'm' the monsters
  speed: ['p', 10, 20], might: ['p', 10, 20], cooldown: ['p', 10, 20], area: ['p', 10, 20], heal: ['p', 10, 20],   // (0.99: 10-20 %, 5-10 before; max HP is always halved)
  mhp: ['m', 5, 10], mdmg: ['m', 5, 10], mspeed: ['m', 5, 10], matk: ['m', 5, 10],
};
const Daily = {
  // the challenge's day: it changes at noon (before 12:00, yesterday's)
  key(now = new Date()) { const d = new Date(now.getTime() - 12 * 3600e3), p = n => String(n).padStart(2, '0'); return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`; },
  nextReset(now = new Date()) { const d = new Date(now); d.setHours(12, 0, 0, 0); if (d <= now) d.setDate(d.getDate() + 1); return d; },
  rng(str) { let h = 1779033703 ^ str.length; for (let i = 0; i < str.length; i++) { h = Math.imul(h ^ str.charCodeAt(i), 3432918353); h = (h << 13) | (h >>> 19); }
    return () => { h = Math.imul(h ^ (h >>> 16), 2246822507); h = Math.imul(h ^ (h >>> 13), 3266489909); h ^= h >>> 16; return (h >>> 0) / 4294967296; }; },
  zones(C, S) { return C.maps.filter(m => !m.hidden && !m.hardOnly && (S.unlocked || []).includes(m.id)); },
  today(C, S) {
    const key = this.key(), zs = this.zones(C, S), r = this.rng(key + '|' + zs.map(m => m.id).join(','));
    const map = zs[Math.floor(r() * zs.length)] || C.maps[0], cls = C.classes[Math.floor(r() * C.classes.length)];
    const pool = Object.keys(DAILY_MODS), mods = [];
    while (mods.length < 3 && pool.length) { const k = pool.splice(Math.floor(r() * pool.length), 1)[0], [, a, b] = DAILY_MODS[k]; mods.push({ k, v: (a + Math.floor(r() * (b - a + 1))) / 100 }); }
    const D = C.daily || {};
    return { key, map: map.id, cls: cls.id, mods, goal: D.goal || 600, reward: D.reward || 5000, rewardHard: D.rewardHard || 10000 };
  },
  claimed(S, key) { return !!(S.daily && S.daily[key]); },
  modText(m) { return T('dm_' + m.k, { n: Math.round(m.v * 100) }); },
};
Object.assign(Run.prototype, {
  // the character's maluses, at the end of Run.recompute
  dailyStats(st) {
    st.speed *= 1 - this.dmod('speed'); st.might *= 1 - this.dmod('might'); st.maxHp *= 0.5;   // (every challenge: max HP halved)
    st.cooldown *= 1 + this.dmod('cooldown'); st.area *= 1 - this.dmod('area'); st.healBonus -= this.dmod('heal');
  },
  // every 2 s (Run.update): the maluses said at the start, the reward when the goal is reached
  dailyTick() {
    const D = this.daily; if (!D) return;
    if (!D.said) { D.said = 1; this.chat('📅 ' + T('daily_title') + ' — ' + [T('dm_halfhp'), ...D.mods.map(Daily.modText)].join(' · '), '#ff9a7a', 20); }
    if (D.paid || this.time < D.goal) return;
    D.paid = 1; const S = Store.data; S.daily = S.daily || {};
    if (S.daily[D.key]) return;   // (paid once per challenge)
    const n = this.hard ? D.rewardHard : D.reward; S.daily[D.key] = { n, t: Date.now() }; S.kamas += n; Store.save();
    this.dailyPaid = n; this.announce(T('daily_title'), T('daily_done', { n: fmtNum(n) }), '#ffd24a', { center: true }); Audio2.fanfare(0.8);
  },
});
Object.assign(UI, {
  // the challenge's window (the play screen's button): what it is, its maluses, its reward, 'Tenter le défi'
  dailyMenu(hard, start) {
    const C = Game.C, S = Store.data, D = Daily.today(C, S), cls = C.classes.find(c => c.id === D.cls), map = C.maps.find(m => m.id === D.map), done = Daily.claimed(S, D.key);
    const close = () => { Audio2.blip('click'); this.closeModal(); };
    const reset = Daily.nextReset(), hh = `${String(reset.getHours()).padStart(2, '0')}:00`;
    const row = (lab, val, kind = 'prop') => h('tr', {}, h('td', {}, lab), h('td', { class: 'fx-' + kind }, val));
    const el = h('div', { class: 'window modal daily' }, h('div', { class: 'title' }, '📅 ' + T('daily_title'), h('button', { class: 'close', onclick: close }, '×')),
      h('div', { class: 'content' },
        h('div', { class: 'daily-top' }, artImg(cls.emblemArt || ('b' + cls.breed), 'daily-emb', 120),
          h('table', { class: 'stats' },
            row(T('st_class'), L(cls.name)), row(T('daily_zone'), L(map.name)), row(T('daily_mode'), '∞ ' + T('mode_infinite') + ' — ' + (hard ? T('mode_hard') : T('mode_normal'))),
            row(T('daily_goal'), fmtTime(D.goal), 'cond'),
            row(T('daily_reward'), done ? T('daily_claimed') : fmtNum(hard ? D.rewardHard : D.reward) + ' K', done ? 'prop' : 'eff'))),
        h('h3', {}, T('daily_mods')),
        h('div', { class: 'daily-mods' }, h('div', { class: 'fx-neg' }, '▼ ' + T('dm_halfhp')), ...D.mods.map(m => h('div', { class: 'fx-neg' }, (DAILY_MODS[m.k][0] === 'p' ? '▼ ' : '▲ ') + Daily.modText(m)))),
        h('p', { class: 'sub' }, T('daily_reset', { t: hh }) + ' ' + T('daily_rewards', { n: fmtNum(D.reward), h: fmtNum(D.rewardHard) })),
        h('div', { class: 'start-row' }, btn(T('back'), close), btn(T('daily_go'), () => { this.closeModal(); start(D); }, 'big orange start-btn'))));
    this.openModal(el);
  },
});
