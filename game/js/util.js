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

const TIPS = {
  fr: [
    "N'oubliez pas de vous inscrire à un ou plusieurs métiers. (Non, ça ne sert à rien ici.)",
    'Les Tofus sont rapides mais complètement idiots. Profitez-en.',
    'Le Bouftou Royal adore se soigner. Frappez fort et vite.',
    'Une Fée d\'Artifice nettoie tout l\'écran. Gardez-la pour les moments chauds !',
    'Une Potion de Rappel attire toute l\'expérience vers vous.',
    'À 5:00, une porte apparaît au centre de la carte. ToT vous y attend.',
    'Chaque boss peut dropper le Dofus qu\'il droppait dans le jeu original.',
    'Le Bandit Manchot s\'enfuit avec ses kamas. Rattrapez-le !',
    'Les kamas servent à acheter des coiffes et des capes dans la Boutique.',
    'Un Crâ qui reste à distance est un Crâ heureux.',
    'Il paraît qu\'un Wabbit GM rôde sur l\'île...',
    'Les Pious ne sont pas dangereux. Enfin, pas tout seuls.',
  ],
  en: [
    "Don't forget to sign up for one or more jobs. (No, it's useless here.)",
    'Tofus are fast but completely dumb. Use it.',
    'The Royal Gobball loves to heal himself. Hit hard and fast.',
    'A Firework Fairy clears the whole screen. Keep it for hot moments!',
    'A Recall Potion pulls every experience crystal to you.',
    "At 5:00, a door appears in the middle of the map. ToT is waiting.",
    'Every boss can drop the Dofus it dropped in the original game.',
    'The One-Armed Bandit runs off with his kamas. Catch him!',
    'Kamas buy hats and capes in the Shop.',
    'A Cra who keeps their distance is a happy Cra.',
    'Rumour says a GM Wabbit roams the island...',
    'Piwis are harmless. Well, not in groups.',
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

