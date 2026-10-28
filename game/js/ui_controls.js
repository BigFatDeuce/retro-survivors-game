'use strict';
// ---------------------------------------------------------------- the Commandes screen. 0.68 (the layout of his
// mock-up — keyboard, controller, mouse, phone — redrawn in the Dofus Retro spirit, no cut-out pictures, no ornaments):
// every device drawn here as vectors (sharp at any size). The keyboard sits in a carved wooden frame with leaves on its
// corners, its keys in relief (only the keys the game uses are named, coloured by what they do; AZERTY / QWERTY switch on
// the left); the controller and the mouse are olive green with leafy camouflage and a golden Dofus spiral where a brand
// would be; the phone is held sideways with a real screenshot of the game (assets/ui/ctl_phone.webp) and the gestures.
const CTL_ACT = {   // action -> colour, label key
  move: ['#4caf50', 'ctl_move'], dash: ['#f08c1e', 'ctl_dash'], spells: ['#9b59d0', 'ctl_movespells'], pause: ['#d64545', 'ctl_pause'],
  levelup: ['#3d8ee0', 'ctl_levelup'], reroll: ['#d9a400', 'ctl_reroll'], menus: ['#2a9d8f', 'ctl_menus'], full: ['#8a7a66', 'ctl_fullscreen'],
  auto: ['#c0662b', 'ctl_auto'],   // 0.34: the bread / kamas auto-choice
};
// physical keys (event.code, width in key units); the game reads codes, so the AZERTY / QWERTY switch only renames
const KB_ROWS = [
  [['Escape', 1.5], ...[...Array(12)].map((_, i) => ['F' + (i + 1), 1]), ['Eject', 1]],
  [['Backquote', 1], ...[...Array(10)].map((_, i) => ['Digit' + ((i + 1) % 10), 1]), ['Minus', 1], ['Equal', 1], ['Backspace', 1.5]],
  [['Tab', 1.5], ...'QWERTYUIOP'.split('').map(c => ['Key' + c, 1]), ['BracketLeft', 1], ['BracketRight', 1], ['Backslash', 1]],
  [['CapsLock', 1.75], ...'ASDFGHJKL'.split('').map(c => ['Key' + c, 1]), ['Semicolon', 1], ['Quote', 1], ['Enter', 1.75]],
  [['ShiftLeft', 2.25], ...'ZXCVBNM'.split('').map(c => ['Key' + c, 1]), ['Comma', 1], ['Period', 1], ['Slash', 1], ['ShiftRight', 2.25]],
  [['Fn', 1], ['ControlLeft', 1], ['AltLeft', 1], ['MetaLeft', 1.25], ['Space', 5], ['MetaRight', 1.25], ['AltRight', 1], ['ArrowLeft', 1], ['ArrowUD', 1], ['ArrowRight', 1]],
];
const KB_USE = { KeyW: 'move', KeyA: 'move', KeyS: 'move', KeyD: 'move', ArrowLeft: 'move', ArrowUp: 'move', ArrowDown: 'move', ArrowRight: 'move',
  Space: 'dash', KeyE: 'dash', KeyQ: 'spells', Escape: 'pause', KeyP: 'pause', KeyR: 'auto', KeyF: 'full', Enter: 'menus' };   // (R: auto-choice in a run, reroll on the level-up screen)
