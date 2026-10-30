'use strict';
// ---------------------------------------------------------------- lifetime statistics and achievements (succès)
const Prog = {
  st() { const S = Store.data; if (!S.st) S.st = {}; if (!S.ach) S.ach = {}; return S.st; },
  add(k, v = 1) { const st = this.st(); st[k] = (st[k] || 0) + v; },
  max(k, v) { const st = this.st(); if (!(st[k] >= v)) st[k] = v; },
  mainSpellDmg(st, C) {
    if (st.spellDmgMain) return st.spellDmgMain;
    const all = new Set([...C.classes.flatMap(c => c.spells), ...(C.globalSpells || []).map(g => g.id), ...(C.spellFusions || []).map(f => f.id)]), o = {};
    for (const k in st.spellDmg || {}) if (all.has(k)) o[k] = st.spellDmg[k];
    return o;
  },
  bump(map, k, v = 1) { const st = this.st(); st[map] = st[map] || {}; st[map][k] = (st[map][k] || 0) + v; },
  // ---- run hooks
  runStart(R) {
    // 0.61: a run given up in its first 20 s counts in no statistic: what they were before it starts (voidRun)
    const S0 = Store.data; R._stSnap = JSON.stringify({ st: S0.st || {}, kills: S0.kills || {}, totalKills: S0.totalKills || 0 });
    R.ps = { dmgDealt: 0, dmgTaken: 0, crits: 0, bestHit: 0, dodges: 0, gems: 0, chests: 0, breads: 0, elites: 0, bosses: 0, dist: 0, rerolls: 0, levelups: 0,
      firstHit: null, kamas: 0, doomT: 0, spell: {}, killer: {} };
    this.bump('clsRuns', R.cls.id); this.bump('mapRuns', R.map.id);
  },
  dealt(R, src, real, crit) {
    const ps = R.ps; if (!ps) return;
    ps.dmgDealt += real; if (crit) ps.crits++;
    if (real > ps.bestHit) ps.bestHit = real;
    const k = src && src.def ? src.def.id : null; if (k) ps.spell[k] = (ps.spell[k] || 0) + real;
  },
  taken(R, d, src) { const ps = R.ps; if (!ps) return; ps.dmgTaken += d; if (ps.firstHit === null) ps.firstHit = R.time; if (src && src.def) ps.killer[src.def.id] = (ps.killer[src.def.id] || 0) + d; },
  runEnd(R) {
    const ps = R.ps; if (!ps) return; const st = this.st(), S = Store.data;
    this.add('playtime', R.time); this.add('kills', R.kills); this.add('dmgDealt', ps.dmgDealt); this.add('dmgTaken', ps.dmgTaken);
    this.add('crits', ps.crits); this.add('dodges', ps.dodges); this.add('gems', ps.gems); this.add('chests', ps.chests); this.add('breads', ps.breads);
    this.add('elites', ps.elites); this.add('bossKills', ps.bosses); this.add('dist', ps.dist); this.add('rerolls', ps.rerolls); this.add('levelups', ps.levelups);
    this.add('kamasEarned', R.kamas); if (R.player.dead) this.add('deaths');
    this.max('bestHit', Math.round(ps.bestHit)); this.max('bestKills', R.kills); this.max('bestLevel', R.level); this.max('bestTime', Math.floor(R.time)); this.max('bestKamas', R.kamas);
    this.max('bestDoom', Math.floor(ps.doomT));
    this.max('bestRelics', (R.relics || []).length); if (R.infinite) this.max('bestEndless', Math.floor(R.time));
    if ((ps.firstHit === null ? R.time : ps.firstHit) >= 180) st.noHit3 = 1;
    // 0.92: the stats' 'sort n°1' counts only the class's own spells (and its fusions) and the global spells, not
    // one won on the ground (the Trool's wheel: another class's spell) — spellDmgMain, started from the old totals
    // (mainSpellDmg: which run won which spell was not kept); spellDmg itself unchanged
    st.spellDmgMain = this.mainSpellDmg(st, R.C);
    const C = R.C, glob = (C.globalSpells || []).map(g => g.id), own = new Set([...R.cls.spells, ...glob, ...(C.spellFusions || []).filter(f => sfusionOf(f, R.cls.id)).map(f => f.id)]);
    for (const k in ps.spell) { this.bump('spellDmg', k, Math.round(ps.spell[k])); if (own.has(k)) this.bump('spellDmgMain', k, Math.round(ps.spell[k])); }
    for (const k in ps.killer) this.bump('hurtBy', k, Math.round(ps.killer[k]));
    if (R.weapon) this.bump('weaponRuns', R.weapon.def.id);
    if (R.finalKilled) { this.bump('clsWins', R.cls.id); this.bump('mapWins', R.map.id); this.add('wins'); if (R.hard) { this.add('hardWins'); this.bump('hardCls', R.cls.id); } }
    // records (0.22): an abandoned run counts for nothing; the record is the best damage dealt in one second (DPS)
    if (!R.abandoned) {
      const dps = Math.round(Math.max(R.bestDps || 0, R._dpsCur || 0));
      const bd = st.clsDps = st.clsDps || {}; if (!(bd[R.cls.id] >= dps)) bd[R.cls.id] = dps;
      const md = st.mapDps = st.mapDps || {}; if (!(md[R.map.id] >= dps)) md[R.map.id] = dps;
      if (!(st.bestDps >= dps)) st.bestDps = dps;
    }
    this.check(null);
  },
  voidRun(R) {
    if (!R._stSnap) return; const o = JSON.parse(R._stSnap), S = Store.data;
    S.st = o.st; S.kills = o.kills; S.totalKills = o.totalKills;
  },
  // ---- achievements
  value(k) {
    const S = Store.data, st = this.st(), C = Game.C;
    switch (k) {
      case 'runs': return S.runs || 0;
      case 'kills': return S.totalKills || 0;
      case 'wins': return st.wins || 0;
      case 'zonesCleared': return C.maps.filter(m => !m.hidden && S.cleared[m.id]).length;
      case 'secretZones': return C.maps.filter(m => m.hidden && S.unlocked.includes(m.id)).length;
      case 'dofusKinds': return Object.keys(S.dofus || {}).length;
      case 'tot': return S.tot || 0;
      case 'classesWon': return Object.keys(st.clsWins || {}).length;
      // (0.61: 'unused' bosses = in no zone, patch_061: out of the count)
      case 'seenPct': { const all = [...Object.keys(C.monsters), ...Object.keys(C.bosses).filter(b => !C.bosses[b].doom && !C.bosses[b].unused)]; return Math.floor(100 * all.filter(k => S.seen[k]).length / all.length); }
      case 'owned': return (S.owned || []).length;
      case 'pets': return (S.owned || []).filter(i => i.startsWith('18_')).length;
      case 'doomTime': return st.bestDoom || 0;
      // v2.0 shop progress
      case 'spellMaxed': return Object.values(S.spellLv || {}).filter(v => v >= (C.spellCost || [0, 0, 0, 0, 0]).length).length;
      case 'spellClassMax': { const M = (C.spellCost || [0, 0, 0, 0, 0]).length, L = S.spellLv || {}; return C.classes.filter(c => c.spells.every(id => (L[id] || 0) >= M)).length; }
      case 'masteryMax': return Object.values(S.mastery || {}).filter(v => v >= ((C.masteryCost || []).length || 5)).length;   // (0.61: masteries stop at 5 since 0.60: the achievement could never unlock)
      case 'scrollMax': return Object.values(S.scrolls || {}).filter(v => v >= 10).length;
      case 'plumes': return S.plumes || 0;
      // 0.31
      case 'souls': return Object.keys(S.souls || {}).length;
      case 'uniquesKinds': return Object.keys(S.uniques || {}).length;
      case 'uniquesAll': { const U = (C.uniqueWeapons || []).filter(u => !u.blood);   // (0.48: the vampiric weapons apart)
      return U.length && U.every(u => (S.uniques || {})[u.id]) ? 1 : 0; }
      case 'jackpots': return S.jackpots || 0;
      case 'hardClasses': return Object.keys(st.hardCls || {}).length;
      case 'zonesPlayed': return Object.keys(st.mapRuns || {}).length;
      case 'boss_ogivol': return (st.bossById || {}).ogivol || 0;
      case 'ttgCards': return Object.keys(S.ttg || {}).length;   // 0.37
      case 'boss_ougah': return (st.bossById || {}).ougah || 0;
      case 'hardZones': return Object.keys(S.clearedHard || {}).length;   // 0.92
      default: return st[k] || 0;
    }
  },
  check(R) {
    { // a zone opened by achievements (the Île de Nowel: 50)
      const S = Store.data, n = Object.keys(S.ach || {}).length;
      for (const m of (Game.C && Game.C.maps) || []) if (m.unlockAch && n >= m.unlockAch && !S.unlocked.includes(m.id)) { S.unlocked.push(m.id); if (typeof toast === 'function') toast('🔓 ' + L(m.name)); }
    }
    const S = Store.data; this.st();
    const got = [];
    for (const a of Game.C.achievements || []) {
      if (S.ach[a.id]) continue;
      if (this.value(a.k) >= a.n) { S.ach[a.id] = Date.now(); got.push(a); }
    }
    for (const a of got) {
      const msg = T('ach_unlocked', { n: L(a.name) });
      if (R && !R.over) { R.chat('🏆 ' + msg, '#ffd24a'); (R.achToasts || (R.achToasts = [])).push({ a, t: 0 }); }
      else if (typeof toast === 'function') toast('🏆 ' + msg);
      Audio2.ui('right', 0.6);
    }
    // every achievement unlocked: the secret, the level 200 aura (shown when the character stands still)
    if (got.length && this.allDone() && !S.aura200) {
      S.aura200 = Date.now(); const msg = T('aura_secret');
      if (R && !R.over) R.announce(T('aura_secret_t'), '✨ ' + msg, '#e6c3ff'); else if (typeof toast === 'function') toast('✨ ' + msg);
      Audio2.sfx('EVENT', 0.8);
    }
    if (got.length) Store.save();
    return got;
  },
  allDone() { const S = Store.data, A = Game.C.achievements || []; return A.length > 0 && A.every(a => S.ach && S.ach[a.id]); },
  // the secret level 200 aura stays once earned (new achievements added later do not take it away)
  auraLevel() { return (Store.data && Store.data.aura200) || this.allDone() ? 200 : 100; },
};

