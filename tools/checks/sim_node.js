// Headless balance simulator: runs the real game logic (util/spells/game/progress) with stubs and a bot player.
// HEAL=1 (heals / life steal picked first), IDLE=1 (the character stands still)
// usage: node sim_node.js <cls|all|a,b> <map> <minutes>   env: GOD=1 (never dies), DODGE=1 (bot dashes), VERBOSE=1,  HARD=1 (Difficile),
//        SHOP=n (every class spell bought to level n), XP=1 (print level-up times)
// spell bench: BENCH=all|id[,id] [LV=6] [T0=240] [DUR=90] node sim_node.js x astrub 0  -> each spell alone (GOD, no level-ups),
//        damage per second from minute T0/60 for DUR seconds (the cooldown pass of 0.23)
const fs = require('fs'), vm = require('vm'), path = require('path');
const G = process.env.GAME || (__dirname + '/../../game');
const C = JSON.parse(fs.readFileSync(process.env.GAME_C || (G + '/data/content.json')));
const SPR = JSON.parse(fs.readFileSync(G + '/data/sprites.json'));
const noop = new Proxy({}, { get: (t, k) => k === 'SND' ? { ui: {}, chars: {}, mobs: {} } : (k === 'spellKeys' ? () => [] : k === 'mobSnd' || k === 'charSnd' ? () => null : () => Promise.resolve()) });
const ctx = {
  console, Math, JSON, Date, Map, Set, Array, Object, Number, String, Promise, Proxy, Uint8Array, Symbol, Infinity, NaN, isNaN, parseInt, parseFloat,
  setTimeout: (f) => { ctx.__timers.push(f); }, __timers: [],
  performance: { now: () => 0 }, navigator: { language: 'fr' }, localStorage: { getItem: () => null, setItem: () => { } },
  document: { createElement: () => ({ getContext: () => ({}) }), fonts: { load: async () => { } }, addEventListener() { } }, window: { addEventListener() { } },
  __noop: noop,
};
vm.createContext(ctx);
for (const f of ['util.js', 'assets.js', 'spells.js', 'game.js', 'extras.js', 'gspells.js', 'weapons.js', 'events.js', 'bosses.js', 'juice.js', 'sfusions.js', 'nowel.js', 'progress.js']) vm.runInContext(fs.readFileSync(path.join(G, 'js', f), 'utf8'), ctx, { filename: f });
vm.runInContext(`
SPR = __SPR;
var Audio2 = __noop;
var UI = { modalOpen(){ return false; }, botPick(){} };
var toast = null;
var Game = { viewW: 1060, viewH: 600, zoom: 1, C: __C, levelUps: 0, run: null, debug: {}, lvT: [],
  levelUp() { const R = this.run; const opts = R.upgradeOptions(3); this.levelUps++; this.lvT.push(Math.round(R.time));
    if (!opts.length) { R.applyUpgrade({ kind: 'kamas' }); return; }
    // HEAL=1: heals and life steal first (the heal / life-steal check of every balance pass)
    const healish = o => (o.kind === 'spell' && (() => { const b = __C.spells[o.id].base; return b.heal || b.leech || b.healer; })()) || (o.kind === 'passive' && ['vol_de_vie', 'soins', 'vitalite'].includes(o.id));
    const pr = o => __HEAL && healish(o) ? 20 : o.kind === 'fusion' ? 9.5 : o.kind === 'spell' ? (o.isNew ? 10 : 8) : o.kind === 'weapon' ? 7 : o.kind === 'wevo' ? 9 : ({ force: 6, pa: 6, vitalite: 5, intelligence: 4, resistances: 4, invocations: 7, pm: 3 }[o.id] || 2);
    opts.sort((a, b) => pr(b) - pr(a)); R.applyUpgrade(opts[0]); },
  openChest(n) { const R = this.run; for (let i = 0; i < (n >= 3 ? 3 : 1); i++) { const o = R.upgradeOptions(1, true)[0]; if (o) R.applyUpgrade(o); } },
  doorPrompt() { this.run.door = null; this.run.doorDone = true; }, enterTot() { }, runOver(v) { this.over = v; }, dofusExploit() { }, tailorWin() { },
};
Store.load(); Store.data.settings.dmgNumbers = false; Store.data.settings.shake = false; Store.data.settings.chat = false;
if (!__AID) for (const id in (__C.beginnerAid || {})) Store.data.clearedNormal[id] = 1;   // (0.95: the sims measure the zones without the beginners' help; AID=1 keeps it)
MobSheets.c = {}; MobSheets.load = () => Promise.resolve(null);
FxSheets.c = {}; FxSheets.get = () => null; FxSheets.load = () => Promise.resolve(null);
`, Object.assign(ctx, { __C: C, __SPR: SPR, __HEAL: !!process.env.HEAL, __AID: !!process.env.AID }));
vm.runInContext(`for (const k in SPR.mobs) { const m = SPR.mobs[k]; MobSheets.c[k] = new Sheet(null, m); }`, ctx);
const Bot = vm.runInContext(`({
  vector(R) {
    const P = R.player; let x = 0, y = 0;
    for (const m of R.mobs) { if (m.dying) continue; const dx = P.x - m.x, dy = P.y - m.y, d2 = dx*dx+dy*dy; if (d2 > 260*260) continue; const d = Math.sqrt(d2)||1; const w = (m.boss?3:1)*3000/(d2+400); x += dx/d*w; y += dy/d*w; }
    for (const e of R.eprojs) { const dx = P.x - e.x, dy = P.y - e.y, d2 = dx*dx+dy*dy; if (d2 < 120*120) { const d = Math.sqrt(d2)||1; x += dx/d*2; y += dy/d*2; } }
    for (const t of R.teles) { if (t.kind === 'circle') { const dx = P.x - t.x, dy = P.y - t.y, d = Math.hypot(dx, dy)||1; if (d < t.r + 30) { x += dx/d*4; y += dy/d*4; } } }
    let best = null, bd = 380*380; for (const g of R.pickups) { const d = dist2(P.x, P.y, g.x, g.y); if (d < bd) { bd = d; best = g; } }
    if (best) { const dx = best.x - P.x, dy = best.y - P.y, d = Math.hypot(dx, dy)||1; x += dx/d*0.6; y += dy/d*0.6; }
    const b = R.bounds, m = 220;
    if (P.x < b.x0+m) x += (b.x0+m-P.x)/m*2; if (P.x > b.x1-m) x -= (P.x-b.x1+m)/m*2; if (P.y < b.y0+m) y += (b.y0+m-P.y)/m*2; if (P.y > b.y1-m) y -= (P.y-b.y1+m)/m*2;
    if (Math.hypot(x, y) < 0.3) { const a = R.time*0.3; x += Math.cos(a)*0.5; y += Math.sin(a)*0.5; }
    const l = Math.hypot(x, y); return l > 1 ? { x: x/l, y: y/l } : { x, y };
  } })`, ctx);
