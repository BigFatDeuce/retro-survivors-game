// 0.94: every class spell, global spell and spell fusion cast
// ALONE at its top level by its own class (no weapon, no waves, no events), for 12 s, on 30 sturdy dummies standing on
// rings around the character (70 to 420 units, they never die nor move by themselves). Every hit, status and effect is
// recorded from the game's own code (the real Run / SpellInst in node, tools/checks/sim_node.js's bootstrap), then compared
// with what the spell is said to do:
//   - its parameters (C.spells: damage, slow, stun, poison, burn, mark, heal, push / pull, count, radius, cooldown…)
//   - its French description: a word that promises an effect (ralentit, étourdit / immobilise, poison, brûle, soigne,
//     repousse, attire, invoque, vole la vie, rebondit, transperce…) must be seen happening
// Balance is NOT judged (no damage value is right or wrong here): only that each promised effect happens, that the
// cast rhythm follows the cooldown, that an area centred on the character stays within its radius, and that a
// projectile spell throws as many projectiles as it says.
// usage: node tools/checks/qa_spells.js [spell…]      prints one JSON line per spell ({ id, ok, fails, seen }) and a summary;
//        exit code 1 if a promised effect never happened (tools/qa.py runs it as its 'spells' step)
const S = require('./sim_node.js'); const { ctx, C, SPR, vm } = S;
const run = (c) => vm.runInContext(c, ctx);
const only = process.argv.slice(2);
const Store = run('Store'); Store.data.passLv = {}; Store.data.scrolls = {}; Store.data.spellLv = {};
// the game's Math.random seeded per scene (from the spell's id): a result is the same on every run of the same code
run(`globalThis.__seed = (n) => { let s = n >>> 0; Math.random = () => { s = (s + 0x6D2B79F5) >>> 0; let t = s; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }`);
const hash = (str) => { let h = 2166136261; for (const c of str) h = Math.imul(h ^ c.charCodeAt(0), 16777619); return h >>> 0; };

function newRun(cls) {
  const R = run(`new Run(Game.C, { cls: '${cls}', sex: 0, colors: [[0,0,0],[0,0,0],[0,0,0]], map: 'astrub' })`);
  ctx.Game.run = R; R.world = SPR.worlds[R.map.world]; R.tiles = {};
  const ins = R.world.inset || [0, 0, 0, 0];
  R.bounds = { x0: 30 + ins[0], x1: R.world.w - 30 - ins[1], y0: 40 + ins[2], y1: R.world.h - 20 - ins[3] };
  R.center = { x: (R.bounds.x0 + R.bounds.x1) / 2, y: (R.bounds.y0 + R.bounds.y1) / 2 };
  R.charSprite = { has: () => true, duration: () => 0.5, sheet: { has: () => true, duration: () => 0.5 } };
  R.player = new (run('Player'))(R, R.charSprite); R.player.x = R.center.x; R.player.y = R.center.y;
  run('Prog').runStart(R);
  return R;
}
const owner = (id) => C.classes.find(c => c.spells.includes(id)) || C.classes.find(c => (C.spellFusions || []).some(f => f.id === id && f.cls === c.id)) || C.classes.find(c => c.id === 'iop');

// the promises of the French descriptions (whole words / stems), and how each is seen
const WORDS = [
  ['slow', /ralenti|ralentit|ralentis|gèle|gel[ée]/i], ['stun', /étourdi|immobilis|paralys|fige|figé|assomm/i], ['poison', /poison|empoisonn|venin/i],
  ['burn', /brûl|enflamm|embras/i], ['heal', /soign|soin|régénèr|rend .*PV|vie perdue/i], ['push', /repouss|projette|éject|renvers/i], ['pull', /attir/i],
  ['summon', /invoqu/i], ['leech', /vol de vie|vole .*vie|draine|aspire la vie/i], ['mark', /(^|[^a-zà-ÿ])vulnérab|marqu/i],   // ('invulnérable' is not a mark)
];

