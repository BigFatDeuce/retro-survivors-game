'use strict';
// ---------------------------------------------------------------- 0.99: the game's own mouse cursor, a little animated
// A teal arrowhead with a notch at its foot (white-cyan face, teal side, dark outline) drawn as an SVG at 32 px, crisp at any scale; a light glint
// sweeps across it now and then and its edge breathes. The frames are made once as data URIs; one of them is set as the
// cursor of the whole page (html.gcur, CSS var --gcur, over the buttons' hand too) every 90 ms. No timer while the page is
// hidden; on a touch device the cursor does not show anyway.
const GameCursor = {
  N: 16, HOT: [3, 2],
  frames: null, i: 0, t: 0,
  frame(k) {   // k in [0, 1): the glint's place (it shows in the first half), the edge's light
    const g = k < 0.5 ? k / 0.5 : -1, gx = -6 + g * 34, edge = 0.55 + 0.45 * Math.sin(k * Math.PI * 2);
    const arrow = 'M3 2 L3 28.5 L9.5 22 L22 21.5 Z';   // (the picture's arrowhead: a vertical left edge, a notch at its foot)
    const svg = `<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32' viewBox='0 0 32 32'>
<defs><linearGradient id='r' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='#39c9d6'/><stop offset='0.6' stop-color='#16a2ae'/><stop offset='1' stop-color='#0a6f79'/></linearGradient>
<linearGradient id='g' x1='0' y1='0' x2='1' y2='0'><stop offset='0' stop-color='#fff' stop-opacity='0'/><stop offset='0.5' stop-color='#fff' stop-opacity='0.95'/><stop offset='1' stop-color='#fff' stop-opacity='0'/></linearGradient>
<clipPath id='c'><path d='${arrow}'/></clipPath></defs>
<path d='${arrow}' fill='#ecfdff'/>
<path d='M4.5 4 L22 21.5 L13 21.8 L9 13 Z' fill='url(#r)'/>
<path d='M9.5 22 L22 21.5' stroke='#075d66' stroke-width='1.4'/><path d='M3.6 27.6 L9.5 22' stroke='#0e7f89' stroke-width='1.6' opacity='0.8'/>
${g >= 0 ? `<g clip-path='url(#c)'><rect x='${gx.toFixed(1)}' y='-6' width='6' height='44' fill='url(#g)' transform='rotate(30 16 16)'/></g>` : ''}
<path d='${arrow}' fill='none' stroke='#1d2a2c' stroke-width='1.8' stroke-linejoin='round'/>
<path d='M4.4 5.2 L4.4 25' stroke='#7ff6ff' stroke-width='0.9' stroke-linecap='round' opacity='${(0.3 + 0.6 * edge).toFixed(2)}'/>
</svg>`;
    return `url("data:image/svg+xml,${encodeURIComponent(svg)}") ${this.HOT[0]} ${this.HOT[1]}, auto`;
  },
  start() {
    if (this.frames || !document.documentElement) return;
    this.frames = [...Array(this.N)].map((_, i) => this.frame(i / this.N));
    const root = document.documentElement; root.classList.add('gcur'); root.style.setProperty('--gcur', this.frames[0]);
    if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) return;   // (reduced motion: the still arrow)
    setInterval(() => { if (document.hidden) return; this.i = (this.i + 1) % this.N; root.style.setProperty('--gcur', this.frames[this.i]); }, 90);
  },
};
GameCursor.start();