const KB_AZ = { KeyQ: 'A', KeyW: 'Z', KeyA: 'Q', KeyZ: 'W' };
const cap = s => s.charAt(0).toUpperCase() + s.slice(1);
function kbLabel(code, az) {
  if (code === 'Space') return T('ctl_space'); if (code === 'Escape') return T('ctl_esc'); if (code === 'Enter') return T('ctl_enter') + ' ↵';
  if (code.startsWith('Digit')) return code.slice(5); if (code.startsWith('Key')) return (az && KB_AZ[code]) || code.slice(3);
  return { ArrowLeft: '◀', ArrowRight: '▶', ArrowUp: '▲', ArrowDown: '▼' }[code] || '';
}
// a darker shade of a #rrggbb colour (the keys' and buttons' sides)
function ctlShade(c, k) { const n = parseInt(c.slice(1), 16), f = v => Math.round(v * k).toString(16).padStart(2, '0'); return '#' + f(n >> 16) + f((n >> 8) & 255) + f(n & 255); }
// the Dofus spiral (the egg's swirl): a golden disc with a dark spiral
function ctlSpiral(x, y, r) {
  return `<circle cx="${x}" cy="${y}" r="${r}" fill="#e2b53c" stroke="#3a2408" stroke-width="${r * 0.12}"/><circle cx="${x - r * 0.25}" cy="${y - r * 0.3}" r="${r * 0.45}" fill="#fff6c8" opacity=".35"/>
    <path d="M${x} ${y} m0 0 a${r * 0.12} ${r * 0.12} 0 1 1 ${r * 0.24} 0 a${r * 0.24} ${r * 0.24} 0 1 1 ${-r * 0.48} 0 a${r * 0.36} ${r * 0.36} 0 1 1 ${r * 0.72} 0 a${r * 0.5} ${r * 0.5} 0 1 1 ${-r * 0.98} 0" fill="none" stroke="#4a2c08" stroke-width="${r * 0.13}" stroke-linecap="round"/>`;
}
// a leaf (drawn pointing right from its stem at 0,0), for the frame's corners and the camouflage
const ctlLeaf = (x, y, r, s, c, o = 1) => `<g transform="translate(${x} ${y}) rotate(${r}) scale(${s})" opacity="${o}"><path d="M0 0 C 22 -30 70 -32 96 -4 C 70 24 22 26 0 0 Z" fill="${c}" stroke="#16300c" stroke-width="5" stroke-linejoin="round"/><path d="M6 0 Q 50 -4 88 -3" stroke="#16300c" stroke-width="3" fill="none" opacity=".55"/></g>`;
function kbSvg(az) {
  const U = 64, G = 6, rowH = [40, 60, 60, 60, 60, 60], M = 40, W0 = 14.5 * U + 2 * 18; let y = 18, out = '';
  const key = (x, y, w, hh, code) => {
    const a = KB_USE[code], c = a ? CTL_ACT[a][0] : '#efe4c8', side = a ? ctlShade(c, 0.62) : '#b29c72', lab = a ? kbLabel(code, az) : '';
    out += `<g class="key${a ? ' on' : ''}"><rect x="${x}" y="${y}" width="${w}" height="${hh}" rx="10" style="fill:${side};stroke:#2a1a0a;stroke-width:2.5"/>`
      + `<rect x="${x + 3}" y="${y + 2}" width="${w - 6}" height="${hh - 10}" rx="8" style="fill:${c};stroke:none"/><rect x="${x + 7}" y="${y + 5}" width="${w - 14}" height="${Math.max(4, (hh - 10) * 0.32)}" rx="5" style="fill:#fff;stroke:none;filter:none" opacity="${a ? 0.22 : 0.45}"/>`;
    if (lab) out += `<text x="${x + w / 2}" y="${y + (hh - 10) / 2 + (lab.length > 2 ? 7 : 10)}" class="${lab.length > 2 ? 'sm' : ''}">${lab}</text>`;
    out += '</g>';
  };
  KB_ROWS.forEach((row, r) => {
    let x = 18; const hh = rowH[r] - G;
    for (const [code, w] of row) {
      const ww = w * U - G;
      if (code === 'ArrowUD') { key(x, y, ww, hh / 2 - 2, 'ArrowUp'); key(x, y + hh / 2 + 2, ww, hh / 2 - 2, 'ArrowDown'); }
      else if (code.startsWith('Arrow')) key(x, y + hh / 2 + 2, ww, hh / 2 - 2, code);
      else key(x, y, ww, hh, code);
      x += w * U;
    }
    y += rowH[r];
  });
  const H0 = y + 14, grain = [0.18, 0.42, 0.66, 0.88].map(f => `<path d="M30 ${H0 * f} C ${W0 * 0.3} ${H0 * f - 8} ${W0 * 0.6} ${H0 * f + 10} ${W0 - 30} ${H0 * f - 2}" stroke="#2e1c0c" stroke-width="2" fill="none" opacity=".22"/>`).join('');
  const leaves = [ctlLeaf(-8, 30, 200, 0.62, '#5aa83a'), ctlLeaf(-4, 36, 150, 0.5, '#3f8a2a'), ctlLeaf(W0 + 8, 30, -20, 0.62, '#5aa83a'), ctlLeaf(W0 + 4, 38, 30, 0.5, '#3f8a2a'),
    ctlLeaf(-6, H0 - 26, 160, 0.55, '#3f8a2a'), ctlLeaf(W0 + 6, H0 - 24, 20, 0.55, '#5aa83a')].join('');
  return `<svg viewBox="${-M} ${-M * 0.6} ${W0 + 2 * M} ${H0 + M * 1.2}" class="kb"><defs><linearGradient id="kbW" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#9a6c3c"/><stop offset=".5" stop-color="#77502c"/><stop offset="1" stop-color="#5a3a1e"/></linearGradient></defs>
    <rect x="3" y="9" width="${W0 - 6}" height="${H0 - 4}" rx="24" fill="#1c1006" opacity=".45"/>
    <rect x="3" y="3" width="${W0 - 6}" height="${H0 - 6}" rx="24" fill="url(#kbW)" stroke="#24150a" stroke-width="5"/>${grain}
    <rect x="11" y="11" width="${W0 - 22}" height="${H0 - 22}" rx="18" fill="#3a2614" opacity=".55"/>
    ${[[16, 16], [W0 - 16, 16], [16, H0 - 16], [W0 - 16, H0 - 16]].map(([cx, cy]) => `<circle cx="${cx}" cy="${cy}" r="5" fill="#d8c39a" stroke="#2a1a0a" stroke-width="2"/>`).join('')}
    ${leaves}${out}</svg>`;
}
// the controller: a two-stick pad, olive green with leafy camouflage, the parts coloured by what they do
function padSvg() {
  const c = a => CTL_ACT[a][0], sh = { l: T('ctl_sh_spells'), r: T('ctl_sh_dash') };
  const lab = (x, y, t, a, anc) => `<text x="${x}" y="${y}" class="tl" text-anchor="${anc}" style="fill:${c(a)}">${t}</text>`;
  const BODY = 'M300 150 Q420 132 500 134 Q580 132 700 150 Q850 160 900 250 Q975 400 985 590 Q992 690 925 715 Q860 735 800 660 L735 580 Q705 548 655 548 L345 548 Q295 548 265 580 L200 660 Q140 735 75 715 Q8 690 15 590 Q25 400 100 250 Q150 160 300 150 Z';
  const stick = (x, y, ring) => `<circle cx="${x}" cy="${y}" r="80" fill="#1e2414" stroke="#0e1208" stroke-width="5"/><circle cx="${x}" cy="${y + 6}" r="58" fill="#000" opacity=".35"/>
    ${ring ? `<circle cx="${x}" cy="${y}" r="66" fill="none" stroke="${ring}" stroke-width="9"/>` : ''}<circle cx="${x}" cy="${y}" r="54" fill="#2c2c28" stroke="#0e0e0c" stroke-width="4"/>
    <circle cx="${x}" cy="${y}" r="38" fill="#3c3c36"/><circle cx="${x - 14}" cy="${y - 16}" r="16" fill="#fff" opacity=".12"/>`;
  const face = (x, y, l, col) => `<circle cx="${x}" cy="${y + 5}" r="34" fill="#000" opacity=".35"/><circle cx="${x}" cy="${y}" r="33" fill="#24241f" stroke="#0e0e0c" stroke-width="4"/>
    <ellipse cx="${x - 8}" cy="${y - 13}" rx="15" ry="8" fill="#fff" opacity=".14"/><text x="${x}" y="${y + 13}" class="w" style="fill:${col}">${l}</text>`;
  const camo = [[160, 330, 30, 1.1, '#6f8445'], [250, 470, -40, 0.9, '#2b3720'], [420, 200, 10, 0.8, '#6f8445'], [610, 190, 160, 0.85, '#2b3720'], [800, 330, 140, 1.1, '#6f8445'],
    [880, 520, 200, 1.0, '#2b3720'], [120, 560, -20, 1.0, '#2b3720'], [700, 480, 60, 0.7, '#6f8445'], [470, 500, -10, 0.8, '#2b3720'], [70, 650, 30, 0.9, '#6f8445'], [930, 640, 150, 0.9, '#6f8445']]
    .map(([x, y, r, s, col]) => ctlLeaf(x, y, r, s, col, 0.55)).join('');
  return `<svg viewBox="0 0 1000 820" class="pad">
  <defs>
    <linearGradient id="pBody" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#5e7040"/><stop offset=".55" stop-color="#46552e"/><stop offset="1" stop-color="#323d20"/></linearGradient>
    <linearGradient id="pTrig" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".35"/><stop offset="1" stop-color="#000" stop-opacity=".25"/></linearGradient>
    <clipPath id="pClip"><path d="${BODY}"/></clipPath>
  </defs>
  ${lab(70, 40, 'LT / LB · ' + sh.l, 'spells', 'start')}${lab(930, 40, 'RT / RB · ' + sh.r, 'dash', 'end')}
  <g transform="translate(0 60)">
  <path d="M190 120 Q200 62 265 58 L330 58 Q352 60 356 84 L360 132 Z" fill="${c('spells')}" stroke="#14180c" stroke-width="5"/><path d="M190 120 Q200 62 265 58 L330 58 Q352 60 356 84 L360 132 Z" fill="url(#pTrig)"/>
  <path d="M810 120 Q800 62 735 58 L670 58 Q648 60 644 84 L640 132 Z" fill="${c('dash')}" stroke="#14180c" stroke-width="5"/><path d="M810 120 Q800 62 735 58 L670 58 Q648 60 644 84 L640 132 Z" fill="url(#pTrig)"/>
  <path d="M150 196 Q178 128 300 122 L372 122 Q392 126 396 150 L398 170 Z" fill="${ctlShade(c('spells'), 0.8)}" stroke="#14180c" stroke-width="5"/>
  <path d="M850 196 Q822 128 700 122 L628 122 Q608 126 604 150 L602 170 Z" fill="${ctlShade(c('dash'), 0.8)}" stroke="#14180c" stroke-width="5"/>
  <path d="${BODY}" fill="#0c0e06" opacity=".35" transform="translate(0 14)"/>
  <path d="${BODY}" fill="url(#pBody)" stroke="#12160a" stroke-width="7"/>
  <g clip-path="url(#pClip)">${camo}</g>
  <path d="M120 270 Q170 185 300 172 Q420 160 500 160 Q580 160 700 172 Q830 185 880 270" fill="none" stroke="#e8f0c8" stroke-width="6" opacity=".22"/>
  ${ctlSpiral(500, 236, 34)}
  <rect x="404" y="290" width="46" height="30" rx="15" fill="#24241f" stroke="#0e0e0c" stroke-width="3.5"/><text x="427" y="313" class="w s" style="fill:${c('full')}">⧉</text>
  <rect x="550" y="290" width="46" height="30" rx="15" fill="#24241f" stroke="#0e0e0c" stroke-width="3.5"/><text x="573" y="313" class="w s" style="fill:${c('pause')}">≡</text>
  ${stick(255, 300, c('move'))}
  ${stick(640, 440, null)}
  <circle cx="362" cy="440" r="80" fill="#1e2414" stroke="#0e1208" stroke-width="5"/>
  <path d="M340 382 h44 v36 h36 v44 h-36 v36 h-44 v-36 h-36 v-44 h36 z" fill="#2c2c28" stroke="${c('move')}" stroke-width="6" stroke-linejoin="round"/>
  <path d="M340 382 h44 v36 h36 v10 h-116 v-10 h36 z" fill="#fff" opacity=".12"/>
  ${face(760, 230, 'Y', c('auto'))}${face(694, 296, 'X', '#5a8ae0')}${face(826, 296, 'B', c('menus'))}${face(760, 362, 'A', c('levelup'))}
  </g></svg>`;
}
// the mouse: left button held = the character walks towards the cursor; a click on the HUD icons switches them
function mouseSvg() {
  const c = a => CTL_ACT[a][0], B = 'M110 18 Q196 18 200 120 L200 230 Q200 322 110 322 Q20 322 20 230 L20 120 Q24 18 110 18 Z';
  const camo = [[40, 200, -30, 0.5, '#6f8445'], [150, 250, 150, 0.45, '#2b3720'], [70, 290, 10, 0.4, '#2b3720'], [180, 180, 200, 0.4, '#6f8445']].map(([x, y, r, s, col]) => ctlLeaf(x, y, r, s, col, 0.55)).join('');
  return `<svg viewBox="0 0 220 340" class="mouse"><defs><linearGradient id="mBody" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#5e7040"/><stop offset="1" stop-color="#2e3a1e"/></linearGradient><clipPath id="mClip"><path d="${B}"/></clipPath></defs>
  <path d="${B}" fill="#0c0e06" opacity=".35" transform="translate(4 8)"/>
  <path d="${B}" fill="url(#mBody)" stroke="#12160a" stroke-width="6"/>
  <g clip-path="url(#mClip)">${camo}<path d="M20 170 Q60 200 30 300 L10 300 L10 170 Z" fill="#d8c8a0" opacity=".85"/></g>
  <path d="M110 22 Q30 26 26 120 L26 150 L106 150 L106 22 Z" fill="${c('move')}" stroke="#12160a" stroke-width="4"/><path d="M110 26 Q40 30 32 100 L104 100 Z" fill="#fff" opacity=".18"/>
  <path d="M114 22 Q190 26 194 120 L194 150 L114 150 L114 22 Z" fill="#3a4728" stroke="#12160a" stroke-width="4"/>
  <rect x="100" y="56" width="20" height="50" rx="10" fill="#1e2414" stroke="#0e1208" stroke-width="3"/><rect x="104" y="64" width="12" height="20" rx="6" fill="${c('move')}"/>
  ${ctlSpiral(110, 235, 26)}
  </svg>`;
}
// the phone held sideways, a real screenshot of the game on it, the gestures drawn over it
function phoneHtml() {
  const c = a => CTL_ACT[a][0], v = (typeof BUILD !== 'undefined' ? '?v=' + BUILD : '');
  return `<div class="phone-land"><div class="pl-scr"><img src="assets/ui/ctl_phone.webp${v}" alt="">
    <svg viewBox="0 0 1720 924" class="pl-over" preserveAspectRatio="xMidYMid slice">
      <circle cx="290" cy="690" r="150" fill="rgba(255,255,255,.16)" stroke="#fff" stroke-width="6" opacity=".9"/><circle cx="290" cy="690" r="150" fill="none" stroke="${c('move')}" stroke-width="10" stroke-dasharray="26 16"/>
      <circle cx="345" cy="640" r="62" fill="${c('move')}" stroke="#fff" stroke-width="6"/>
      <path d="M352 700 q34 72 18 160 l-72 0 q-10 -52 -34 -88 q-10 -24 14 -28 q18 0 28 16 l0 -88 q0 -24 23 -24 q23 0 23 24 z" fill="#ffe0c0" stroke="#5a3a20" stroke-width="7"/>
      <circle cx="1150" cy="520" r="34" fill="${c('dash')}" stroke="#fff" stroke-width="5"/><circle cx="1150" cy="520" r="66" fill="none" stroke="${c('dash')}" stroke-width="8"/><circle cx="1150" cy="520" r="98" fill="none" stroke="${c('dash')}" stroke-width="6" opacity=".55"/>
      <path d="M1100 500 L 900 470" stroke="${c('dash')}" stroke-width="8" stroke-linecap="round" stroke-dasharray="4 18"/>
    </svg></div></div>`;
}
Object.assign(UI, {
  controls(tab) {
    this.clear(); document.body.classList.add('menu-bg'); this.screen = 'controls';
    let az = Input.layout ? Input.layout === 'azerty' : LANG === 'fr';
    const k = (...keys) => h('span', { class: 'keys' }, ...keys.map(x => x === '/' ? h('i', {}, T('ctl_or')) : h('kbd', {}, x)));
    const txt = t => h('span', { class: 'ctl-txt' }, t);
    const leg = (a, ...v) => h('div', { class: 'ctl-leg' }, h('b', { style: { '--c': CTL_ACT[a][0] } }, cap(T(CTL_ACT[a][1]))), h('span', { class: 'ctl-val' }, ...v));
    const art = (html, cls) => { const d = h('div', { class: 'ctl-dev' + (cls ? ' ' + cls : '') }); d.innerHTML = html; return d; };
    const body = h('div', { class: 'ctl-body' }), tabs = h('div', { class: 'tabs' });
    const mv = () => az ? ['Z', 'Q', 'S', 'D'] : ['W', 'A', 'S', 'D'];
    const PANES = {
      kb: () => {
        const dev = art(kbSvg(az)), legend = h('div', { class: 'ctl-legend two' });
        const fill = () => { legend.innerHTML = ''; legend.append(
          leg('move', k(...mv()), k('/'), k('▲', '◀', '▼', '▶'), txt(' · ' + T('ctl_mouse'))), leg('dash', k(T('ctl_space'), '/', 'E')), leg('spells', k(az ? 'A' : 'Q'), txt(' · ' + T('ctl_clickicon'))),
          leg('pause', k(T('ctl_esc'), '/', 'P')), leg('levelup', k('▲', '◀', '▼', '▶'), txt(' · '), k(T('ctl_enter'))), leg('auto', k('R'), txt(' · ' + T('ctl_clickicon'))),
          leg('full', k('F')), leg('menus', k(...mv()), k('/'), k('▲', '▼'), txt(' · '), k(T('ctl_enter')), txt(' · ' + T('ctl_back') + ' '), k(az ? 'A' : 'Q', '/', T('ctl_esc')))); };
        const sw = h('div', { class: 'ctl-switch' }, ...['AZERTY', 'QWERTY'].map(n => { const b = btn(n, () => { az = n === 'AZERTY'; Input.layout = az ? 'azerty' : 'qwerty'; dev.innerHTML = kbSvg(az); fill(); sw.querySelectorAll('.btn').forEach(e => e.classList.toggle('active', e === b)); }, (n === 'AZERTY') === az ? 'active' : ''); return b; }));
        fill(); body.append(h('div', { class: 'ctl-kbrow' }, sw, dev, art(mouseSvg(), 'ctl-mouse')), legend);
      },
      pad: () => body.append(h('div', { class: 'ctl-side' }, art(padSvg()), h('div', { class: 'ctl-legend' },
        leg('move', txt(T('ctl_lstick')), k('/'), txt(T('ctl_dpad'))), leg('dash', k('RB', '/', 'RT')), leg('spells', k('LB', '/', 'LT')), leg('pause', k('Menu ≡')),
        leg('levelup', k('A')), leg('auto', k('Y'), txt(' (' + T('ctl_inrun') + ')')), leg('menus', k('A'), txt(' · ' + T('ctl_back') + ' '), k('B'), txt(' · ' + T('ctl_tabs') + ' '), k('LB', 'RB')), leg('full', k('View ⧉'))))),
      touch: () => body.append(h('div', { class: 'ctl-side phone' }, art(phoneHtml()), h('div', { class: 'ctl-legend' },
        leg('move', txt(T('ctl_drag'))), leg('dash', txt(T('ctl_dtap'))), leg('spells', txt(T('ctl_icon'))), leg('pause', txt(T('ctl_pausebtn'))), leg('levelup', txt(T('ctl_card'))), leg('auto', txt(T('ctl_autotap')))))),
    };
    const go = (t) => { tab = t; body.innerHTML = ''; PANES[t](); tabs.querySelectorAll('.btn').forEach(b => b.classList.toggle('active', b.dataset.k === t)); };
    for (const [key, name] of [['kb', T('ctl_kb')], ['pad', T('ctl_pad')], ['touch', T('ctl_touch')]]) { const b = btn(name, () => go(key)); b.dataset.k = key; tabs.append(b); }
    this.rootEl.append(h('div', { class: 'screen controls-screen' }, this.panel(T('ctl_title'), tabs, body, h('div', { class: 'start-row' }, btn(T('back'), () => this.mainMenu())))));
    const touch = matchMedia('(pointer: coarse)').matches;
    go(tab || (Nav.enabled ? 'pad' : touch ? 'touch' : 'kb'));
  },
});