ctx.Input = { vector: () => process.env.IDLE ? { x: 0, y: 0 } : Bot.vector(ctx.Game.run), dev: 'kb' };   // IDLE=1: the character never moves
vm.runInContext('var Input = this.Input;', ctx);

async function runSim(cls, map, minutes) {
  if (process.env.SHOP) { const n = +process.env.SHOP; const c = C.classes.find(x => x.id === cls); for (const s of c.spells) vm.runInContext('Store', ctx).data.spellLv[s] = n; }
  const R = vm.runInContext(`new Run(Game.C, { cls: '${cls}', sex: 0, colors: [[0,0,0],[0,0,0],[0,0,0]], map: '${map}', hard: ${process.env.HARD ? 'true' : 'false'} })`, ctx);
  ctx.Game.run = R; ctx.Game.lvT = [];
  R.world = SPR.worlds[R.map.world]; R.tiles = {};
  const ins = R.world.inset || [0, 0, 0, 0];
  R.bounds = { x0: 30 + ins[0], x1: R.world.w - 30 - ins[1], y0: 40 + ins[2], y1: R.world.h - 20 - ins[3] };
  R.center = { x: (R.bounds.x0 + R.bounds.x1) / 2, y: (R.bounds.y0 + R.bounds.y1) / 2 };
  R.charSprite = { has: () => true, duration: () => 0.5, sheet: { has: () => true, duration: () => 0.5 } };
  R.player = new (vm.runInContext('Player', ctx))(R, R.charSprite); R.player.x = R.center.x; R.player.y = R.center.y;
  R.addSpell(R.cls.spells[0]); R.recompute(); R.player.hp = R.stats.maxHp;
  vm.runInContext('Prog', ctx).runStart(R);
  const dt = 1 / 30; const log = [];
  // 0.81: ALLXP=1 = every amber is picked up the moment it drops (the 'all ambers' player); allMaxT = when every spell
  // slot holds a maxed spell; drops = normal ambers that fell (each map's amberRate applied)
  let allMaxT = null, drops = 0; const orgGem = R.dropGem;
  R.dropGem = function (x, y, v, big) { drops++; if (process.env.ALLXP) { this.addXP(v); return; } return orgGem.call(this, x, y, v, big); };
  let nextLog = 60, minHp = 1e9, dmgTaken = 0, lastHp = R.player.hp, hits = 0, big = 0;
  const bossKill = {};
  while (R.time < minutes * 60 && !R.over) {
    R.update(dt);
    while (ctx.__timers.length) ctx.__timers.shift()();
    if (process.env.DODGE && R.time >= R.player.dodgeReady) { for (const m of R.mobs) if (!m.dying && (m.x - R.player.x) ** 2 + (m.y - R.player.y) ** 2 < 70 * 70) { R.player.dodge(); break; } }
    if (R.player.hp < lastHp) { const d = lastHp - R.player.hp; dmgTaken += d; hits++; if (d > R.stats.maxHp * 0.25) big++; }
    if (process.env.GOD && (R.player.hp < R.stats.maxHp * 0.3 || process.env.GOD === '2')) { R.player.hp = R.stats.maxHp; R.player.dead = false; }   // (GOD=2, the audit: never hurt)
    lastHp = R.player.hp;
    minHp = Math.min(minHp, R.player.hp / R.stats.maxHp);
    for (const b of R.bossAlive) { if (!bossKill[b.def.id]) bossKill[b.def.id] = { spawn: Math.round(R.time) }; }
    for (const id in bossKill) if (!bossKill[id].dead && !R.bossAlive.some(b => b.def.id === id)) { bossKill[id].dead = Math.round(R.time); }
    if (R.time >= nextLog) { nextLog += 60; log.push(`${Math.round(R.time / 60)}m lv${R.level} hp${Math.round(R.player.hp)}/${R.stats.maxHp} k${R.kills} mobs${R.mobs.length} sp:${R.spells.map(s => s.level).join('')} ${R.bossAlive.map(b => b.def.id + ' ' + Math.round(b.hp / b.maxHp * 100) + '%').join(',')}`); }
    if (allMaxT === null && R.spells.length >= R.spellSlots() && R.spells.every(s => s.maxed)) allMaxT = Math.round(R.time);
    if (R.player.dead) break;
  }
  const wpn = R.weapon ? R.weapon.def.id + (R.weapon.finale ? '+' + R.weapon.finale.id : '') + (R.weapon.fusion ? '+' + R.weapon.fusion.id : '') : null;
  return { allMaxT, drops, wpn, cls, map, t: Math.round(R.time), dead: R.player.dead, lvl: R.level, kills: R.kills, minHp: Math.round(minHp * 100), dmgTaken: Math.round(dmgTaken), hits, big, boss: bossKill, victory: R.finalKilled, lvT: ctx.Game.lvT.slice(0, 20), log };
}
async function bench(id, map, lv, t0, dur) {
  const owner = C.classes.find(c => c.spells.includes(id)) || C.classes.find(c => c.id === (C.spells[id] || {}).cls) || C.classes.find(c => c.id === 'iop');   // (0.60: a spell fusion with its class)
  const R = vm.runInContext(`new Run(Game.C, { cls: '${owner.id}', sex: 0, colors: [[0,0,0],[0,0,0],[0,0,0]], map: '${map}' })`, ctx);
  ctx.Game.run = R; ctx.Game.levelUp = () => { }; ctx.Game.openChest = () => { };
  R.world = SPR.worlds[R.map.world]; R.tiles = {};
  const ins = R.world.inset || [0, 0, 0, 0];
  R.bounds = { x0: 30 + ins[0], x1: R.world.w - 30 - ins[1], y0: 40 + ins[2], y1: R.world.h - 20 - ins[3] };
  R.center = { x: (R.bounds.x0 + R.bounds.x1) / 2, y: (R.bounds.y0 + R.bounds.y1) / 2 };
  R.charSprite = { has: () => true, duration: () => 0.5, sheet: { has: () => true, duration: () => 0.5 } };
  R.player = new (vm.runInContext('Player', ctx))(R, R.charSprite); R.player.x = R.center.x; R.player.y = R.center.y;
  const wd = vm.runInContext('weaponById', ctx)(C, id);   // a weapon: benched alone too (BENCH=weapons)
  const s = wd ? (R.weapon = new (vm.runInContext('SpellInst', ctx))(R, wd)) : R.addSpell(id); if (wd) R.spells = []; for (let i = 1; i < lv; i++) s.levelUp(); R.level = 15 + lv * 3; R.recompute(); R.player.hp = R.stats.maxHp;
  vm.runInContext('Prog', ctx).runStart(R);
  R.time = t0; R.bossQueue = []; const dt = 1 / 30; let k0 = 0, d0 = 0, started = false;
  while (R.time < t0 + 15 + dur) {
    if (!started && R.time >= t0 + 15) { started = true; d0 = R.ps.spell[id] || 0; k0 = R.kills; }   // 15 s to fill the screen
    R.update(dt); while (ctx.__timers.length) ctx.__timers.shift()();
    if (R.player.hp < R.stats.maxHp * 0.5) R.player.hp = R.stats.maxHp;
    R.bossAlive.forEach(b => { b.dying = true; b.hp = 0; }); R.bossAlive.length = 0;
  }
  return { id, cls: owner.id, t: s.def.t, lv, cd: +s.p.cd.toFixed(2), dps: Math.round(((R.ps.spell[id] || 0) - d0) / dur), kills: R.kills - k0 };
}
// AUDIT=1 node sim_node.js x x [minutes]: the release check (0.38) — every class on every zone (GOD, minutes), errors
// caught with their stack, what dropped / happened per run (rare items, ToT's door, portal, merchant, Tofuzmo, bosses);
// then every characteristic, relic and Dofus is applied alone and must change the stats it says
async function audit(minutes) {
  const fails = [], tot = {}; let runs = 0;
  const Run = vm.runInContext('Run', ctx), orig = Run.prototype.dropPickup;
  Run.prototype.dropPickup = function (kind, x, y, v) { const k = kind === 'chest' ? 'chest' : kind; this._drops = this._drops || {}; this._drops[k] = (this._drops[k] || 0) + 1; return orig.call(this, kind, x, y, v); };
  process.env.GOD = '2';
  const only = process.env.AUDIT_CLS ? process.env.AUDIT_CLS.split(',') : null, onlyM = process.env.AUDIT_MAPS ? process.env.AUDIT_MAPS.split(',') : null;
  for (const m of C.maps) for (const c of C.classes) {
    if ((only && !only.includes(c.id)) || (onlyM && !onlyM.includes(m.id))) continue;
    let r; const t0 = Date.now();
    try { r = await runSim(c.id, m.id, minutes); } catch (e) { fails.push(`${c.id}@${m.id}: ${e.stack.split('\n').slice(0, 3).join(' | ')}`); continue; }
    const R = ctx.Game.run; runs++;
    const ev = { door: !!(R.doorDone || R.door), portal: !!R.portalRun, merchant: !!R.merchantDone, mutant: !!(R.mobs.some(o => o.def.id === 'tofu_mutant') || R.mutantSeen), boosterSpot: !!R.boosterSpot };
    for (const k in (R._drops || {})) tot[k] = (tot[k] || 0) + R._drops[k];
    for (const k in ev) if (ev[k]) tot['ev_' + k] = (tot['ev_' + k] || 0) + 1;
    tot.bossesKilled = (tot.bossesKilled || 0) + Object.values(r.boss).filter(b => b.dead).length;
    tot.victories = (tot.victories || 0) + (r.victory ? 1 : 0);
    if (process.env.VERBOSE) console.log(c.id, m.id, 't' + r.t, r.dead ? 'DEAD' : '', R.over ? 'over:' + R.over : '', r.lvl, r.kills, JSON.stringify(R._drops), ((Date.now() - t0) / 1000).toFixed(1) + 's');
  }
  console.log('RUNS', runs, 'FAILS', fails.length); fails.slice(0, 20).forEach(f => console.log('  FAIL', f));
  console.log('TOTALS', JSON.stringify(tot));
  // characteristics / relics / Dofus: each alone must move its stat
  const R = vm.runInContext(`new Run(Game.C, { cls: 'iop', sex: 0, colors: [[0,0,0],[0,0,0],[0,0,0]], map: 'astrub' })`, ctx); ctx.Game.run = R;
  R.charSprite = { has: () => true, duration: () => 0.5, sheet: { has: () => true, duration: () => 0.5 } };
  R.player = new (vm.runInContext('Player', ctx))(R, R.charSprite); R.dofus = []; R.recompute(); const base = JSON.parse(JSON.stringify(R.stats)); const bad = [];
  const diff = () => Object.keys(R.stats).filter(k => typeof R.stats[k] === 'number' && Math.abs(R.stats[k] - (base[k] || 0)) > 1e-9);
  for (const p of C.passives) { R.passives = { [p.id]: 1 }; R.recompute(); const d = diff(); if (!d.length) bad.push('passive ' + p.id + ' (' + p.stat + ') changes nothing'); }
  R.passives = {};
  for (const r of C.relics) { R.relics = [r]; R.recompute(); const d = diff(); if (!d.length) bad.push('relic ' + r.id + ' changes nothing'); }
  R.relics = [];
  for (const d0 of C.dofus) { R.dofus = [d0]; R.recompute(); if (!diff().length && Object.keys(d0.bonus || {}).length) bad.push('dofus ' + d0.id + ' changes nothing'); }
  R.dofus = [];
  console.log('STATS', bad.length ? bad.join('; ') : 'every characteristic, relic and Dofus changes the stats');
}
// 0.93: tools/checks/qa_unit.js reuses this bootstrap (the game's logic in a vm with stubs) and runSim
module.exports = { ctx, C, SPR, vm, runSim };
if (require.main === module) (async () => {
  const [cls, map, minutes] = process.argv.slice(2);
  if (process.env.BENCH) {
    const ids = process.env.BENCH === 'weapons' ? [...C.weapons, ...(C.uniqueWeapons || [])].map(w => w.id) : process.env.BENCH === 'all' ? [...C.classes.flatMap(c => c.spells), ...(C.globalSpells || []).map(g => g.id)] : process.env.BENCH.split(',');
    for (const id of [...new Set(ids)]) for (const lv of (process.env.LV || '1,6').split(',').map(Number)) console.log(JSON.stringify(await bench(id, map || 'astrub', lv, +(process.env.T0 || 240), +(process.env.DUR || 90))));
    return;
  }
  if (process.env.AUDIT) return audit(+(minutes || 11));
  const classes = cls === 'all' ? C.classes.map(c => c.id) : cls.split(',');
  for (const c of classes) {
    const r = await runSim(c, map, +minutes);
    const o = { cls: r.cls, map: r.map, t: r.t, dead: r.dead, lvl: r.lvl, kills: r.kills, minHp: r.minHp, hits: r.hits, big: r.big, victory: r.victory };
    if (process.env.XP) { o.lvT = r.lvT; o.allMaxT = r.allMaxT; o.drops = r.drops; }
    if (process.env.WPN) o.wpn = r.wpn;
    if (process.env.BOSS) o.boss = r.boss;
    console.log(JSON.stringify(o));
    if (process.env.VERBOSE) console.log(r.log.join('\n'));
  }
})();
