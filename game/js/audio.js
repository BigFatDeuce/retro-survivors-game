'use strict';
// ---------------------------------------------------------------- audio
const Audio2 = {
  ctx: null, sfxGain: null, buffers: {}, loading: {}, music: null, musicName: null, musicVol: 0.6, sfxVol: 0.7,
  playing: 0, lastPlay: {},
  init() {
    if (this.ctx) return;
    try {
      this.ctx = new (window.AudioContext || window.webkitAudioContext)();
      this.sfxGain = this.ctx.createGain(); this.sfxGain.gain.value = this.sfxVol; this.sfxGain.connect(this.ctx.destination);
    } catch (e) { this.ctx = null; }
  },
  // 0.97 (the APK's music went on ~5 s after the app was closed): every sound stops at once, nothing faded — a fade
  // runs on requestAnimationFrame, which stops with a hidden page, so a track fading out kept playing; resume() brings
  // the wanted music back (a class theme playing is dropped, the music it ducked comes back instead)
  halt() {
    this.halted = true;   // (0.98.2: nothing starts until resume: a track still loading, a fade, a timer)
    try { if (this.ctx && this.ctx.state === 'running') this.ctx.suspend(); } catch (e) { }
    const j = this._jingle; if (j) { this._jingle = null; j._want = false; this._ducked = false; }
    for (const a of this._els || []) { a._fadeTok = (a._fadeTok || 0) + 1; try { a.pause(); } catch (e) { } }
  },
  track(a) { const s = (this._els = this._els || new Set()); for (const e of s) if (e.paused && !e._want && e !== this.music) s.delete(e); s.add(a); return a; },   // (the media elements alive, for halt)
  resume() { this.halted = false; if (this.ctx && this.ctx.state === 'suspended') this.ctx.resume(); if (this.music && this.music.paused && this.wantMusic && !this._ducked) { this.music._want = true; this.music.volume = Math.max(0, Math.min(1, this.musicVol)); this.music.play().catch(() => { }); } },   // (0.98.2: its volume too, a halted fade-in stayed low)
  setVolumes(m, s) {
    this.musicVol = m; this.sfxVol = s;
    if (this.sfxGain) this.sfxGain.gain.value = s;
    if (this.music && !this._ducked) { this.music._fadeTok = (this.music._fadeTok || 0) + 1; this.music.volume = m; }
    if (this._jingle) this._jingle.volume = this._jingle._fx ? s : m * 0.9;
  },
  async loadSfx(name) {
    if (!this.ctx) return null;
    if (this.buffers[name]) return this.buffers[name];
    if (this.loading[name]) return this.loading[name];
    this.loading[name] = (async () => {
      let b = null;
      const ent = this.SND.pack && this.SND.pack[name];
      if (ent) { const pb = await this.loadPack(); if (pb) b = pb.slice(ent[0], ent[0] + ent[1]); }
      if (!b) b = await fetch(`assets/audio/sfx/${name}.mp3`).then(r => { if (!r.ok) throw new Error('404'); return r.arrayBuffer(); });
      const buf = await this.ctx.decodeAudioData(b);
      return (this.buffers[name] = buf);
    })().catch(() => null);
    return this.loading[name];
  },
  // all sfx live in one packed file (assets/audio/sfx_pack.mp3), sliced with the offsets from sounds.json
  loadPack() {
    if (!this._pack) this._pack = fetch('assets/audio/sfx_pack.mp3').then(r => (r.ok ? r.arrayBuffer() : null)).catch(() => null);
    return this._pack;
  },
  // gap: the shortest time between two plays of this sound (0.07 s; the hit sounds pass their own, 0.84); hits may use
  // a few more voices than the 14 of the other sounds (a hit cut by music / ambience was the 'missing' projectile sound)
  sfx(name, vol = 1, rate = 1, gap = 0.07, voices = 14) {
    if (!this.ctx || this.sfxVol <= 0) return;
    const now = this.ctx.currentTime;
    if (this.playing > voices) return;
    if (this.lastPlay[name] && now - this.lastPlay[name] < gap) return;
    const buf = this.buffers[name];
    if (!buf) { this.loadSfx(name); return; }
    this.lastPlay[name] = now;
    const src = this.ctx.createBufferSource(); src.buffer = buf; src.playbackRate.value = rate;
    const g = this.ctx.createGain(); g.gain.value = vol;
    src.connect(g); g.connect(this.sfxGain);
    this.playing++; src.onended = () => this.playing--;
    src.start();
  },
  // ---- original client sounds (keys from data/sounds.json: official audio lang -> effects.swf)
  SND: { ui: {}, fx: {}, chars: {}, mobs: {}, weapons: {}, vol: {} },
  key(name) { return name; },
  vol(name) { const v = this.SND.vol[name]; return v === undefined ? 1 : v / 100; },
  play(name, vol = 1, rate = 1) { if (name) this.sfx(name, vol * this.vol(name), rate); },
  hit(name, vol, rate, gap) { if (name) this.sfx(name, vol * this.vol(name), rate, gap, 20); },   // 0.84: impact sounds (Run.hitSfx)
  ui(ev, vol = 0.8) { const k = this.SND.ui[ev]; if (k) this.play(k, vol); },
  spellKeys(def) {
    if (def.snd) return [def.snd];
    for (const f of def.fx || []) { const k = this.SND.fx[f]; if (k && k.length) return k; }
    return [];
  },
  spell(def, vol = 0.55) { const k = this.spellKeys(def); if (k.length) this.play(k[0], vol, rand(0.95, 1.05)); },
  charSnd(sid, anim) { const c = this.SND.chars[sid]; return c && (c[anim] || c[anim.replace(/L$/, 'R')]) || null; },
  mobSnd(gfx, kind) { const m = this.SND.mobs[gfx]; return m && m[kind] && m[kind].length ? m[kind] : null; },
  preload(keys) { return Promise.all([...new Set(keys.filter(Boolean))].map(k => this.loadSfx(k))); },
  // UI / pickups: original sounds (no synth fallback, they load at boot)
  blip(type) {
    const map = { gem: ['gem', 0.22], coin: ['coin', 0.5], click: ['click', 0.6], level: ['level', 0.7], door: ['door', 0.8], wrong: ['error', 0.8], right: ['right', 0.8], cast: [null, 0], hurt: [null, 0] };
    if (type === 'boom') { this.play('explosion', 0.45, rand(0.9, 1.1)); return; }
    const m = map[type]; if (m) { if (m[0]) this.ui(m[0], m[1]); return; }
    this._blip(type);
  },
  // 0.38: a short victory fanfare (original, synthesized: two square + triangle voices, ta-ta-ta-taaa) for the relics
  fanfare(vol = 1) {
    if (!this.ctx || this.sfxVol <= 0) return;
    const t0 = this.ctx.currentTime + 0.02, N = [[523, 0, 0.11], [659, 0.12, 0.11], [784, 0.24, 0.11], [1046, 0.36, 0.5], [784, 0.36, 0.5], [1175, 0.9, 0.12], [1318, 1.0, 0.7], [988, 1.0, 0.7]];
    for (const [f, at, d] of N) for (const [type, k] of [['square', 0.035], ['triangle', 0.07]]) {
      const o = this.ctx.createOscillator(), g = this.ctx.createGain(); o.type = type; o.frequency.setValueAtTime(f * (type === 'square' ? 1 : 0.5), t0 + at);
      g.gain.setValueAtTime(0.0001, t0 + at); g.gain.exponentialRampToValueAtTime(k * vol, t0 + at + 0.015); g.gain.exponentialRampToValueAtTime(0.0001, t0 + at + d);
      o.connect(g); g.connect(this.sfxGain); o.start(t0 + at); o.stop(t0 + at + d + 0.03);
    }
  },
  // 0.61: a relic picked up: a rising magic chime (bells climbing a major arpeggio, a soft shimmer of high partials, a
  // warm low swell under it) — the 'something important' sound of the old console games
  relicSfx() {
    if (!this.ctx || this.sfxVol <= 0) return;
    const c = this.ctx, t0 = c.currentTime + 0.01;
    const tone = (f, at, d, type, v, f2) => { const o = c.createOscillator(), g = c.createGain(); o.type = type; o.frequency.setValueAtTime(f, t0 + at); if (f2) o.frequency.exponentialRampToValueAtTime(f2, t0 + at + d);
      g.gain.setValueAtTime(0.0001, t0 + at); g.gain.exponentialRampToValueAtTime(v, t0 + at + 0.012); g.gain.exponentialRampToValueAtTime(0.0001, t0 + at + d); o.connect(g); g.connect(this.sfxGain); o.start(t0 + at); o.stop(t0 + at + d + 0.03); };
    [784, 988, 1175, 1568, 1976, 2349].forEach((f, i) => { tone(f, i * 0.07, 0.9, 'sine', 0.075); tone(f * 2.01, i * 0.07, 0.35, 'sine', 0.02); });   // the chime
    for (let i = 0; i < 8; i++) tone(2600 + Math.random() * 1800, 0.45 + i * 0.045, 0.25, 'triangle', 0.018);   // the shimmer
    tone(196, 0.02, 1.1, 'triangle', 0.09, 392); tone(392, 0.4, 0.9, 'sine', 0.05);   // the swell
  },
  // 0.62: the kill combo (juice.js): 'tick' every 5 kills (a soft pluck climbing a pentatonic scale), 'tier' at each step
  // (a rising square / triangle chord, higher at each step, with a low hit), 'end' (a big combo broken: two soft falling
  // notes), 'record' (the profile's best combo beaten: the fanfare)
  comboSfx(kind, v = 0) {
    if (!this.ctx || this.sfxVol <= 0) return;
    const c = this.ctx, t0 = c.currentTime + 0.005;
    const tone = (f, at, d, type, vol, f2) => { const o = c.createOscillator(), g = c.createGain(); o.type = type; o.frequency.setValueAtTime(f, t0 + at); if (f2) o.frequency.exponentialRampToValueAtTime(f2, t0 + at + d);
      g.gain.setValueAtTime(0.0001, t0 + at); g.gain.exponentialRampToValueAtTime(vol, t0 + at + 0.01); g.gain.exponentialRampToValueAtTime(0.0001, t0 + at + d); o.connect(g); g.connect(this.sfxGain); o.start(t0 + at); o.stop(t0 + at + d + 0.03); };
    if (kind === 'tick') {
      if (c.currentTime - (this._ctk || 0) < 0.07) return; this._ctk = c.currentTime;
      const st = Math.floor((v - 10) / 5) % 10, f = 523.25 * Math.pow(2, ([0, 2, 4, 7, 9][st % 5] + 12 * Math.floor(st / 5)) / 12);
      tone(f, 0, 0.13, 'triangle', 0.04); tone(f * 2, 0, 0.07, 'sine', 0.014); return;
    }
    if (kind === 'tier') {
      const b = 392 * Math.pow(2, v / 6);
      [0, 4, 7, 12].forEach((s, i) => { const f = b * Math.pow(2, s / 12); tone(f, i * 0.055, 0.3 + i * 0.06, 'square', 0.02); tone(f, i * 0.055, 0.4 + i * 0.06, 'triangle', 0.045); });
      tone(130, 0, 0.35, 'sine', 0.12, 55); return;
    }
    if (kind === 'end') { tone(523, 0, 0.16, 'triangle', 0.035, 466); tone(392, 0.12, 0.3, 'triangle', 0.03, 349); return; }
    if (kind === 'record') this.fanfare(0.7);
  },
  // 0.60: a soft low heartbeat (the low-life vignette, juice.js)
  thump(vol = 0.3) {
    if (!this.ctx || this.sfxVol <= 0) return;
    const t = this.ctx.currentTime + 0.01, o = this.ctx.createOscillator(), g = this.ctx.createGain();
    o.type = 'sine'; o.frequency.setValueAtTime(95, t); o.frequency.exponentialRampToValueAtTime(42, t + 0.14);
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(vol, t + 0.012); g.gain.exponentialRampToValueAtTime(0.0001, t + 0.2);
    o.connect(g); g.connect(this.sfxGain); o.start(t); o.stop(t + 0.22);
  },
  // 0.40: the booster: a rising magic swell while the pack charges (riser), then a burst of bells and a paper tear (sparkle)
  boosterSfx(kind) {
    if (!this.ctx || this.sfxVol <= 0) return;
    const c = this.ctx, t0 = c.currentTime + 0.01;
    const tone = (f, at, d, type, v, f2) => { const o = c.createOscillator(), g = c.createGain(); o.type = type; o.frequency.setValueAtTime(f, t0 + at); if (f2) o.frequency.exponentialRampToValueAtTime(f2, t0 + at + d);
      g.gain.setValueAtTime(0.0001, t0 + at); g.gain.exponentialRampToValueAtTime(v, t0 + at + Math.min(0.05, d / 3)); g.gain.exponentialRampToValueAtTime(0.0001, t0 + at + d); o.connect(g); g.connect(this.sfxGain); o.start(t0 + at); o.stop(t0 + at + d + 0.02); };
    if (kind === 'riser') { tone(180, 0, 1.6, 'sawtooth', 0.025, 900); tone(360, 0.1, 1.5, 'triangle', 0.04, 1500); for (let i = 0; i < 10; i++) tone(700 + i * 90, 0.15 * i, 0.12, 'sine', 0.035); return; }
    const n = c.createBufferSource(), b = c.createBuffer(1, c.sampleRate * 0.35, c.sampleRate), d = b.getChannelData(0);   // the tear: a short filtered noise
    for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / d.length, 2);
    const bp = c.createBiquadFilter(), g = c.createGain(); bp.type = 'bandpass'; bp.frequency.value = 2400; g.gain.value = 0.35; n.buffer = b; n.connect(bp); bp.connect(g); g.connect(this.sfxGain); n.start(t0);
    [1568, 2093, 2637, 3136, 2349, 3520].forEach((f, i) => tone(f, 0.05 + i * 0.06, 0.6, 'sine', 0.05));   // bells
    tone(523, 0.05, 0.5, 'triangle', 0.06); tone(784, 0.05, 0.5, 'triangle', 0.05);
  },
  // 0.48: the level-up dice: a rattle in the hand (roll), each bounce on the table (clack, higher as they slow down: u
  // 0..1), the landing (a wooden thud and a chime)
  diceSfx(kind, u = 0) {
    if (!this.ctx || this.sfxVol <= 0) return;
    const c = this.ctx, t0 = c.currentTime + 0.005;
    const noise = (at, d, f, q, v) => { const n = c.createBufferSource(), b = c.createBuffer(1, Math.max(1, c.sampleRate * d | 0), c.sampleRate), x = b.getChannelData(0);
      for (let i = 0; i < x.length; i++) x[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / x.length, 3);
      const bp = c.createBiquadFilter(), g = c.createGain(); bp.type = 'bandpass'; bp.frequency.value = f; bp.Q.value = q; g.gain.value = v; n.buffer = b; n.connect(bp); bp.connect(g); g.connect(this.sfxGain); n.start(t0 + at); };
    const tone = (f, at, d, type, v, f2) => { const o = c.createOscillator(), g = c.createGain(); o.type = type; o.frequency.setValueAtTime(f, t0 + at); if (f2) o.frequency.exponentialRampToValueAtTime(f2, t0 + at + d);
      g.gain.setValueAtTime(0.0001, t0 + at); g.gain.exponentialRampToValueAtTime(v, t0 + at + 0.008); g.gain.exponentialRampToValueAtTime(0.0001, t0 + at + d); o.connect(g); g.connect(this.sfxGain); o.start(t0 + at); o.stop(t0 + at + d + 0.02); };
    if (kind === 'roll') { for (let i = 0; i < 9; i++) noise(i * 0.045 + Math.random() * 0.02, 0.05, 2600 + Math.random() * 1400, 3, 0.35); tone(110, 0, 1.0, 'sawtooth', 0.012, 220); return; }
    if (kind === 'clack') { noise(0, 0.06, 1500 + u * 1200 + Math.random() * 300, 5, 0.6); tone(700 + u * 600 + Math.random() * 80, 0, 0.05, 'triangle', 0.05); return; }
    noise(0, 0.12, 380, 2, 0.9); tone(140, 0, 0.25, 'sine', 0.18, 70);   // land: the thud...
    [988, 1319, 1976].forEach((f, i) => tone(f, 0.06 + i * 0.05, 0.5, 'sine', 0.06)); tone(659, 0.06, 0.45, 'triangle', 0.05);   // ...and the chime
  },
  // 0.53: the countdown: a short bell-like beep for 3, 2, 1 (n), a higher chord with a whoosh for GO! (n = 0)
  countdownSfx(n) {
    if (!this.ctx || this.sfxVol <= 0) return;
    const c = this.ctx, t0 = c.currentTime + 0.01;
    const tone = (f, at, d, type, v) => { const o = c.createOscillator(), g = c.createGain(); o.type = type; o.frequency.setValueAtTime(f, t0 + at);
      g.gain.setValueAtTime(0.0001, t0 + at); g.gain.exponentialRampToValueAtTime(v, t0 + at + 0.01); g.gain.exponentialRampToValueAtTime(0.0001, t0 + at + d); o.connect(g); g.connect(this.sfxGain); o.start(t0 + at); o.stop(t0 + at + d + 0.02); };
    if (n > 0) { const f = [0, 784, 698, 659][n]; tone(f, 0, 0.32, 'square', 0.05); tone(f * 2, 0, 0.25, 'sine', 0.05); tone(f / 2, 0, 0.2, 'triangle', 0.08); return; }
    [1046, 1318, 1568, 2093].forEach((f, i) => { tone(f, i * 0.02, 0.7, 'square', 0.035); tone(f, i * 0.02, 0.8, 'sine', 0.05); });
    const nz = c.createBufferSource(), b = c.createBuffer(1, c.sampleRate * 0.5, c.sampleRate), d = b.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * Math.sin(Math.PI * i / d.length);
    const bp = c.createBiquadFilter(), g = c.createGain(); bp.type = 'bandpass'; bp.frequency.setValueAtTime(600, t0); bp.frequency.exponentialRampToValueAtTime(4000, t0 + 0.45); g.gain.value = 0.25;
    nz.buffer = b; nz.connect(bp); bp.connect(g); g.connect(this.sfxGain); nz.start(t0);
    this.ui('door', 0.7);
  },
  // 0.54: a boss comes in: the client's fight gong, a deep war horn (brass chord, its pitch falling a little) and a boom
  bossSfx(final) {
    const now = performance.now(); if (now - (this._bossT || 0) < 2000) return; this._bossT = now;   // (once for a wave of bosses)
    this.ui('boss', 1);
    if (!this.ctx || this.sfxVol <= 0) return;
    const c = this.ctx, t0 = c.currentTime + 0.02, out = c.createGain(); out.gain.value = final ? 1.25 : 1; out.connect(this.sfxGain);
    const lp = c.createBiquadFilter(); lp.type = 'lowpass'; lp.frequency.setValueAtTime(500, t0); lp.frequency.linearRampToValueAtTime(1600, t0 + 0.35); lp.frequency.linearRampToValueAtTime(700, t0 + 1.6); lp.connect(out);
    for (const [f, v] of [[73.4, 0.16], [110, 0.13], [146.8, 0.1], [220, 0.05]]) for (const det of [-6, 6]) {
      const o = c.createOscillator(), g = c.createGain(); o.type = 'sawtooth'; o.detune.value = det;
      o.frequency.setValueAtTime(f, t0); o.frequency.linearRampToValueAtTime(f * 0.94, t0 + 1.6);
      g.gain.setValueAtTime(0.0001, t0); g.gain.exponentialRampToValueAtTime(v, t0 + 0.18); g.gain.setValueAtTime(v, t0 + 1.0); g.gain.exponentialRampToValueAtTime(0.0001, t0 + 1.8);
      o.connect(g); g.connect(lp); o.start(t0); o.stop(t0 + 1.85);
    }
    const nz = c.createBufferSource(), b = c.createBuffer(1, c.sampleRate * 0.9, c.sampleRate), d = b.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / d.length, 3);
    const bl = c.createBiquadFilter(), g = c.createGain(); bl.type = 'lowpass'; bl.frequency.value = 160; g.gain.value = 1.4;
    nz.buffer = b; nz.connect(bl); bl.connect(g); g.connect(out); nz.start(t0);
    const k = c.createOscillator(), kg = c.createGain(); k.type = 'sine'; k.frequency.setValueAtTime(90, t0); k.frequency.exponentialRampToValueAtTime(34, t0 + 0.5);
    kg.gain.setValueAtTime(0.6, t0); kg.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.6); k.connect(kg); kg.connect(out); k.start(t0); k.stop(t0 + 0.65);
  },
  // 0.61: the character falls (Run.juiceDeath): a deep impact (a low noise burst and a falling sub), a slow lament (a
  // minor arpeggio on soft bells over a dark string pad, in a little reverb) and two last heartbeats, the second weaker
  // 0.71: a one-off sound file (assets/audio/fx/<name>.mp3) at the effects' volume (the Goultard laugh, the death easter egg)
  fxFile(name, vol = 1) {
    try { const a = this.track(new Audio('assets/audio/fx/' + name + '.mp3?v=' + (typeof BUILD !== 'undefined' ? BUILD : ''))); a.volume = Math.max(0, Math.min(1, vol * (this.sfxVol === undefined ? 1 : this.sfxVol))); const p = a.play(); if (p) p.catch(() => { }); } catch (e) { }
  },
  deathSfx() {
    if (Math.random() < 1 / 15) { this.fxFile('death_cough', 1); return; }   // (0.71: an easter egg one death in 15)
    if (!this.ctx || this.sfxVol <= 0) return;
    const c = this.ctx, t0 = c.currentTime + 0.02, out = c.createGain(); out.gain.value = 1; out.connect(this.sfxGain);
    if (!this._rev) {   // a short reverb (made once): decaying noise as the impulse
      const n = c.sampleRate * 2.2, b = c.createBuffer(2, n, c.sampleRate);
      for (let ch = 0; ch < 2; ch++) { const d = b.getChannelData(ch); for (let i = 0; i < n; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / n, 3); }
      this._rev = b;
    }
    const rv = c.createConvolver(), rg = c.createGain(); rv.buffer = this._rev; rg.gain.value = 0.55; rv.connect(rg); rg.connect(out);
    const tone = (f, at, d, type, v, f2) => { const o = c.createOscillator(), g = c.createGain(); o.type = type; o.frequency.setValueAtTime(f, t0 + at); if (f2) o.frequency.exponentialRampToValueAtTime(f2, t0 + at + d);
      g.gain.setValueAtTime(0.0001, t0 + at); g.gain.exponentialRampToValueAtTime(v, t0 + at + Math.min(0.02, d / 4)); g.gain.exponentialRampToValueAtTime(0.0001, t0 + at + d); o.connect(g); g.connect(out); g.connect(rv); o.start(t0 + at); o.stop(t0 + at + d + 0.05); };
    // the impact
    const nz = c.createBufferSource(), b = c.createBuffer(1, c.sampleRate * 1.1, c.sampleRate), d = b.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / d.length, 4);
    const lp = c.createBiquadFilter(), ng = c.createGain(); lp.type = 'lowpass'; lp.frequency.setValueAtTime(900, t0); lp.frequency.exponentialRampToValueAtTime(90, t0 + 0.8); ng.gain.value = 1.3;
    nz.buffer = b; nz.connect(lp); lp.connect(ng); ng.connect(out); ng.connect(rv); nz.start(t0);
    tone(110, 0, 0.9, 'sine', 0.75, 28); tone(55, 0, 1.3, 'triangle', 0.3, 30);
    // the lament: A minor falling (A4 E4 C4 A3, then a low E), soft bells
    [[440, 0.45], [329.6, 0.85], [261.6, 1.25], [220, 1.65], [164.8, 2.1]].forEach(([f, at], i) => { tone(f, at, 1.6 + i * 0.2, 'sine', 0.11); tone(f * 2, at, 0.6, 'sine', 0.025); tone(f / 2, at, 1.2, 'triangle', 0.035); });
    // a dark pad under it: two detuned saws, filtered, a slow swell
    const pf = c.createBiquadFilter(); pf.type = 'lowpass'; pf.frequency.value = 650; pf.connect(out); pf.connect(rv);
    for (const [f, det] of [[110, -7], [110, 7], [130.8, -5], [164.8, 5]]) {
      const o = c.createOscillator(), g = c.createGain(); o.type = 'sawtooth'; o.detune.value = det; o.frequency.setValueAtTime(f, t0 + 0.3); o.frequency.linearRampToValueAtTime(f * 0.97, t0 + 3.6);
      g.gain.setValueAtTime(0.0001, t0 + 0.3); g.gain.exponentialRampToValueAtTime(0.022, t0 + 1.3); g.gain.setValueAtTime(0.022, t0 + 2.4); g.gain.exponentialRampToValueAtTime(0.0001, t0 + 3.8);
      o.connect(g); g.connect(pf); o.start(t0 + 0.3); o.stop(t0 + 3.9);
    }
    // two last heartbeats (lub-dub), the second weaker and later
    for (const [at, v] of [[0.7, 0.45], [1.75, 0.22]]) { tone(90, at, 0.2, 'sine', v, 40); tone(80, at + 0.17, 0.18, 'sine', v * 0.7, 38); }
  },
  // tiny synthesized blips (kept only as last-resort fallback)
  _blip(type) {
    if (!this.ctx || this.sfxVol <= 0) return;
    const now = this.ctx.currentTime;
    if (this.lastPlay['b_' + type] && now - this.lastPlay['b_' + type] < 0.045) return;
    this.lastPlay['b_' + type] = now;
    const o = this.ctx.createOscillator(), g = this.ctx.createGain();
    o.connect(g); g.connect(this.sfxGain);
    let dur = 0.08;
    const P = {
      gem: () => { o.type = 'sine'; o.frequency.setValueAtTime(880 + rand(0, 200), now); o.frequency.exponentialRampToValueAtTime(1400, now + 0.06); g.gain.setValueAtTime(0.08, now); dur = 0.07; },
      coin: () => { o.type = 'square'; o.frequency.setValueAtTime(1320, now); o.frequency.setValueAtTime(1760, now + 0.05); g.gain.setValueAtTime(0.05, now); dur = 0.12; },
      hurt: () => { o.type = 'sawtooth'; o.frequency.setValueAtTime(220, now); o.frequency.exponentialRampToValueAtTime(90, now + 0.15); g.gain.setValueAtTime(0.09, now); dur = 0.16; },
      click: () => { o.type = 'triangle'; o.frequency.setValueAtTime(660, now); g.gain.setValueAtTime(0.06, now); dur = 0.05; },
      level: () => { o.type = 'triangle'; [523, 659, 784, 1046].forEach((f, i) => o.frequency.setValueAtTime(f, now + i * 0.07)); g.gain.setValueAtTime(0.09, now); dur = 0.34; },
      cast: () => { o.type = 'sine'; o.frequency.setValueAtTime(300, now); o.frequency.exponentialRampToValueAtTime(700, now + 0.08); g.gain.setValueAtTime(0.025, now); dur = 0.09; },
      boom: () => { o.type = 'sawtooth'; o.frequency.setValueAtTime(120, now); o.frequency.exponentialRampToValueAtTime(40, now + 0.25); g.gain.setValueAtTime(0.12, now); dur = 0.3; },
      wrong: () => { o.type = 'square'; o.frequency.setValueAtTime(200, now); o.frequency.setValueAtTime(150, now + 0.12); g.gain.setValueAtTime(0.07, now); dur = 0.28; },
      right: () => { o.type = 'triangle'; [659, 880, 1175].forEach((f, i) => o.frequency.setValueAtTime(f, now + i * 0.08)); g.gain.setValueAtTime(0.09, now); dur = 0.3; },
      door: () => { o.type = 'sine'; o.frequency.setValueAtTime(200, now); o.frequency.exponentialRampToValueAtTime(800, now + 0.5); g.gain.setValueAtTime(0.08, now); dur = 0.55; },
    };
    (P[type] || P.click)();
    g.gain.exponentialRampToValueAtTime(0.0001, now + dur);
    o.start(now); o.stop(now + dur + 0.02);
  },
  // ---- music: one channel only. The background track and the class themes never overlap:
  // a theme pauses the background track, a new theme hard-stops the previous one, and starting a run stops any theme.
  // Every element carries _want; nothing (fade, blob fallback, resume) may start an element that is no longer wanted.
  // 0.55: three music styles (settings.musicStyle): 'classic' (the HD Dofus musics), 'phonk', 'lofi'. In phonk / lofi
  // the main menu plays the style's own version of its track, and every zone / fight plays the style's 5 zone tracks
  // from a shuffled bag (never the same twice in a row), one after another
  MENU_TRACKS: ['loc_incarnam', 'loc_amakna', 'loc_brakmar'],
  style() { const s = typeof Store !== 'undefined' && Store.data && Store.data.settings && Store.data.settings.musicStyle; return s === 'phonk' || s === 'lofi' ? s : 'classic'; },
  bagNext(st) {
    const b = (this._bags = this._bags || {}), last = this._bagLast && this._bagLast[st];
    if (!b[st] || !b[st].length) { b[st] = shuffle([1, 2, 3, 4, 5]); if (b[st][b[st].length - 1] === last) b[st].reverse(); }
    const n = b[st].pop(); (this._bagLast = this._bagLast || {})[st] = n; return `${st}/${st}${n}`;
  },
  playMusic(name, fade = 1.0, o = {}) {
    this.stopJingle(0, true);
    this._ducked = false;
    this.wantMusic = true;
    const st = this.style(), key = st + ':' + name + (o.menu ? ':m' : '');
    this._req = { name, menu: !!o.menu };
    if (this.musicName === key && this.music) { this._start(this.music, this.musicVol, 0.4); return; }
    const old = this.music;
    if (old) this._stop(old, 0.5);
    this.musicName = key;
    const bag = st !== 'classic' && !(o.menu && this.MENU_TRACKS.includes(name));
    const file = st === 'classic' ? name : bag ? this.bagNext(st) : `${st}/${name}`;
    const a = this.mediaEl(`assets/audio/music/${file}.mp3`);
    a.loop = !bag; a._role = 'music';
    if (bag) a.addEventListener('ended', () => { if (this.music === a && this.musicName === key) { this.musicName = null; this.playMusic(name, 0.3, o); } });
    this.music = a;
    this._start(a, this.musicVol, fade);
  },
  setStyle(st) {   // (switching live: the current request is played again in the new style)
    Store.data.settings.musicStyle = st; Store.save();
    if (this._req && this.wantMusic) { this.musicName = null; this.playMusic(this._req.name, 0.6, { menu: this._req.menu }); }
  },
  stopMusic(sec = 0.2) { this.stopJingle(0, true); this.wantMusic = false; if (this.music) this._stop(this.music, sec); this.music = null; this.musicName = null; },   // (0.61: sec = a longer fade, the character's death)
  _start(a, vol, fade) {
    a._want = true;
    a._fadeTok = (a._fadeTok || 0) + 1;
    if (a.paused && !this.halted) { a.volume = 0; const p = a.play(); if (p) p.catch(() => { }); }
    this.fadeEl(a, vol, fade);
  },
  _stop(a, sec = 0) {
    if (!a) return;
    a._want = false;
    if (sec <= 0) { a._fadeTok = (a._fadeTok || 0) + 1; a.pause(); return; }
    this.fadeEl(a, 0, sec, () => { if (!a._want) a.pause(); });
  },
  // fade an element's volume to `to` over `sec`; one fade per element at a time
  fadeEl(a, to, sec, done) {
    if (!a) return;
    const from = a.volume, t0 = performance.now(), tok = (a._fadeTok = (a._fadeTok || 0) + 1);
    if (!sec) { a.volume = Math.max(0, Math.min(1, to)); if (done) done(); return; }
    const step = () => {
      if (a._fadeTok !== tok) return;
      const k = Math.min(1, (performance.now() - t0) / (sec * 1000));
      a.volume = Math.max(0, Math.min(1, from + (to - from) * k));
      if (k < 1) requestAnimationFrame(step); else if (done) done();
    };
    step();
  },
  // class themes: the background music pauses while one plays, then comes back
  // (0.92: o.fx = a clip of assets/audio/fx at the effects' volume, the profile names' easter eggs, UI.nameEgg)
  jingle(name, o = {}) {
    this.stopJingle(0, true);
    let a;
    try { a = this.mediaEl(o.fx ? `assets/audio/fx/${name}.mp3?v=${typeof BUILD !== 'undefined' ? BUILD : ''}` : `assets/audio/music/${name}.mp3`); } catch (e) { return null; }
    a.loop = false; a._role = 'jingle';
    this._jingle = a;
    if (this.music && !this._ducked) { this._ducked = true; this._stop(this.music, 0.15); }
    this._ducked = true;
    const end = () => { if (this._jingle === a) { this._jingle = null; a._want = false; this.unduck(); } };
    a.addEventListener('ended', end);
    a._want = true; a.volume = Math.max(0, Math.min(1, o.fx ? this.sfxVol : this.musicVol * 0.9)); a._fx = !!o.fx;
    if (this.halted) return a; const p = a.play(); if (p) p.catch(() => { /* the blob fallback retries while still wanted */ });
    return a;
  },
  stopJingle(sec = 0.25, keepDucked = false) {
    const j = this._jingle;
    if (j) { this._jingle = null; this._stop(j, sec); }
    if (!keepDucked) this.unduck();
  },
  unduck() {
    if (!this._ducked) return;
    this._ducked = false;
    if (this.music && this.wantMusic) this._start(this.music, this.musicVol, 1.2);
  },
  // media element with a blob: fallback for sandboxes that refuse direct media loads
  mediaEl(url) {
    const a = this.track(new Audio()); a.preload = 'auto'; a._want = false;
    let triedBlob = false;
    a.addEventListener('error', () => {
      if (triedBlob) return; triedBlob = true;
      fetch(url).then(r => r.blob()).then(b => {
        a.src = URL.createObjectURL(b);
        if (a._want && !this.halted && !(a._role === 'music' && this._ducked)) { const p = a.play(); if (p) p.catch(() => { }); }
      }).catch(() => { });
    });
    // never let an unwanted element make noise (late loads, autoplay retries)
    a.addEventListener('playing', () => { if (!a._want || this.halted) a.pause(); });
    a.src = url;
    return a;
  },
};

