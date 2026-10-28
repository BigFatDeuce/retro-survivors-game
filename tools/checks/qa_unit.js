// 0.93: the fast checks of the game's data and logic, no browser (node, ~1 min). The game's own
// scripts run in a vm (tools/checks/sim_node.js's bootstrap: the real util / spells / game / progress code with stubs).
//   integrity  every reference of content.json / sprites.json / sounds.json points to something that exists — spells,
//              fusions, monsters, bosses, sheets, effect sheets, icons, accessory pictures, sounds, musics — and every
//              file named exists with that exact case (the web server is case-sensitive, Windows is not)
//   i18n       every interface string in the 7 languages; every T('key') of the scripts known
//   store      the save: defaults, old / partial / broken saves loaded without breaking the profile, imports refused or
//              taken as they should, the save code's packing round trip
//   logic      the stats rebuilt the same each time (no bonus counted twice), the shield's +1 only where allowed, drops
//              never on each other nor off the ground, the stats' top spell, achievements' values
//   runtime    every spell, fusion and weapon cast in a real run (level 1 and its top level), every zone played a few
//              seconds, every class started: no error thrown
// Prints one JSON line per check ({ suite, name, ok, detail }) and a summary; exit code 1 if any failed.
// usage: node tools/checks/qa_unit.js [suite…]    (tools/qa.py runs it as its 'unit' step)
const fs = require('fs'), path = require('path');
const S = require('./sim_node.js'); const { ctx, C, SPR, vm } = S;
const G = path.join(__dirname, '..', '..', 'game');
const only = process.argv.slice(2);
const results = [];
const check = (suite, name, ok, detail) => { results.push({ suite, name, ok: !!ok, detail: ok ? undefined : detail }); };
const run = (code) => vm.runInContext(code, ctx);

// ---------------------------------------------------------------- helpers
const exists = (() => {   // exact-case existence (the web is case-sensitive)
  const dirs = new Map();
  const list = d => { if (!dirs.has(d)) { try { dirs.set(d, new Set(fs.readdirSync(d))); } catch (e) { dirs.set(d, null); } } return dirs.get(d); };
  return rel => { const parts = rel.split('/'); let d = G; for (const p of parts) { const L = list(d); if (!L || !L.has(p)) return false; d = path.join(d, p); } return true; };
})();
const ICONS = new Set([...Object.keys(SPR.icons || {}), ...Object.keys(SPR.icons2 || {}), ...Object.keys(SPR.icons3 || {})]);
const SND = JSON.parse(fs.readFileSync(path.join(G, 'data', 'sounds.json'), 'utf8'));
const sndOk = n => !!(SND.pack && SND.pack[n]) || exists(`assets/audio/sfx/${n}.mp3`) || exists(`assets/audio/fx/${n}.mp3`);
const missing = (list, test) => list.filter(x => !test(x));
const say = (arr, n = 12) => arr.slice(0, n).join(', ') + (arr.length > n ? ` … (${arr.length})` : '');

