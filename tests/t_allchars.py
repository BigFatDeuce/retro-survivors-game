url('')
time.sleep(5)
pg.evaluate("""(async () => {
  const C = Game.C; const cv = document.createElement('canvas'); cv.width = 2400; cv.height = 1100; cv.id = 'allc';
  cv.style.cssText = 'position:fixed;left:0;top:0;z-index:9999;background:#7a9a6a'; document.body.append(cv);
  const g = cv.getContext('2d'); let i = 0;
  const hats = C.hats.map(h => h.id), capes = C.capes.map(c => c.id), pets = C.pets.map(p => p.id);
  for (const cls of C.classes) for (const sex of [0, 1]) {
    const sp = new CharSprite(cls.sprites[sex], randomColors(), cls.nohats ? null : hats[(i * 7) % hats.length], cls.nohats ? null : capes[(i * 5) % capes.length], cls.nopets ? null : pets[(i * 3) % pets.length]);
    await sp.load();
    const x = 90 + (i % 14) * 165, y = 300 + Math.floor(i / 14) * 520;
    sp.draw(g, 'staticR', 0, x, y, 3.0, false, { loop: true });
    sp.draw(g, 'runR', 0.2, x, y + 230, 3.0, false, { loop: true, moving: true, at: 0.2 });
    const atk = cls.casts ? cls.casts[0] + 'R' : 'anim1R';
    i++;
  }
  return i;
})()""")
time.sleep(2)
shot('allchars', clip={'x': 0, 'y': 0, 'width': 2400, 'height': 1100})