function scene(id, mode) {
  const moving = mode === 'moving' || mode === true, kill = mode === 'kill'; ctx.__seed(hash(id + (mode || '')));
  const def = C.spells[id], cls = owner(id).id, R = newRun(cls), P = R.player, T = moving ? 4 : kill ? 60 : def.base.allOrNothing ? 60 : 12, dt = 1 / 30;   // (walking monsters: judged while the summons live; a 60 / 40 gamble: long enough to see both sides)
  R.spells.length = 0; R.weapon = null; R.spawner = () => { }; R.updateElites = () => { }; R.randEvents = []; R.nextRandEvent = 1e9; R.time = 60;   // (events keep running: the Cawotte heals there)
  ctx.Game.levelUp = () => { }; ctx.Game.openChest = () => { };
  const s = R.addSpell(id); while (!s.maxed) s.levelUp(); R.recompute(); s.cd = 0.05;
  const mobId = 'bouftou';
  const dummies = [];
  const put = (r, a) => {   // (kill: ordinary life, a new one where one died)
    const m = R.spawnMob(mobId, P.x + Math.cos(a) * r, P.y + Math.sin(a) * r * 0.75, { force: true, keep: true, noArchi: true });
    if (!m) return null; m.hp = m.maxHp = kill ? 40 : 1e12; /* (kill: weak ones, so a 15 s scene kills enough of them for the chances per kill to show) */ m.qa = { r, a, home: [m.x, m.y], o: [m.x, m.y] }; if (!moving) m.speed = 0; m.dmg = 0; m.atkT = 1e9; return m; };
  for (const [r, n] of [[70, 4], [140, 6], [220, 6], [320, 7], [420, 7]]) for (let i = 0; i < n; i++) { const m = put(r, i / n * Math.PI * 2 + r * 0.01); if (m) dummies.push(m); }
  const seen = { dmg: 0, hits: 0, slow: 0, stun: 0, poison: 0, burn: 0, mark: 0, heal: 0, push: 0, pull: 0, summon: 0, leech: 0, casts: 0, projMax: 0, farHit: 0, armor: 0, kamas: 0, bounce: 0 };
  const hitBy = new Map();
  const dm = R.damageMob.bind(R);
  R.damageMob = (m, d, src, ...a) => { if (m.qa) { seen.hits++; hitBy.set(m, (hitBy.get(m) || 0) + 1); const h = m.qa.home, f = Math.min(Math.hypot(h[0] - P.x, h[1] - P.y), Math.hypot(m.x - P.x, m.y - P.y)) - m.r; if ((inCast || def.t === 'aura') && f > seen.farHit) seen.farHit = f; /* (a pulse's own blows land as it is cast; what a fused rider drops later — rocks, strikes — falls where the monsters are) */ } return dm(m, d, src, ...a); };   // (the game's metric: mobsInRadius = a circle, r + the monster's size; where it stood at the tick's start or now: a push / pull may come before the blow)
  // (effects only, never calls: a call that does nothing must not pass — the life a steal really gave back)
  const lh = P.leechHeal ? P.leechHeal.bind(P) : null; if (lh) P.leechHeal = (v, ...a) => { const b = P.hp, r = lh(v, ...a); if (P.hp > b) seen.leech += P.hp - b; return r; };
  const cast = s.cast.bind(s); let projBefore = 0, inCast = false;
  s.cast = () => { projBefore = R.projs.length; inCast = true; let ok; try { ok = cast(); } finally { inCast = false; } if (ok !== false) { seen.casts++; seen.projMax = Math.max(seen.projMax, R.projs.filter(q => q.spell === s).length - 0); } return ok; };
  const armor0 = R.stats.armor, k0 = R.kamas, dp = R.dropPickup.bind(R); seen.kamaDrops = 0;
  R.dropPickup = (kind, ...a) => { if (kind === 'kama') seen.kamaDrops++; return dp(kind, ...a); };
  let hp = P.hp = R.stats.maxHp * 0.5;
  for (let t = 0; t < T; t += dt) {
    if (kill && seen.kamaDrops + R.kamas - k0 > 0) break;   // (kill: until the first kama, 60 s at most)
    R.update(dt); while (ctx.__timers.length) ctx.__timers.shift()();
    if (P.hp > hp + 1e-6) seen.heal++;
    if (P.hp > R.stats.maxHp * 0.9 || P.hp < R.stats.maxHp * 0.2) P.hp = R.stats.maxHp * 0.5;
    hp = P.hp; P.invulnUntil = R.time + 1; P.dead = false;
    if (P.tempArmor && P.tempArmor.until > R.time) seen.armor++;
    for (const m of dummies) {
      if (m.slowUntil > R.time && m.slowAmt > 0) seen.slow++;
      if (m.stunUntil > R.time) seen.stun++;
      if (m.burnUntil > R.time) seen.burn++;
      if (m.poisonUntil > R.time) seen.poison++;
      if (m.markUntil > R.time && m.markAmt > 0) seen.mark++;
      const d0 = Math.hypot(m.qa.o[0] - P.x, m.qa.o[1] - P.y), d1 = Math.hypot(m.x - P.x, m.y - P.y);
      if (!moving) { if (d1 > d0 + 15) seen.push++; else if (d1 < d0 - 15) seen.pull++; }   // (from where it stood at first: a push moves it a few units a tick)
      m.qa.home = [m.x, m.y]; if (!kill) { m.hp = m.maxHp; m.dying = false; }
    }
    if (kill) for (let i = 0; i < dummies.length; i++) if (dummies[i].dying || dummies[i].hp <= 0) { seen.kills = (seen.kills || 0) + 1; const n = put(dummies[i].qa.r, dummies[i].qa.a); if (n) dummies[i] = n; }
    seen.summon = Math.max(seen.summon, R.summons.filter(o => o.spell === s).length + (R.allies ? R.allies.filter(o => o.spell === s).length : 0));
  }
  seen.dmg = Math.round(R.ps.spell[id] || 0); seen.kamas = R.kamas - k0; seen.multiHit = [...hitBy.values()].filter(n => n > 1).length; seen.mobsHit = hitBy.size;
  seen.cd = +s.cooldown().toFixed(2);
  if (moving) {   // the monsters that walk: closer to a taunting summon than to the character?
    const tn = R.summons.filter(o => o.spell === s && o.taunt); let toward = 0, n = 0;
    for (const m of dummies) { const c = tn.length ? tn.reduce((a, b) => Math.hypot(b.x - m.x, b.y - m.y) < Math.hypot(a.x - m.x, a.y - m.y) ? b : a) : null; if (!c) continue; n++; if (Math.hypot(c.x - m.x, c.y - m.y) < Math.hypot(c.x - m.qa.o[0], c.y - m.qa.o[1]) - 20) toward++; }
    seen.taunted = n ? toward / n : 0;
  }
  return { R, s, def, seen, T };
}