// ---------------------------------------------------------------- integrity
function integrity() {
  const sp = C.spells, cls = C.classes;
  check('integrity', 'class spells exist', !cls.flatMap(c => c.spells.filter(s => !sp[s]).map(s => c.id + ':' + s)).length, say(cls.flatMap(c => c.spells.filter(s => !sp[s]).map(s => c.id + ':' + s))));
  check('integrity', 'class sprites in the sheets', !cls.flatMap(c => c.sprites.filter(s => !SPR.chars[String(s)]).map(s => c.id + ':' + s)).length, say(cls.flatMap(c => c.sprites.filter(s => !SPR.chars[String(s)]).map(s => c.id + ':' + s))));
  const fus = C.spellFusions || [];
  const badF = fus.filter(f => !sp[f.id] || !(f.src || []).every(s => sp[s] || (C.weapons || []).some(w => w.id === s) || (C.globalSpells || []).some(g => g.id === s)) || (f.cls && !cls.some(c => c.id === f.cls)));   // (0.95: cls null, two global spells: every class)
  check('integrity', 'spell fusions: their spell, sources and class exist', !badF.length, say(badF.map(f => f.id)));
  // (known, docs/reports/0.94-qa-audit.md QA-17: these clips were never built; the game draws its own orb / blow strip instead)
  const fx = Object.values(sp).flatMap(s => (s.fx || []).map(f => [s.id, String(f)])).filter(([, f]) => !SPR.fx[f]).map(([s, f]) => s + ':' + f);
  const fxNew = fx.filter(k => !['larme:1014', 'poing_enflamme:1208', 'fu_sad_toile:1014', 'fu_pan_hache:1208'].includes(k));
  check('integrity', 'spell effects in the effect sheets' + (fx.length > fxNew.length ? ` (${fx.length - fxNew.length} known, QA-08)` : ''), !fxNew.length, say(fxNew));
  const fxFiles = missing(Object.keys(SPR.fx || {}), k => exists(`assets/fx/${k}.webp`));
  check('integrity', 'effect sheet files', !fxFiles.length, say(fxFiles));
  const spIc = Object.values(sp).filter(s => s.icon !== undefined && !ICONS.has('sp_' + s.icon) && !ICONS.has(String(s.icon)));
  check('integrity', 'spell icons in the atlases', !spIc.length, say(spIc.map(s => s.id + ':' + s.icon)));
  const snd = Object.values(sp).flatMap(s => [s.snd].flat().filter(Boolean).map(n => [s.id, n])).filter(([, n]) => !sndOk(n));
  check('integrity', 'spell sounds', !snd.length, say(snd.map(([s, n]) => s + ':' + n)));
  // zones
  const mobs = C.monsters, boss = C.bosses;
  const zoneBad = [];
  for (const m of C.maps) {
    if (!SPR.worlds[m.world]) zoneBad.push(m.id + ': world ' + m.world);
    else for (const t of SPR.worlds[m.world].tiles || []) if (!exists(`assets/worlds/${t[2]}`)) { zoneBad.push(m.id + ': tile ' + t[2]); break; }
    if (!exists(`assets/worlds/${m.world}_mini.webp`)) zoneBad.push(m.id + ': mini map');
    for (const w of m.waves || []) for (const [id] of w[2] || []) if (!mobs[id]) zoneBad.push(m.id + ': monster ' + id);
    for (const [, b] of m.bosses || []) if (!boss[b]) zoneBad.push(m.id + ': boss ' + b);
    for (const k of ['music', 'boss_music']) if (m[k] && !exists(`assets/audio/music/${m[k]}.mp3`)) zoneBad.push(m.id + ': ' + k + ' ' + m[k]);
  }
  check('integrity', 'zones: worlds, tiles, mini maps, monsters, bosses, musics', !zoneBad.length, say(zoneBad));
  const sheet = k => SPR.mobs[k] && (SPR.mobs[k].src ? exists('assets/' + SPR.mobs[k].src) : exists(`assets/mobs/${k}.webp`));
  const mobBad = [...Object.entries(mobs), ...Object.entries(boss)].filter(([, d]) => d.sprite && !sheet(d.sprite)).map(([k, d]) => k + ':' + d.sprite);
  check('integrity', 'monster / boss sheets and their files', !mobBad.length, say(mobBad));
  // the sheets CharSprite.load really loads (an old sheet that the '_s' one covers is data only: it has no file)
  const CH = SPR.chars, charBad = [], file = (k, mask) => { if (!exists(`assets/chars/${k}.webp`)) charBad.push(k); if (mask && !exists(`assets/chars/${k}_m.webp`)) charBad.push(k + '_m'); };
  const sids = new Set([...cls.flatMap(c => c.sprites.map(String)), ...Object.keys(CH).filter(k => /^\d+_c$/.test(k))]);
  for (const sid of sids) for (const hat of [false, true]) {
    const sk = sid + (hat && CH[sid + '_h_s'] ? '_h_s' : '_s'), S3 = CH[sk];
    const ld = [sid + '_x', sid + '_e', sid + (hat && CH[sid + '_h_r'] ? '_h_r' : '_r'), sid + '_h_x', sid + '_h_e', sk];
    for (const k of [sid, sid + '_h']) if (CH[k] && !(S3 && Object.keys(CH[k].anims).every(a => S3.anims[a] || a.startsWith('run')))) ld.push(k);
    for (const k of ld) if (CH[k]) { file(k, !CH[k].nomask); for (const l of ['fa', 'fh']) if (CH[k][l]) file(CH[k][l].src, true); }
  }
  check('integrity', 'character sheets loaded by the game: files, colour masks, front layers', !charBad.length, say([...new Set(charBad)]));
  // skins
  const skins = [...C.hats, ...C.capes, ...C.pets, ...(C.shields || [])];
  const accBad = skins.filter(i => !SPR.acci[i.id] || !exists(`assets/acc/i/${i.id}.webp`) || (SPR.acci[i.id].m && !exists(`assets/acc/i/${i.id}_m.webp`))).map(i => i.id);
  check('integrity', 'skins: their worn pictures', !accBad.length, say(accBad));
  const icBad = skins.filter(i => !ICONS.has('it_' + i.id)).map(i => i.id);
  check('integrity', 'skins: their shop icons', !icBad.length, say(icBad));
  const priceBad = skins.filter(i => !(i.price > 0) && !i.free).map(i => i.id);
  check('integrity', 'skins: a price', !priceBad.length, say(priceBad));
  const dup = skins.map(i => i.id).filter((id, i, a) => a.indexOf(id) !== i);
  check('integrity', 'skins: no id twice', !dup.length, say(dup));
  const shP = (C.shields || []).filter(s => s.price < 5000 || s.price > 10000).map(s => s.id);
  check('integrity', 'shields: price within 5 000-10 000', !shP.length && (C.shields || []).length > 0, say(shP));
  // the rest of what shows an icon
  const others = [...C.achievements.map(a => ['ach ' + a.id, a.icon]), ...C.passives.map(p => ['passive ' + p.id, p.icon]), ...(C.relics || []).map(r => ['relic ' + r.id, r.icon]),
    ...C.dofus.map(d => ['dofus ' + d.id, 'dofus_hd_' + d.icon])].filter(([, ic]) => ic && !ICONS.has(String(ic)));
  check('integrity', 'achievement / characteristic / relic / Dofus icons', !others.length, say(others.map(([k, i]) => k + ':' + i)));
  const ach = run('Prog'); const achBad = [];
  for (const a of C.achievements) { try { const v = ach.value(a.k); if (typeof v !== 'number' || isNaN(v)) achBad.push(a.id + ' -> ' + v); } catch (e) { achBad.push(a.id + ': ' + e.message); } }
  check('integrity', 'achievements: every condition can be read', !achBad.length, say(achBad));
  const music = ['loc_incarnam', 'loc_amakna', 'loc_brakmar', ...cls.map(c => c.theme || 'cls_' + c.id)].filter(n => !exists(`assets/audio/music/${n}.mp3`));
  check('integrity', 'menu and class musics', !music.length, say(music));
  const styles = ['phonk', 'lofi'].flatMap(st => [1, 2, 3, 4, 5].map(i => `${st}/${st}${i}`)).filter(n => !exists(`assets/audio/music/${n}.mp3`));
  check('integrity', 'music styles (phonk / lofi)', !styles.length, say(styles));
  const eggs = ['bardella', 'lassalle', 'zemmour', 'meluche', 'sardoche', 'lisnard', 'sarkozy', 'hollande', 'lepen', 'marine', 'macron', 'fah', 'laugh_goultard', 'death_cough'].filter(n => !exists(`assets/audio/fx/${n}.mp3`));
  check('integrity', 'easter-egg and victory clips', !eggs.length, say(eggs));
  // (the game's media carry no metadata — no ID3 / APE tags or covers in the sounds, no EXIF / XMP / text chunks in
  // the pictures)
  const meta = [];
  const walk = d => { for (const f of fs.readdirSync(d, { withFileTypes: true })) { const p = path.join(d, f.name); if (f.isDirectory()) walk(p); else if (/\.(mp3|webp|png|jpg|mp4|webm)$/i.test(f.name)) {
    const b = fs.readFileSync(p), rel = path.relative(G, p).replace(/\\/g, '/'), ext = f.name.split('.').pop().toLowerCase();
    if (ext === 'mp3' && (b.slice(0, 3).toString() === 'ID3' || (b.length > 128 && b.slice(b.length - 128, b.length - 125).toString() === 'TAG') || b.includes('APETAGEX'))) meta.push(rel);
    else if (ext === 'webp') { for (let i = 12; i + 8 <= b.length;) { const cc = b.slice(i, i + 4).toString(), n = b.readUInt32LE(i + 4); if (cc === 'EXIF' || cc === 'XMP ') { meta.push(rel); break; } i += 8 + n + (n & 1); } }   // (its RIFF chunks, not bytes that happen to spell EXIF)
    else if (ext === 'png' && ['tEXt', 'iTXt', 'zTXt', 'eXIf'].some(k => b.includes(k))) meta.push(rel);
    else if (ext === 'jpg' && (b.includes('Exif\0') || b.includes('http://ns.adobe.com/xap'))) meta.push(rel); } } };
  walk(path.join(G, 'assets'));
  check('integrity', 'media without metadata (tags, covers, EXIF / XMP / text chunks)', !meta.length, say(meta));
  // every 'assets/…' literal of the scripts and the page, exact case (no template)
  const lit = [];
  for (const f of fs.readdirSync(path.join(G, 'js')).filter(f => f.endsWith('.js'))) {
    const src = fs.readFileSync(path.join(G, 'js', f), 'utf8');
    for (const m of src.matchAll(/['"`](assets\/[^'"`$?{}]+\.(?:webp|png|jpg|mp3|json|woff2?|ttf))['"`]/g)) lit.push([f, m[1]]);
  }
  const html = fs.readFileSync(path.join(G, 'index.html'), 'utf8');
  for (const m of html.matchAll(/(?:src|href)=["']([^"'?#]+\.(?:js|css|webp|png|jpg|woff2?|ttf|ico))/g)) if (!/^https?:/.test(m[1])) lit.push(['index.html', m[1]]);
  for (const m of html.matchAll(/url\(['"]?([^'")?#]+\.(?:webp|png|jpg|woff2?|ttf))/g)) if (!/^(https?:|data:)/.test(m[1])) lit.push(['index.html css', m[1]]);
  const litBad = lit.filter(([, p]) => !exists(p.replace(/^\.\//, '')));
  check('integrity', 'files named in the scripts and the page (exact case)', !litBad.length, say(litBad.map(([f, p]) => f + ': ' + p)));
}

// ---------------------------------------------------------------- i18n
function i18n() {
  const LG = ['fr', 'en', 'de', 'es', 'it', 'nl', 'pt'], U = C.ui;
  const keys = new Set(Object.keys(U.fr));
  const holes = []; for (const lg of LG) for (const k of keys) if (!U[lg] || !U[lg][k] || !String(U[lg][k]).trim()) holes.push(lg + ':' + k);
  check('i18n', 'every interface string in the 7 languages', !holes.length, say(holes));
  const base = run('I18N').fr; const used = new Set();
  for (const f of fs.readdirSync(path.join(G, 'js')).filter(f => f.endsWith('.js'))) {
    const src = fs.readFileSync(path.join(G, 'js', f), 'utf8');
    for (const m of src.matchAll(/\bT\(\s*'([a-z0-9_]+)'\s*[,)]/g)) used.add(m[1]);   // (whole keys only: T('ev_' + id) is built)
  }
  const unknown = [...used].filter(k => !keys.has(k) && !(base && base[k]));
  check('i18n', "every T('key') of the scripts exists", !unknown.length, say(unknown));
  const names = [...C.classes, ...Object.values(C.spells), ...C.hats, ...C.capes, ...C.pets, ...(C.shields || []), ...C.achievements, ...C.maps].filter(o => o.name && typeof o.name === 'object' && LG.some(l => !o.name[l]));
  check('i18n', 'names in the 7 languages (classes, spells, skins, achievements, zones)', !names.length, say(names.map(o => o.id)));
}

// ---------------------------------------------------------------- store
function store() {
  const St = run('Store');
  const ls = {}; ctx.localStorage.getItem = k => (k in ls ? ls[k] : null); ctx.localStorage.setItem = (k, v) => { ls[k] = String(v); };
  const shape = d => { const bad = []; const def = St.defaults();
    for (const k of Object.keys(def)) { const a = def[k], b = d[k]; if (a === null) continue; if (Array.isArray(a) !== Array.isArray(b) || typeof a !== typeof b) bad.push(k); }
    return bad; };
  const cases = {
    'no save': null,
    'old save (before 0.59, no version)': { kamas: 120, unlocked: ['astrub', 'bonta'], owned: ['16_1'], cleared: { astrub: 1 } },
    'partial save (fields missing)': { kamas: 5, unlocked: ['astrub'] },
    'broken fields (null / wrong types)': { kamas: 50, unlocked: null, owned: null, equip: null, cleared: 'x', best: [], settings: null, mastery: null, spellLv: 3, seen: null, kills: null, dofus: null },
    'kamas not a number': { kamas: 'abc', unlocked: ['astrub'] },
    'not JSON': '{broken',
  };
  for (const [name, d] of Object.entries(cases)) {
    for (const k in ls) delete ls[k];
    if (d !== null) ls[St.base] = typeof d === 'string' ? d : JSON.stringify(d);
    let err = null, bad = []; try { const r = St.load(); bad = shape(r); if (typeof r.kamas !== 'number' || !isFinite(r.kamas)) bad.push('kamas'); if (!r.unlocked.includes('astrub')) bad.push('astrub locked'); } catch (e) { err = e.message; }
    check('store', 'loads: ' + name, !err && !bad.length, err || ('wrong fields: ' + bad.join(', ')));
  }
  // the valid data of an old save is kept
  for (const k in ls) delete ls[k]; ls[St.base] = JSON.stringify(cases['old save (before 0.59, no version)']);
  const kept = St.load(); check('store', 'an old save keeps its progress', kept.kamas === 120 && kept.unlocked.includes('bonta') && kept.owned.includes('16_1') && kept.cleared.astrub === 1, JSON.stringify({ k: kept.kamas, u: kept.unlocked }));
  // imports
  const good = St.exportText(); const r1 = St.parseImport(good);
  check('store', 'import: its own export', r1.data && !r1.err, JSON.stringify(r1).slice(0, 200));
  check('store', 'import: refuses what is not a save', St.parseImport('hello').err === 'save_bad' && St.parseImport('{"a":1}').err === 'save_bad' && St.parseImport('[]').err === 'save_bad', 'accepted');
  const newer = JSON.parse(good); newer.v = St.SAVE_V + 1; newer.data.v = St.SAVE_V + 1;
  check('store', 'import: refuses a newer save format', St.parseImport(JSON.stringify(newer)).err === 'save_newer', 'accepted');
  const d0 = Object.assign(St.defaults(), { owned: ['16_1', '16_44', '17_3', '18_1', '82_44'], seen: { a: 1, b: 1 }, kills: { a: 3 }, ttg: { 3: 1, 10: 2 }, souls: { 5: 1 } });
  const rt = St.unpackSave(JSON.parse(JSON.stringify(St.packSave(JSON.parse(JSON.stringify(d0))))));
  const same = JSON.stringify([...rt.owned].sort()) === JSON.stringify([...d0.owned].sort()) && JSON.stringify(rt.ttg) === JSON.stringify(d0.ttg) && rt.seen.a && rt.seen.b;
  check('store', 'save code: packing round trip (skins, seen, cards)', same, JSON.stringify(rt.owned));
  // profiles stay apart
  for (const k in ls) delete ls[k]; St.load(); St.data.kamas = 11; St.save(); St.switchTo(2); St.data.kamas = 22; St.save(); St.switchTo(1);
  check('store', 'profiles: each keeps its own data', St.data.kamas === 11 && JSON.parse(ls[St.keyOf(2)]).kamas === 22, 'profile 1 kamas ' + St.data.kamas);
  for (const k in ls) delete ls[k]; St.load();
}

// ---------------------------------------------------------------- logic
function newRun(cls, map = 'astrub', opts = {}) {
  const R = run(`new Run(Game.C, Object.assign({ cls: '${cls}', sex: 0, colors: [[0,0,0],[0,0,0],[0,0,0]], map: '${map}' }, ${JSON.stringify(opts)}))`);
  ctx.Game.run = R; R.world = SPR.worlds[R.map.world]; R.tiles = {};
  const ins = R.world.inset || [0, 0, 0, 0];
  R.bounds = { x0: 30 + ins[0], x1: R.world.w - 30 - ins[1], y0: 40 + ins[2], y1: R.world.h - 20 - ins[3] };
  R.center = { x: (R.bounds.x0 + R.bounds.x1) / 2, y: (R.bounds.y0 + R.bounds.y1) / 2 };
  R.charSprite = { has: () => true, duration: () => 0.5, sheet: { has: () => true, duration: () => 0.5 } };
  R.player = new (run('Player'))(R, R.charSprite); R.player.x = R.center.x; R.player.y = R.center.y;
  R.addSpell(R.cls.spells[0]); R.recompute(); R.player.hp = R.stats.maxHp; run('Prog').runStart(R);
  return R;
}
function logic() {
  const St = run('Store'); St.data.passLv = {}; St.data.scrolls = {};
  // recompute: the same stats every time (a bonus never counted twice)
  const twice = [];
  for (const c of C.classes) {
    const R = newRun(c.id, 'astrub', { shield: '82_44' });
    R.dofus = C.dofus.slice(0, 2); R.relics = (C.relics || []).slice(0, 3); R.passives = { [C.passives[0].id]: 2 };
    R.recompute(); const a = JSON.stringify(R.stats); R.recompute(); R.recompute(); if (JSON.stringify(R.stats) !== a) twice.push(c.id);
  }
  check('logic', 'stats rebuilt identically (no bonus counted twice)', !twice.length, say(twice));
  // the shield: +1 resistance, only for the classes that wear hats, only a real shield
  const sh = [];
  for (const c of C.classes) {
    const R0 = newRun(c.id), base = R0.stats.armor, R1 = newRun(c.id, 'astrub', { shield: '82_44' }), R2 = newRun(c.id, 'astrub', { shield: 'not_a_shield' });
    const want = c.nohats ? base : base + (C.shieldArmor || 1);
    if (Math.abs(R1.stats.armor - want) > 1e-9 || R2.stats.armor !== base) sh.push(`${c.id}: ${base} -> ${R1.stats.armor} (want ${want}), fake ${R2.stats.armor}`);
  }
  check('logic', 'shield: +1 resistance, not for Roublard / Brigandin / Otomai, not for an unknown id', !sh.length, say(sh, 4));
  // drops: inside the ground the character walks, never on each other (placeDrop looks 11 rings around: past ~50 drops on
  // one spot in a corner the last ones may touch — docs/reports/0.94-qa-audit.md QA-18, accepted)
  const drops = (fill) => { const R = newRun('iop'); R.pickups.length = 0; const b = R.bounds; fill(R, b);
    let over = 0, out = 0; const P = R.pickups;
    for (let i = 0; i < P.length; i++) { const p = P[i]; if (p.x < b.x0 || p.x > b.x1 || p.y < b.y0 || p.y > b.y1) out++; for (let j = i + 1; j < P.length; j++) { const q = P[j], d = p._r + q._r, dx = p.x - q.x, dy = (p.y - q.y) / 0.75; if (dx * dx + dy * dy < d * d - 0.01) over++; } }
    return [over, out, P.length]; };
  const kinds = ['chest', 'kama', 'tmap', 'manuel', 'bread', 'relic', 'dofus', 'booster'];
  const d1 = drops((R, b) => { for (let i = 0; i < 80; i++) R.dropGem(R.center.x, R.center.y, 1, i % 9 === 0 ? 1 : i % 31 === 0 ? 2 : 0); for (const k of kinds) R.dropPickup(k, R.center.x, R.center.y, 1); });
  const d2 = drops((R, b) => { for (let i = 0; i < 30; i++) R.dropGem(b.x0 + 20, b.y0 + 20, 1, i % 9 === 0 ? 1 : 0); for (const k of kinds) R.dropPickup(k, b.x1, b.y1, 1); R.dropPickup('chest', b.x0 - 500, b.y1 + 500, 1); R.dropGem(-1e4, -1e4, 1); });
  check('logic', `drops never overlap nor fall off the ground (${d1[2]} on one spot, ${d2[2]} in corners / outside)`, !d1[0] && !d1[1] && !d2[0] && !d2[1], `${d1[0] + d2[0]} overlaps, ${d1[1] + d2[1]} outside`);
  // the stats' top spell ignores a spell won on the ground
  const Pg = run('Prog'), st = { spellDmg: { epee_iop: 10, fleche_magique: 999 } }, m = Pg.mainSpellDmg(st, C);
  check('logic', "stats: the top spell is computed from class / global / fusion spells", m.epee_iop === 10 && m.fleche_magique === 999, JSON.stringify(m));
  // the quality's default by platform (Game.quality is in main.js, not loaded here): checked in the browser suite
}

// ---------------------------------------------------------------- runtime
function runtime() {
  const errs = [], step = (R, sec) => { const dt = 1 / 30; for (let t = 0; t < sec; t += dt) { R.update(dt); while (ctx.__timers.length) ctx.__timers.shift()(); if (R.player.hp < R.stats.maxHp * 0.5) { R.player.hp = R.stats.maxHp; R.player.dead = false; } } };
  ctx.Game.levelUp = () => { }; ctx.Game.openChest = () => { };
  // every class starts and plays 20 s
  for (const c of C.classes) { try { const R = newRun(c.id); step(R, 20); } catch (e) { errs.push('class ' + c.id + ': ' + e.message); } }
  check('runtime', 'every class starts and plays 20 s', !errs.length, say(errs, 5)); errs.length = 0;
  // every zone a few seconds (time set where its monsters / bosses come)
  for (const m of C.maps) { try { const R = newRun('iop', m.id); R.time = 60; step(R, 6); R.time = 500; step(R, 6); } catch (e) { errs.push('zone ' + m.id + ': ' + e.message); } }
  check('runtime', 'every zone runs (start, then 8:20)', !errs.length, say(errs, 5)); errs.length = 0;
  // every spell, fusion and weapon, at level 1 and at its top, in its own class's run
  const SpellInst = run('SpellInst'), weaponById = run('weaponById');
  const owner = id => C.classes.find(c => c.spells.includes(id)) || C.classes.find(c => (C.spellFusions || []).some(f => f.id === id && f.cls === c.id)) || C.classes.find(c => c.id === 'iop');
  const ids = [...new Set([...C.classes.flatMap(c => c.spells), ...(C.globalSpells || []).map(g => g.id), ...(C.spellFusions || []).map(f => f.id)])];
  // (the damage it did is read back: a spell that throws nothing but hits nothing would pass unseen. Buffs, heals,
  // summons' own blows and the spells that wait for a pickup or a hit legitimately do none: listed, not failed)
  const quiet = [];
  for (const id of ids) for (const lv of [1, 99]) {
    try {
      const R = newRun(owner(id).id); R.time = 240; R.spells = R.spells.filter(s => s.def.id === id); const s = R.spells[0] || R.addSpell(id);
      while (lv > 1 && !s.maxed && s.level < 12) s.levelUp(); R.recompute(); s.cd = 0; step(R, 8);
      if (lv > 1 && !(R.ps.spell[id] > 0)) quiet.push(id);
    } catch (e) { errs.push(`${id} lv${lv}: ${e.message}`); }
  }
  check('runtime', `every spell / fusion cast at level 1 and at its top (${ids.length} spells; no damage of its own: ${quiet.length} — ${say(quiet, 40)})`, !errs.length, say(errs, 6)); errs.length = 0;
  const wids = [...(C.weapons || []).map(w => w.id), ...(C.uniqueWeapons || []).map(w => w.id)];
  for (const id of wids) {
    try { const R = newRun('iop'); R.time = 240; R.applyUpgrade({ kind: 'weapon', id }); for (let i = 1; i < 6; i++) R.weapon.levelUp(); const E = ((C.weaponEvo || {})[id] || [])[0]; if (E) R.applyUpgrade({ kind: 'wevo', id: E.id }); step(R, 4); }
    catch (e) { errs.push(`${id}: ${e.message}`); }
  }
  check('runtime', `every weapon (and its finale) at its top (${wids.length})`, !errs.length, say(errs, 6));
}

const suites = { integrity, i18n, store, logic, runtime };
(async () => {
  for (const [k, f] of Object.entries(suites)) {
    if (only.length && !only.includes(k)) continue;
    const t0 = Date.now();
    try { f(); } catch (e) { check(k, 'the suite itself', false, e.stack.split('\n').slice(0, 3).join(' | ')); }
    results.push({ suite: k, name: '(time)', ok: true, ms: Date.now() - t0, timing: true });
  }
  for (const r of results) console.log(JSON.stringify(r));
  const f = results.filter(r => !r.ok);
  console.log(`UNIT ${results.filter(r => !r.timing).length} checks, ${f.length} failed`);
  process.exit(f.length ? 1 : 0);
})();
