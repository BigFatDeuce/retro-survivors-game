'use strict';
// ---------------------------------------------------------------- math / rng
const TAU = Math.PI * 2;
const ES = 1.5; // entity draw scale relative to Dofus 1x
const clamp = (v, a, b) => v < a ? a : v > b ? b : v;
const lerp = (a, b, t) => a + (b - a) * t;
const bossHp = (hp) => Math.ceil(hp / 1000) * 1000;   // bosses always have a round number of HP (next 1000 up)
function segDist(px, py, ax, ay, bx, by) { // distance from point P to segment AB
  const vx = bx - ax, vy = by - ay, l2 = vx * vx + vy * vy || 1;
  const k = clamp(((px - ax) * vx + (py - ay) * vy) / l2, 0, 1);
  return Math.hypot(px - ax - vx * k, py - ay - vy * k);
}
function fnv1a(bytes) { let h = 0x811c9dc5; for (let i = 0; i < bytes.length; i++) { h ^= bytes[i]; h = Math.imul(h, 0x01000193) >>> 0; } return h >>> 0; }   // (0.60: the save code's checksum)
const dist2 = (ax, ay, bx, by) => { const dx = ax - bx, dy = ay - by; return dx * dx + dy * dy; };
const rand = (a = 1, b) => b === undefined ? Math.random() * a : a + Math.random() * (b - a);
const randi = (a, b) => Math.floor(a + Math.random() * (b - a + 1));
const pick = arr => arr[(Math.random() * arr.length) | 0];
function shuffle(a) { for (let i = a.length - 1; i > 0; i--) { const j = (Math.random() * (i + 1)) | 0;[a[i], a[j]] = [a[j], a[i]]; } return a; }
function weighted(list) { // [[item, w], ...]
  let t = 0; for (const [, w] of list) t += w;
  let r = Math.random() * t;
  for (const [it, w] of list) { r -= w; if (r <= 0) return it; }
  return list[list.length - 1][0];
}
function hexToRgb(h) { h = h.replace('#', ''); return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)]; }
function hsl2rgb(h, s, l) {
  const k = n => (n + h / 30) % 12, a = s * Math.min(l, 1 - l);
  const f = n => l - a * Math.max(-1, Math.min(k(n) - 3, Math.min(9 - k(n), 1)));
  return [Math.round(f(0) * 255), Math.round(f(8) * 255), Math.round(f(4) * 255)];
}
// 0.91: a class sprite's own colours — the client's look with no colours of its own (C.classes[].baseColors by
// sprite id, tools/research/classcolors091.py): a class not coloured yet starts with them, the palette's ↺ puts them back
function baseColors(cls, sex) { const b = cls && cls.baseColors && cls.baseColors[cls.sprites[sex || 0]]; return b ? b.map(c => hexToRgb(c || '#808080')) : randomColors(); }
function randomColors() {
  // three harmonious-but-random colours (hair / outfit / accents)
  const h0 = rand(360);
  return [
    hsl2rgb((h0 + rand(-20, 20) + 360) % 360, rand(0.45, 0.85), rand(0.32, 0.6)),
    hsl2rgb((h0 + rand(100, 260)) % 360, rand(0.35, 0.8), rand(0.3, 0.62)),
    hsl2rgb(rand(360), rand(0.2, 0.75), rand(0.25, 0.7)),
  ];
}
function fmtTime(s) { s = Math.max(0, Math.floor(s)); return String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0'); }
const LOCALES = { fr: 'fr-FR', en: 'en-GB', de: 'de-DE', es: 'es-ES', it: 'it-IT', nl: 'nl-NL', pt: 'pt-BR' };
// (0.95: one Intl.NumberFormat per language — toLocaleString built a formatter at every call: 5 % of a crowded frame)
const _NF = {};
function fmtNum(n) { const l = LOCALES[LANG] || 'fr-FR'; try { return (_NF[l] || (_NF[l] = new Intl.NumberFormat(l))).format(Math.floor(n)); } catch (e) { return String(Math.floor(n)); } }

// ---------------------------------------------------------------- storage (guarded)
// v2.0: three profiles on the same device. Profile 1 keeps the original key (old saves stay where they were);
// the settings (language, volumes, theme…) belong to the device and follow the player from one profile to another.
const Store = {
  base: 'krosmoz-survivors-v1', metaKey: 'krosmoz-survivors-profiles', NPROF: 3,
  key: 'krosmoz-survivors-v1',
  data: null, prof: 1,
  // 0.59: the save format's version, written in every save and exported file (a save made before 0.59 has none: 0). A
  // change of the format bumps SAVE_V and adds its step to migrate(), which every load and import goes through
  SAVE_V: 2,
  migrate(d) {
    if (!d || typeof d !== 'object') return d;
    // (0 -> 1: nothing to convert, the number is new)
    if ((d.v || 0) < 2) {   // 1 -> 2 (0.95): the Normal wins apart (beginners' help, Ganymède's tutorials), Difficile locked until Grobe is won
      const cl = d.cleared || {}, ch = d.clearedHard || {}; d.clearedNormal = d.clearedNormal || {};
      for (const k in cl) { const n = (+cl[k] || 0) - (+ch[k] || 0); if (n > 0) d.clearedNormal[k] = n; }   // (won more often than in Difficile: in Normal)
      d.tuto = d.tuto || {}; for (const k in d.clearedNormal) d.tuto[k] = 1;   // (no tutorial on a zone already won)
      if (cl.grobe) d.hardUnlocked = 1;
    }
    d.v = this.SAVE_V; return d;
  },
  hardOk() { return !!(this.data && this.data.hardUnlocked); },   // 0.95: Difficile opens once Grobe is won (Run.claimVictory)
  defaults() {
    return {
      v: this.SAVE_V, kamas: 0, owned: [], equip: {}, unlocked: ['astrub'], best: {}, cleared: {}, clearedNormal: {}, tuto: {}, hardUnlocked: 0, mastery: {}, scrolls: {}, spellLv: {},
      seen: {}, kills: {}, dofus: {}, tot: 0, runs: 0, totalKills: 0,
      settings: { music: 0.75, sfx: 0.75, lang: null, autoPick: null, dmgNumbers: true, shake: true, chat: true, quality: 'uhd', fx: 'full', zoom: 'normal' },   // (0.95: fx 'full' | 'low' | 'min', zoom 'far' | 'normal' | 'close')
      lastClass: 'iop', lastSex: 0, lastMap: 'astrub', easter: {},
    };
  },
  // 0.94 (quality audit): a field of a damaged or hand-edited save that has not its default's type (null, a list for a
  // table, text for a number…) is dropped, so the default stays: such a save stopped the boot at every launch (settings:
  // null) — an imported file only had kamas / unlocked checked. Everything else of the save is kept as it is
  sane(d, def) {
    if (!d || typeof d !== 'object' || Array.isArray(d)) return {};
    const o = Object.assign({}, d);
    for (const k in def) {
      const a = def[k], b = o[k]; if (a === null || b === undefined) continue;
      if (b === null || typeof b !== typeof a || Array.isArray(b) !== Array.isArray(a) || (typeof a === 'number' && !isFinite(b))) delete o[k];
    }
    return o;
  },
  keyOf(n) { return n === 1 ? this.base : this.base + '-p' + n; },
  meta() { let m = null; try { m = JSON.parse(localStorage.getItem(this.metaKey) || 'null'); } catch (e) { m = null; } return m && m.cur ? m : { cur: 1 }; },
  saveMeta(m) { try { localStorage.setItem(this.metaKey, JSON.stringify(m)); } catch (e) { } },
  read(n) { try { return JSON.parse(localStorage.getItem(this.keyOf(n)) || 'null'); } catch (e) { return null; } },
  load() {
    const m = this.meta(); this.prof = clamp(m.cur | 0, 1, this.NPROF); this.key = this.keyOf(this.prof);
    const d = this.migrate(this.read(this.prof));
    const def = this.defaults();
    this.data = Object.assign(def, this.sane(d, this.defaults()));
    this.data.settings = Object.assign(this.defaults().settings, this.sane(this.data.settings, this.defaults().settings));   // (0.94: the defaults of settings a save lacks — the old code merged the save's settings into themselves)
    if (this.data.settings.perf) { this.data.settings.quality = 'sd'; this.data.settings.qualityUser = 1; delete this.data.settings.perf; }   // (0.44: the old performance mode = SD)
    this.data.mastery = this.data.mastery || {};
    this.data.scrolls = this.data.scrolls || {};
    this.data.spellLv = this.data.spellLv || {};
    return this.data;
  },
  save() { try { localStorage.setItem(this.key, JSON.stringify(this.data)); } catch (e) { } },
  // 0.59: the current profile as a file (Options): the save with its version, the game's build and the profile's name
  exportText() {
    this.data.v = this.SAVE_V;
    return JSON.stringify({ game: 'retro-survivors', v: this.SAVE_V, build: typeof BUILD !== 'undefined' ? BUILD : '', profile: this.pname(this.prof), date: new Date().toISOString(), data: this.data });
  },
  // a file's text -> { data } (a save, brought up to SAVE_V) or { err: 'save_bad' | 'save_newer' } (a key of the UI strings)
  parseImport(text) {
    let o = null; try { o = JSON.parse(text); } catch (e) { return { err: 'save_bad' }; }
    const d = o && o.game === 'retro-survivors' ? o.data : o;   // (a bare save works too: the value kept in localStorage)
    if (!d || typeof d !== 'object' || Array.isArray(d) || typeof d.kamas !== 'number' || !Array.isArray(d.unlocked)) return { err: 'save_bad' };
    if ((d.v | 0) > this.SAVE_V || (o.v | 0) > this.SAVE_V) return { err: 'save_newer' };
    return { data: this.migrate(d) };
  },
  // 0.60: the profile as a code made of digits and lowercase letters only (to copy anywhere, a chat, a note): the save
  // without this device's settings (an import keeps them anyway), deflated, 5 bytes -> 8 base-36 characters.
  // 'rs1' + the bytes' count (6 characters) + an FNV-1a checksum (7) + the data. As short as the compression allows:
  // a few thousand characters for a played profile (to copy and paste, not to type)
  // 0.68 (much shorter codes): 'rs2' = the profile made compact before deflate — the skins as sorted gaps per kind
  // ('16_242' → 16: [..]), the monsters seen only when not already in the kills, the TTG cards / souls as sorted gaps +
  // counts — then 8 bytes = 11 characters of [0-9A-Za-z] (rs1: 5 bytes = 8 base-36 characters). A full profile:
  // 12 700 → see CLAUDE.md 0.68 notes. Codes are case-sensitive now; rs1 codes are still read.
  packSave(d) {
    const o = Object.assign({}, d), gaps = a => a.map((v, i) => i ? v - a[i - 1] : v), byNum = m => Object.keys(m || {}).every(k => /^\d+$/.test(k));
    if (Array.isArray(o.owned)) { const g = {}, other = []; for (const id of o.owned) { const m = /^(\d+)_(\d+)$/.exec(id); if (m) (g[m[1]] = g[m[1]] || []).push(+m[2]); else other.push(id); } for (const k in g) g[k] = gaps(g[k].sort((a, b) => a - b)); o.owned = { g, o: other }; }
    if (o.seen && o.kills) o.seen = Object.keys(o.seen).filter(k => !(o.kills[k] > 0));
    for (const k of ['ttg', 'souls']) if (o[k] && byNum(o[k])) { const ids = Object.keys(o[k]).map(Number).sort((a, b) => a - b); o[k] = { i: gaps(ids), n: ids.map(i => o[k][i]) }; }
    o._pk = 1; return o;
  },
  unpackSave(o) {
    if (!o || !o._pk) return o; delete o._pk; const ungap = a => { let s = 0; return a.map(v => (s += v)); };
    if (o.owned && o.owned.g) { const out = [...(o.owned.o || [])]; for (const k in o.owned.g) for (const n of ungap(o.owned.g[k])) out.push(k + '_' + n); o.owned = out; }
    if (Array.isArray(o.seen)) { const s = {}; for (const k of o.seen) s[k] = 1; for (const k in o.kills || {}) if (o.kills[k] > 0) s[k] = 1; o.seen = s; }
    for (const k of ['ttg', 'souls']) if (o[k] && Array.isArray(o[k].i)) { const m = {}; ungap(o[k].i).forEach((id, j) => { m[id] = o[k].n[j]; }); o[k] = m; }
    return o;
  },
  B62: '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',
  async exportCode() {
    const d = Object.assign({}, this.data, { v: this.SAVE_V }); delete d.settings;
    const z = new Uint8Array(await new Response(new Blob([JSON.stringify(this.packSave(d))]).stream().pipeThrough(new CompressionStream('deflate-raw'))).arrayBuffer());
    const A = this.B62, enc = (n, w) => { let s = ''; for (let k = 0; k < w; k++) { s = A[Number(n % 62n)] + s; n /= 62n; } return s; };
    let out = 'rs2' + enc(BigInt(z.length), 4) + enc(BigInt(fnv1a(z)), 6);
    for (let i = 0; i < z.length; i += 8) { let n = 0n; for (let k = 0; k < 8; k++) n = n * 256n + BigInt(z[i + k] || 0); out += enc(n, 11); }
    return out;
  },
  async parseCode2(c) {
    c = c.replace(/[^0-9A-Za-z]/g, ''); const A = this.B62, dec = s => { let n = 0n; for (const ch of s) { const v = A.indexOf(ch); if (v < 0) return -1n; n = n * 62n + BigInt(v); } return n; };
    if (c.length < 24 || (c.length - 13) % 11) return { err: 'save_code_bad' };
    const len = Number(dec(c.slice(3, 7))), sum = Number(dec(c.slice(7, 13))), z = new Uint8Array(Math.ceil(len / 8) * 8);
    if (!(len > 0) || (c.length - 13) / 11 * 8 < len) return { err: 'save_code_bad' };
    for (let g = 0, i = 13; i < c.length; i += 11, g += 8) { let n = dec(c.slice(i, i + 11)); if (n < 0n) return { err: 'save_code_bad' }; for (let k = 7; k >= 0; k--) { z[g + k] = Number(n % 256n); n /= 256n; } }
    const zz = z.subarray(0, len); if (fnv1a(zz) !== sum) return { err: 'save_code_bad' };
    let txt; try { txt = await new Response(new Blob([zz]).stream().pipeThrough(new DecompressionStream('deflate-raw'))).text(); } catch (e) { return { err: 'save_code_bad' }; }
    let o; try { o = this.unpackSave(JSON.parse(txt)); } catch (e) { return { err: 'save_code_bad' }; }
    return this.parseImport(JSON.stringify(o));
  },
  // a code -> { data } or { err } like parseImport (spaces and line breaks are forgiven; rs1 codes: capitals too)
  async parseCode(code) {
    const raw = String(code || '').trim();
    if (/^rs2/.test(raw.replace(/[^0-9A-Za-z]/g, ''))) return this.parseCode2(raw);
    const c = raw.toLowerCase().replace(/[^0-9a-z]/g, '');
    if (!c.startsWith('rs1') || c.length < 24 || (c.length - 16) % 8) return { err: 'save_code_bad' };
    const len = parseInt(c.slice(3, 9), 36), sum = parseInt(c.slice(9, 16), 36), z = new Uint8Array(Math.ceil(len / 5) * 5);
    if (!(len > 0) || (c.length - 16) / 8 * 5 < len) return { err: 'save_code_bad' };
    for (let g = 0, i = 16; i < c.length; i += 8, g += 5) { let n = parseInt(c.slice(i, i + 8), 36); for (let k = 4; k >= 0; k--) { z[g + k] = n % 256; n = Math.floor(n / 256); } }
    const zz = z.subarray(0, len); if (fnv1a(zz) !== sum) return { err: 'save_code_bad' };
    let txt; try { txt = await new Response(new Blob([zz]).stream().pipeThrough(new DecompressionStream('deflate-raw'))).text(); } catch (e) { return { err: 'save_code_bad' }; }
    return this.parseImport(txt);
  },
  // replaces the current profile by an imported save; this device's settings stay (language, volumes, quality…)
  importData(d) {
    const settings = Object.assign({}, this.data.settings);
    this.data = Object.assign(this.defaults(), this.sane(d, this.defaults())); this.data.settings = settings; this.save();   // (0.94: a damaged field of the file keeps its default)
  },
  // 0.34: a profile can be named (8 characters at most; kept with the device's profile list)
  pname(n) { const m = this.meta(); return (m.names && m.names[n]) || T('profile_n', { n }); },
  setName(n, name) { const m = this.meta(); m.cur = m.cur || this.prof; m.names = m.names || {}; name = String(name || '').trim().slice(0, 8); if (name) m.names[n] = name; else delete m.names[n]; this.saveMeta(m); },
  // a short summary of a profile (for the profile picker)
  info(n) { const d = n === this.prof ? this.data : this.read(n); if (!d) return null; return { runs: d.runs || 0, kamas: d.kamas || 0, ach: Object.keys(d.ach || {}).length, kills: d.totalKills || 0, zones: Object.keys(d.cleared || {}).length, t: d.lastPlayed || 0 }; },
  switchTo(n) {
    n = clamp(n | 0, 1, this.NPROF); if (n === this.prof) return;
    const settings = Object.assign({}, this.data.settings);
    this.data.lastPlayed = Date.now(); this.save();
    const m = this.meta(); m.cur = n; this.saveMeta(m);
    this.load(); this.data.settings = Object.assign(this.data.settings, settings); this.save();
  },
  // 0.97: the test code GODMODE (Options > save code): everything of the game on the current profile — every zone open and
  // won (the secret ones and Difficile too), every shop line at its top (class / global spells, characteristics, weapon
  // masteries, scrolls), every look owned, every Dofus, relic, achievement, Archimonster soul, TTG card, unique weapon and
  // fusion found, the bestiary seen, kamas to spare; nothing of the profile is taken away
  godMode(C) {
    const S = this.data, all = (list, v = 1) => Object.fromEntries((list || []).map(x => [String(x.id || x), v])), up = (o, add) => Object.assign(o || {}, add);
    const top = (cost, fb) => (cost || fb).length, now = Date.now();
    S.unlocked = [...new Set([...(S.unlocked || []), ...C.maps.map(m => m.id)])];
    S.cleared = up(S.cleared, all(C.maps)); S.clearedNormal = up(S.clearedNormal, all(C.maps)); S.clearedHard = up(S.clearedHard, all(C.maps)); S.tuto = up(S.tuto, all(C.maps));
    S.hardUnlocked = 1; S.tot = Math.max(1, S.tot || 0); S.kamas = Math.max(S.kamas || 0, 9999999);
    const spells = [...C.classes.flatMap(c => c.spells), ...(C.globalSpells || []).map(g => g.id).filter(id => C.spells[id] && C.spells[id].t !== 'wheel')];
    S.spellLv = up(S.spellLv, all(spells, top(C.spellCost, [0, 0, 0, 0, 0])));
    S.passLv = up(S.passLv, all((C.passives || []).filter(p => p.max > 1 && p.stat !== 'amount'), top(C.passCost || C.spellCost, [0, 0, 0, 0, 0])));   // (the shop's: UI.shop 'traits')
    S.mastery = up(S.mastery, all(C.weapons, top(C.masteryCost, [0, 0, 0, 0, 0])));
    S.scrolls = up(S.scrolls, all(C.scrolls, top(C.scrollCost, [0])));
    S.owned = [...new Set([...(S.owned || []), ...[C.hats, C.capes, C.pets, C.shields].flatMap(l => (l || []).map(it => it.id))])];
    S.dofus = up(S.dofus, all(C.dofus)); S.relics = up(S.relics, all(C.relics)); S.ach = up(S.ach, all(C.achievements, now));
    S.souls = up(S.souls, all(Object.values(C.archi || {}).flat())); S.ttg = up(S.ttg, all((C.ttg || {}).cards));
    S.uniques = up(S.uniques, all(C.uniqueWeapons)); S.fusions = up(S.fusions, all(C.fusions));
    S.seen = up(S.seen, all([...Object.keys(C.monsters), ...Object.keys(C.bosses)]));
    this.save();
  },
  // back to zero: every progress of the current profile is erased (the settings stay)
  reset() {
    const settings = Object.assign({}, this.data.settings);
    this.data = this.defaults(); this.data.settings = Object.assign(this.data.settings, settings); this.save();
  },
};

// ---------------------------------------------------------------- i18n
const I18N = {
  fr: {
    play: 'Jouer', bestiary: 'Bestiaire', shop: 'Boutique', options: 'Options', credits: 'Crédits', back: 'Retour',
    choose_class: 'Choisissez votre classe', choose_map: 'Choisissez une zone', start: "C'est parti !",
    male: 'Homme', female: 'Femme', reroll: 'Nouvelles couleurs', locked: 'Verrouillé', locked_hint: 'Atteignez le boss final de la zone précédente (20:00)',
    best: 'Record', level: 'Niv.', kills: 'Victimes', kamas: 'Kamas', time: 'Temps',
    levelup: 'Niveau supérieur !', choose_upgrade: 'Choisissez une amélioration', new_: 'NOUVEAU',
    nothing_left: 'Tout est au maximum !', take_kamas: 'Bourse de kamas', take_bread: 'Incroyable potion de soin de masse',
    take_kamas_d: '+{n} kamas pour la boutique.', take_bread_d: 'Rend 25 % de vos PV et soigne vos invocations.',
    always_pick: 'Toujours choisir automatiquement quand tout est au max',
    paused: 'Pause', resume: 'Reprendre', quit: 'Abandonner la partie', auto_pick: 'Choix automatique (tout au max)',
    auto_off: 'Désactivé', music: 'Musique', sfx: 'Effets sonores', lang: 'Langue', dmg_numbers: 'Afficher les dégâts',
    shake: 'Tremblement de l\'écran', chat: 'Afficher le chat', fullscreen: 'Plein écran',
    dead_title: 'Vous êtes mort...', dead_sub: 'Votre fantôme erre jusqu\'à la statue du Phénix la plus proche.',
    victory: 'Victoire !', victory_sub: 'La zone est nettoyée. Les Douze sont fiers de vous.',
    new_zone: 'Nouvelle zone débloquée : {z}', earned: 'Kamas gagnés', continue: 'Continuer',
    boss_appears: '{n} apparaît !', door_appears: 'Une porte mystérieuse est apparue au centre de la carte...',
    door_enter: 'Entrer dans la porte de ToT', dofus_found: 'Vous avez obtenu : {n} !', chest: 'Coffre',
    chest_open: 'Ouvrir', unknown: '???', bestiary_hint: 'Rencontrez un monstre pour le découvrir.',
    lvl_dofus: 'Niveau (Rétro)', hp_dofus: 'PV (Rétro)', attacks: 'Sorts', zone: 'Zone', killed: 'Vaincus',
    drops: 'Peut dropper', bosses: 'Boss', owned: 'Possédé', buy: 'Acheter', equip: 'Équiper', equipped: 'Équipé',
    hats: 'Coiffes', capes: 'Capes', none: 'Aucune', not_enough: 'Pas assez de kamas !', preview: 'Aperçu',
    spells: 'Sorts', passives: 'Caractéristiques', class_passive: 'Bonus de classe', dofus_coll: 'Collection de Dofus',
    tot_title: 'Combat contre ToT, le Maître du Jeu', tot_intro: 'Bienvenue dans mon donjon ! Choisissez le BON sort à chaque tour. Trois erreurs et je vous renvoie dehors.',
    tot_win: 'Bien joué ! Prenez ce Dofus Ocre, vous l\'avez mérité.', tot_lose: 'Trop facile. Retournez jouer dehors !',
    tot_right: 'Bien vu !', tot_wrong: 'Raté !', your_turn: 'À vous de jouer !', hint: 'Indice',
    loading: 'Chargement', tip: 'Astuce', fanmade: 'Fan-game non officiel — Dofus Rétro © Ankama Games. Non affilié à Ankama.',
    controls: 'Déplacement : ZQSD / WASD / flèches / manette — Échap : pause', minimap: 'Carte',
    gm_banned: '[Wabbit GM] Vous êtes banni... Non je rigole. Prenez ces kamas.', jackpot: 'JACKPOT ! +{n} kamas',
    run_kamas: 'Kamas', run_level: 'Niveau', enter: 'Entrer', door: 'Porte de ToT', elite: 'Élite',
    secret_boss: 'Un grondement sourd... {n} se réveille !', stage: 'Zone', difficulty: 'Niveaux',
    sex: 'Sexe', colors: 'Couleurs', class_spells: 'Sorts de classe', tofumode: 'Mode Tofu activé ! Tout le monde devient un Tofu.',
    stats_hp: 'PV', stats_speed: 'Vitesse', stats_might: 'Puissance', stats_armor: 'Résistance',
    no_save: '(sauvegarde indisponible dans ce navigateur)', mute: 'Muet', confirm_quit: 'Abandonner ? Les kamas ramassés sont conservés.',
  },
  en: {
    play: 'Play', bestiary: 'Bestiary', shop: 'Shop', options: 'Options', credits: 'Credits', back: 'Back',
    choose_class: 'Choose your class', choose_map: 'Choose a zone', start: "Let's go!",
    male: 'Male', female: 'Female', reroll: 'New colours', locked: 'Locked', locked_hint: 'Reach the final boss of the previous zone (20:00)',
    best: 'Best', level: 'Lvl', kills: 'Kills', kamas: 'Kamas', time: 'Time',
    levelup: 'Level up!', choose_upgrade: 'Choose an upgrade', new_: 'NEW',
    nothing_left: 'Everything is maxed!', take_kamas: 'Bag of kamas', take_bread: 'Incredible Mass Healing Potion',
    take_kamas_d: '+{n} kamas for the shop.', take_bread_d: 'Restores 25% of your HP and heals your summons.',
    always_pick: 'Always pick this automatically when everything is maxed',
    paused: 'Paused', resume: 'Resume', quit: 'Give up the run', auto_pick: 'Auto-pick (all maxed)',
    auto_off: 'Off', music: 'Music', sfx: 'Sound effects', lang: 'Language', dmg_numbers: 'Show damage numbers',
    shake: 'Screen shake', chat: 'Show chat', fullscreen: 'Fullscreen',
    dead_title: 'You died...', dead_sub: 'Your ghost wanders to the nearest Phoenix statue.',
    victory: 'Victory!', victory_sub: 'The zone is cleared. The Twelve are proud of you.',
    new_zone: 'New zone unlocked: {z}', earned: 'Kamas earned', continue: 'Continue',
    boss_appears: '{n} appears!', door_appears: 'A mysterious door appeared in the middle of the map...',
    door_enter: "Enter ToT's door", dofus_found: 'You obtained: {n}!', chest: 'Chest',
    chest_open: 'Open', unknown: '???', bestiary_hint: 'Meet a monster to discover it.',
    lvl_dofus: 'Level (Retro)', hp_dofus: 'HP (Retro)', attacks: 'Spells', zone: 'Zone', killed: 'Defeated',
    drops: 'May drop', bosses: 'Bosses', owned: 'Owned', buy: 'Buy', equip: 'Equip', equipped: 'Equipped',
    hats: 'Hats', capes: 'Capes', none: 'None', not_enough: 'Not enough kamas!', preview: 'Preview',
    spells: 'Spells', passives: 'Characteristics', class_passive: 'Class bonus', dofus_coll: 'Dofus collection',
    tot_title: 'Fight against ToT, the Gamemaster', tot_intro: 'Welcome to my dungeon! Pick the RIGHT spell each turn. Three mistakes and I kick you out.',
    tot_win: 'Well played! Take this Ochre Dofus, you earned it.', tot_lose: 'Too easy. Go back outside and play!',
    tot_right: 'Spot on!', tot_wrong: 'Missed!', your_turn: 'Your turn!', hint: 'Hint',
    loading: 'Loading', tip: 'Tip', fanmade: 'Unofficial fan game — Dofus Retro © Ankama Games. Not affiliated with Ankama.',
    controls: 'Move: WASD / ZQSD / arrows / gamepad — Esc: pause', minimap: 'Map',
    gm_banned: '[Wabbit GM] You are banned... Just kidding. Take these kamas.', jackpot: 'JACKPOT! +{n} kamas',
    run_kamas: 'Kamas', run_level: 'Level', enter: 'Enter', door: "ToT's door", elite: 'Elite',
    secret_boss: 'A deep rumble... {n} awakens!', stage: 'Zone', difficulty: 'Levels',
    sex: 'Sex', colors: 'Colours', class_spells: 'Class spells', tofumode: 'Tofu mode on! Everyone turns into a Tofu.',
    stats_hp: 'HP', stats_speed: 'Speed', stats_might: 'Power', stats_armor: 'Armour',
    no_save: '(saving unavailable in this browser)', mute: 'Mute', confirm_quit: 'Give up? Kamas you picked up are kept.',
  },
};
let LANG = 'fr';
const LANGS = ['fr', 'en', 'de', 'es', 'it', 'nl', 'pt'];
// 0.94: a characteristic's value per level in a run, with the shop's levels (Store.data.passLv): `perShop`
// [shop 0, shop max] when it has one (Vitalité 10 -> 20 %, Points d'action 3 -> 5 %, in even steps), else `per` + 10 %
// of it a shop level (C.spellPer). Shared by Run.recompute and the shop / level-up texts (ui.js)
function passivePer(C, p, shopLv) {
  shopLv = shopLv || 0;
  if (p.perShop) { const M = (C.passCost || []).length || 5; return p.perShop[0] + (p.perShop[1] - p.perShop[0]) * Math.min(shopLv, M) / M; }
  return p.per * (p.max > 1 && p.stat !== 'amount' ? 1 + (C.spellPer || 0.1) * shopLv : 1);
}
function T(k, vars) {
  let s = (I18N[LANG] && I18N[LANG][k]) || (I18N.en && I18N.en[k]) || I18N.fr[k] || k;
  if (vars) for (const v in vars) s = s.replace('{' + v + '}', vars[v]);
  return s;
}
function L(obj) { if (!obj) return ''; if (typeof obj === 'string') return obj; return obj[LANG] || obj.en || obj.fr || ''; }
function detectLang() { const n = (navigator.language || 'en').toLowerCase().slice(0, 2); return LANGS.includes(n) ? n : 'en'; }

// the loading screen's tips before content.json is there (C.tips replaces them at boot; 0.97: current ones, every language)
const TIPS = {
  fr: [
    "Plus l'ambre est grosse, plus elle rapporte d'expérience. Ramassez tout : un Enutrof ne laisserait rien traîner.",
    "Un Dofus trouvé reste actif dans toutes vos parties suivantes. Pas besoin de farmer le Dragon Cochon trois cents fois.",
    "Les bombes du Roublard explosent en chaîne : posez-les près les unes des autres. De préférence pas sous vos pieds.",
    "Une Fée d'Artifice nettoie tout l'écran. Gardez-la pour les moments chauds, pas pour le premier Piou venu.",
    "Une Potion de Rappel attire toute l'expérience vers vous. Plus rapide qu'une Potion de Rappel… vers Astrub.",
    "Dans l'eau, on avance 30 % moins vite. Même un Crâ ne marche pas sur l'eau.",
    "Le Bouftou Royal adore se soigner. Frappez fort et vite : c'est un Bouftou, pas un Eniripsa.",
    "Les Sacrieurs adorent prendre des coups. Vous, un peu moins : ramassez le pain, il rend de la vie.",
  ],
  en: [
    "The bigger the amber, the more experience it gives. Pick everything up: an Enutrof would never leave anything behind.",
    "A Dofus you find stays active in all your next runs. No need to farm the Dragon Pig three hundred times.",
    "The Rogue's bombs explode in a chain: lay them close together. Preferably not under your own feet.",
    "A Firework Fairy clears the whole screen. Keep it for the tough moments, not for the first Piwi you meet.",
    "A Recall Potion pulls all the experience to you. Faster than a Recall Potion… back to Astrub.",
    "In water you move 30% slower. Not even a Cra walks on water.",
    "The Royal Gobball loves healing itself. Hit hard and fast: it is a Gobball, not an Eniripsa.",
    "Sacriers love taking hits. You, a bit less: pick up the bread, it gives life back.",
  ],
  de: [
    "Je größer der Bernstein, desto mehr Erfahrung. Sammle alles ein: Ein Enutrof würde nichts liegen lassen.",
    "Ein gefundenes Dofus bleibt in allen folgenden Runden aktiv. Kein Grund, den Schweinedrachen dreihundertmal zu farmen.",
    "Die Bomben des Halsabschneiders explodieren in Kette: Leg sie dicht beieinander. Am besten nicht unter deine Füße.",
    "Eine Feuerwerksfee räumt den ganzen Bildschirm. Heb sie für heiße Momente auf, nicht für den ersten Piepmatz.",
    "Ein Rückruftrank zieht alle Erfahrung zu dir. Schneller als ein Rückruftrank… nach Astrub.",
    "Im Wasser bist du 30 % langsamer. Nicht einmal ein Cra läuft übers Wasser.",
    "Der Königliche Fresssack heilt sich gern. Schlag hart und schnell zu: Er ist ein Fresssack, kein Eniripsa.",
    "Sacrieurs lieben es, Schläge einzustecken. Du etwas weniger: Sammle das Brot ein, es gibt Leben zurück.",
  ],
  es: [
    "Cuanto más grande el ámbar, más experiencia da. Recógelo todo: un Anutrof no dejaría nada por ahí.",
    "Un Dofus encontrado sigue activo en todas tus partidas siguientes. No hace falta farmear al Dragocerdo trescientas veces.",
    "Las bombas del Tymador explotan en cadena: ponlas cerca unas de otras. Preferiblemente no bajo tus pies.",
    "Un Hada de Artificio limpia toda la pantalla. Guárdala para los momentos calientes, no para el primer Pío que pase.",
    "Una Poción de Regreso atrae toda la experiencia hacia ti. Más rápida que una Poción de Regreso… a Astrub.",
    "En el agua avanzas un 30 % más lento. Ni un Ocra camina sobre el agua.",
    "El Jalató Real adora curarse. Golpea fuerte y rápido: es un Jalató, no un Aniripsa.",
    "A los Sacrógritos les encanta recibir golpes. A ti, algo menos: recoge el pan, devuelve vida.",
  ],
  it: [
    "Più l'ambra è grande, più esperienza dà. Raccogli tutto: un Anutrof non lascerebbe niente in giro.",
    "Un Dofus trovato resta attivo in tutte le partite successive. Niente bisogno di farmare il Drago Maiale trecento volte.",
    "Le bombe del Ladrurbo esplodono a catena: mettile vicine tra loro. Possibilmente non sotto i tuoi piedi.",
    "Una Fata d'Artificio ripulisce tutto lo schermo. Tienila per i momenti caldi, non per il primo Pìu che passa.",
    "Una Pozione di Richiamo attira tutta l'esperienza verso di te. Più veloce di una Pozione di Richiamo… verso Astrub.",
    "In acqua si avanza il 30% più lentamente. Nemmeno un Ocra cammina sull'acqua.",
    "Il Pappatutto Reale adora curarsi. Colpisci forte e veloce: è un Pappatutto, non un Aniripsa.",
    "Ai Sàcridi piace prendere botte. A te un po' meno: raccogli il pane, ridà vita.",
  ],
  nl: [
    "Hoe groter de amber, hoe meer ervaring. Raap alles op: een Enutrof laat nooit iets liggen.",
    "Een gevonden Dofus blijft actief in al je volgende runs. Je hoeft de Dragon Pig geen driehonderd keer te farmen.",
    "De bommen van de Schurk ontploffen in een ketting: leg ze dicht bij elkaar. Liefst niet onder je eigen voeten.",
    "Een Vuurwerkfee veegt het hele scherm schoon. Bewaar haar voor hete momenten, niet voor de eerste de beste Piwi.",
    "Een Terugroepdrank trekt alle ervaring naar je toe. Sneller dan een Terugroepdrank… naar Astrub.",
    "In het water ga je 30% trager. Zelfs een Cra loopt niet over water.",
    "De Koninklijke Veelvraat geneest zichzelf graag. Sla hard en snel: het is een Veelvraat, geen Eniripsa.",
    "Sacriers houden ervan klappen te krijgen. Jij iets minder: raap het brood op, het geeft leven terug.",
  ],
  pt: [
    "Quanto maior o âmbar, mais experiência dá. Apanha tudo: um Enutrof nunca deixaria nada para trás.",
    "Um Dofus encontrado fica ativo em todas as partidas seguintes. Não é preciso farmar o Dragão Porco trezentas vezes.",
    "As bombas do Ladino explodem em cadeia: põe-nas perto umas das outras. De preferência não debaixo dos teus pés.",
    "Uma Fada de Artifício limpa o ecrã todo. Guarda-a para os momentos quentes, não para o primeiro Piwi que aparecer.",
    "Uma Poção de Chamada atrai toda a experiência para ti. Mais rápida que uma Poção de Chamada… para Astrub.",
    "Na água avanças 30% mais devagar. Nem um Cra caminha sobre a água.",
    "O Gobball Real adora curar-se. Bate com força e depressa: é um Gobball, não um Eniripsa.",
    "Os Sacriers adoram levar pancada. Tu, um pouco menos: apanha o pão, devolve vida.",
  ],
};
// fullscreen on / off (menu button, gamepad SELECT). Browsers may refuse it outside a click or key press (a gamepad
// button is not always a "user gesture"): then the next key / click / tap finishes the job
function toggleFullscreen() {
  const d = document, el = d.documentElement;
  const fs = d.fullscreenElement || d.webkitFullscreenElement;
  try {
    if (fs) { (d.exitFullscreen || d.webkitExitFullscreen).call(d); return; }
    const req = el.requestFullscreen || el.webkitRequestFullscreen; if (!req) return;
    const later = () => {
      if (typeof toast === 'function') toast(T('fs_press'));
      const go = () => { window.removeEventListener('keydown', go, true); window.removeEventListener('pointerdown', go, true); try { const q = req.call(el); if (q && q.catch) q.catch(() => { }); } catch (e) { } };
      window.addEventListener('keydown', go, true); window.addEventListener('pointerdown', go, true);
    };
    const p = req.call(el);
    if (p && p.catch) p.catch(later);
  } catch (e) { }
}
// light / dark theme of the menus (Store.data.settings.theme)
function applyTheme() { try { document.body.classList.toggle('dark', !!(Store.data && Store.data.settings && Store.data.settings.theme === 'dark')); } catch (e) { } }
// switch it (the main menu's button, F1, a pad's R3); the main menu's switch follows
function toggleTheme() {
  const S = Store.data && Store.data.settings; if (!S) return;
  S.theme = S.theme === 'dark' ? 'light' : 'dark'; Store.save(); applyTheme();
  document.querySelectorAll('.theme-btn .switch').forEach(e => e.classList.toggle('on', S.theme === 'dark')); Audio2.blip('click');
}