const results = [];
const ids = only.length ? only : [...new Set([...C.classes.flatMap(c => c.spells), ...(C.globalSpells || []).map(g => g.id), ...(C.spellFusions || []).map(f => f.id)])];
for (const id of ids) {
  const def = C.spells[id]; if (!def) { results.push({ id, ok: false, fails: ['unknown spell'] }); continue; }
  let sc; try { sc = scene(id); } catch (e) { results.push({ id, ok: false, fails: ['error: ' + e.message] }); continue; }
  const { s, seen, T } = sc, p = s.p, t = def.t, fails = [], notes = [];
  const desc = (def.desc && def.desc.fr) || '';
  // damage: a spell with damage hurts something (its summons' blows count as its own)
  if (p.dmg > 0 && !seen.dmg) fails.push(`it has damage (${p.dmg}) but hurt no one in ${T} s`);
  // the cooldown: lasting things (orbits, auras, summons, traps, zones that wait for room) are not cast on a clock
  const clock = ['projectile', 'strike', 'melee', 'pulse', 'line', 'beam', 'cone', 'toss', 'bomb', 'leap', 'dash', 'detonate'].includes(t);
  if (clock && seen.cd > 0) { const want = (T - 0.1) / seen.cd; if (seen.casts < Math.floor(want * 0.6) || seen.casts > Math.ceil(want * 1.4) + 1) fails.push(`cast ${seen.casts} times in ${T} s, its cooldown ${seen.cd} s says about ${want.toFixed(1)}`); }
  // a projectile spell throws its count at once (+ the character's 'Démultiplication', 0 here)
  if (t === 'projectile' && p.count > 0 && seen.projMax && seen.projMax < p.count) fails.push(`throws ${seen.projMax} projectiles at a time, says ${p.count}`);
  // an area centred on the character stays within its radius (dummy size and a little margin allowed)
  if (['pulse', 'aura'].includes(t) && p.radius > 0 && seen.farHit > p.radius * sc.R.stats.area * 1.15 + 20) fails.push(`hits ${Math.round(seen.farHit)} units away, its radius is ${Math.round(p.radius * sc.R.stats.area)}`);
  // what the parameters promise
  if (p.slow > 0 && !seen.slow) fails.push(`slow ${p.slow}: no monster slowed`);
  if (p.stun > 0 && !seen.stun) fails.push(`stun ${p.stun}: no monster stunned`);
  if ((p.poison > 0 || p.puddlePoison > 0) && !seen.poison) fails.push('poison: no monster poisoned');
  if (p.burn > 0 && !seen.burn) fails.push('burn: no monster burning');
  if (p.mark > 0 && !seen.mark) fails.push('mark: no monster marked');
  if ((p.heal > 0 || p.healTick > 0 || t === 'heal') && !seen.heal) fails.push('heal: the character never healed (at half life)');
  if (p.armorBuff > 0 && !seen.armor) fails.push('armorBuff: no armour bonus seen');
  if (p.pull > 0 && !seen.pull) fails.push('pull: no monster drawn in');
  if (p.taunt) { const mv = scene(id, 'moving').seen; seen.taunted = +mv.taunted.toFixed(2); if (mv.taunted < 0.3) fails.push(`taunt: only ${Math.round(mv.taunted * 100)} % of the walking monsters went for the summon`); }
  if (t === 'summon' && !seen.summon) fails.push('summon: nothing summoned');
  if (p.leech > 0 && !seen.leech) fails.push('leech: no life stolen');
  if (p.bounce > 0 && seen.multiHit === 0 && seen.mobsHit < 2) fails.push('bounce: hit only one monster');
  // kamas: by the spell itself (the Coffre Animé, the pickaxe) or a chance on each monster it kills (then monsters that die)
  const perKill = p.rKama > 0 || p.steal1 > 0 || p.gold > 0;
  if (perKill || p.kamas > 0 || t === 'pioche') {
    const k = perKill ? scene(id, 'kill').seen : seen; seen.kamaDrops = k.kamaDrops; seen.kills = k.kills;
    // (a chance per kill is judged only once enough monsters died for 'none at all' to be under 0.5 %)
    const ch = Math.max(p.rKama || 0, p.steal1 || 0, p.gold || 0), need = perKill ? Math.ceil(Math.log(0.005) / Math.log(1 - Math.min(0.95, ch || 0.1))) : 0;
    if (!k.kamas && !k.kamaDrops) (perKill && (k.kills || 0) < need ? notes : fails).push(`kamas: none dropped nor won` + (perKill ? ` (${k.kills || 0} monsters killed in 60 s${(k.kills || 0) < need ? `, ${need} needed to judge a ${Math.round(ch * 100)} % chance` : ''})` : ` in ${T} s`));
  }
  // what the description promises (words), seen happening
  for (const [k, re] of WORDS) {
    if (!re.test(desc)) continue;
    // (a toxic cloud / a burning puddle hurts what stays in it: its 'poison' / 'flames' are its ticks, not a status)
    const ok = k === 'summon' ? seen.summon > 0 : k === 'pull' ? seen.pull > 0 || seen.taunted >= 0.3 : k === 'poison' ? seen.poison > 0 || (p.cloud && seen.multiHit > 0) : k === 'burn' ? seen.burn > 0 || (p.puddle && seen.multiHit > 0) : seen[k] > 0;
    if (!ok && !fails.some(f => f.startsWith(k))) fails.push(`the description says "${(desc.match(re) || [''])[0]}" (${k}) but it never happened`);
  }
  results.push({ id, cls: owner(id).id, t, ok: !fails.length, fails, notes, seen });
}
for (const r of results) console.log(JSON.stringify(r));
const bad = results.filter(r => !r.ok);
console.log(`SPELLS ${results.length} spells, ${bad.length} with a promise not kept`);
process.exit(bad.length ? 1 : 0);
