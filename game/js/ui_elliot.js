'use strict';
// ---------------------------------------------------------------- 0.99: an easter egg at launch, "Bonsoir Elliot"
// Once the profile has won 5 runs, one launch in ELLIOT_ODDS plays assets/audio/fx/bonsoir_elliot.mp3 at full volume
// (whatever the sound settings), the whole page glitching while it plays (colours split, jitter, scanlines, torn bars),
// then a fade to black and back to the game as it was. A browser that blocks sound before the first click / key: the
// egg waits for it. ?elliot=1 forces it (tests). Called by Game.boot once the main menu is up.
const ELLIOT_ODDS = 20;
Object.assign(UI, {
  elliotEgg(force) {
    const st = (Store.data && Store.data.st) || {};
    if (!force && !((st.wins || 0) >= 5 && Math.random() < 1 / ELLIOT_ODDS)) return false;
    const a = new Audio('assets/audio/fx/bonsoir_elliot.mp3?v=' + (typeof BUILD !== 'undefined' ? BUILD : '')); a.volume = 1;
    if (Audio2.track) Audio2.track(a);
    let started = false;
    const go = () => {
      if (started) return; started = true; off();
      const S = Store.data.settings; Audio2.setVolumes(0, S.sfx);   // (the menu's music silent while it plays)
      const root = document.documentElement, ov = h('div', { id: 'elliot' }, h('i', { class: 'el-scan' }));
      document.body.append(ov); root.classList.add('elliot');
      const bars = setInterval(() => {   // torn bars: a few slices of colour that jump about
        for (const b of ov.querySelectorAll('.el-bar')) b.remove();
        for (let i = 0, n = 1 + Math.floor(Math.random() * 4); i < n; i++) {
          const y = Math.random() * 100, hh = 0.6 + Math.random() * 5;
          ov.append(h('i', { class: 'el-bar', style: { top: y + '%', height: hh + '%', left: (Math.random() * 30 - 15) + '%', background: pick(['rgba(255,0,80,.35)', 'rgba(0,255,230,.3)', 'rgba(255,255,255,.22)', 'rgba(0,0,0,.5)']) } }));
        }
        root.style.setProperty('--el-x', (Math.random() * 8 - 4).toFixed(1) + 'px'); root.style.setProperty('--el-h', Math.floor(Math.random() * 360) + 'deg');
      }, 90);
      let done = false;
      const end = () => {
        if (done) return; done = true; clearInterval(bars); clearTimeout(safety);
        const black = h('div', { id: 'elliot-black' }); document.body.append(black);
        requestAnimationFrame(() => black.classList.add('on'));
        setTimeout(() => {   // under the black: the glitch gone, the music back; then the black fades away
          root.classList.remove('elliot'); root.style.removeProperty('--el-x'); root.style.removeProperty('--el-h'); ov.remove();
          Audio2.setVolumes(S.musicOff ? 0 : S.music, S.sfx); black.classList.remove('on'); setTimeout(() => black.remove(), 1300);
        }, 900);
      };
      a.addEventListener('ended', end);
      const safety = setTimeout(end, 60000);   // (a sound that never ends: never a game stuck glitching)
    };
    const play = () => { if (started) return; const p = a.play(); if (p && p.then) p.then(go).catch(() => { }); else go(); };   // (go once it really plays)
    const off = () => { removeEventListener('pointerdown', play, true); removeEventListener('keydown', play, true); };
    addEventListener('pointerdown', play, true); addEventListener('keydown', play, true);   // (autoplay refused: the first click / key starts it)
    play();
    return true;
  },
});
