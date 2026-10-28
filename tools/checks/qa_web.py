"""0.94: the deployed web version, READ ONLY (nothing is sent but page loads: no login, no form,
no change of the site or of its configuration). A fresh browser profile each time (Playwright's Chromium, or Edge with
QA_CHANNEL=msedge), so the player's own saves are not involved.

  cold     the first visit (empty cache): time to the menu, every response (HTTP errors, failed requests), console and
           page errors, the version shown, the transferred bytes
  warm     the same page again (the browser's cache): how many files came from the cache, time to the menu
  run      a short run started on the site (?autostart=1&fresh=1, in the test profile): its files load, it moves
  files    every file of the local game folder named by the page / scripts is asked with HEAD (exact case: the server is
           case-sensitive) — only the game's own data / scripts / atlases, a few hundred requests at most
  compare  the deployed BUILD against the local one

usage: python tools/checks/qa_web.py [URL] [--out DIR] [--no-files]      (default URL https://retro-survivors.holy-c.men/)
prints one JSON line per check ({ check, ok, info, fails }) then 'WEB <n> checks, <m> failed'; exit code 1 if any failed"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, json, time, re, datetime, urllib.request, urllib.error
from playwright.sync_api import sync_playwright

URL = 'https://retro-survivors.holy-c.men/'


def main():
    try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception: pass
    args = [a for a in sys.argv[1:]]; url = next((a for a in args if a.startswith('http')), URL)
    out = args[args.index('--out') + 1] if '--out' in args else f"{ROOT}/work/qa/web-{datetime.datetime.now():%Y%m%d-%H%M%S}"
    os.makedirs(out, exist_ok=True); res = []
    def rep(check, ok, info=None, fails=None):
        r = dict(check=check, ok=bool(ok), info=info or {}, fails=fails or []); res.append(r); print(json.dumps(r, ensure_ascii=False), flush=True)
    local_build = re.search(r"BUILD\s*=\s*'([^']+)'", open(f'{ROOT}/game/js/assets.js', encoding='utf-8').read()).group(1)
    with sync_playwright() as p:
        try: b = p.chromium.launch(channel=os.environ.get('QA_CHANNEL', 'chromium'), args=['--autoplay-policy=no-user-gesture-required'])
        except Exception: b = p.chromium.launch()
        ctx = b.new_context(viewport={'width': 1920, 'height': 1080}); pg = ctx.new_page()
        cdp = ctx.new_cdp_session(pg); cdp.send('Network.enable')
        net = {}
        cdp.on('Network.responseReceived', lambda e: net.__setitem__(e['requestId'], dict(url=e['response']['url'], status=e['response']['status'], cache=bool(e['response'].get('fromDiskCache') or e['response'].get('fromMemoryCache') or e['response'].get('fromServiceWorker')))))
        cdp.on('Network.requestServedFromCache', lambda e: net.setdefault(e['requestId'], {}).__setitem__('cache', True))
        sizes = {}; cdp.on('Network.loadingFinished', lambda e: sizes.__setitem__(e['requestId'], e.get('encodedDataLength', 0)))
        failed = []; cdp.on('Network.loadingFailed', lambda e: failed.append(e.get('errorText', '?') + ' ' + str(e.get('requestId'))))
        errs = []; pg.on('pageerror', lambda e: errs.append('pageerror: ' + str(e)[:300])); pg.on('console', lambda m: m.type == 'error' and errs.append('console: ' + m.text[:300]))
        def visit(q=''):
            net.clear(); sizes.clear(); failed.clear(); errs.clear(); t = time.time()
            pg.goto(url + q, wait_until='domcontentloaded', timeout=120000)
            pg.wait_for_function("typeof Game !== 'undefined' && (Game.state === 'menu' || Game.state === 'run')", timeout=180000)
            return round(time.time() - t, 2)
        def http_fails(): return [f"{v['status']} {v['url']}" for v in net.values() if v.get('status', 200) >= 400]
        # cold
        s = visit(''); pg.wait_for_function("document.querySelector('.menu-buttons')", timeout=120000); time.sleep(1.5)
        build = pg.evaluate("typeof BUILD !== 'undefined' ? BUILD : null"); shown = pg.evaluate("(document.querySelector('.version') || {}).textContent || ''")
        f = http_fails() + failed + errs
        rep('cold', not f, dict(menu_s=s, files=len(net), MB=round(sum(sizes.values()) / 2**20, 1), build=build, shown=shown.strip()), f[:20])
        pg.screenshot(path=f'{out}/web_menu.png')
        # warm
        s = visit(''); pg.wait_for_function("document.querySelector('.menu-buttons')", timeout=120000); time.sleep(1.0)
        n = len(net); c = sum(1 for v in net.values() if v.get('cache'))
        f = http_fails() + failed + errs
        rep('warm', not f, dict(menu_s=s, files=n, from_cache=c, MB_over_network=round(sum(v for k, v in sizes.items() if not net.get(k, {}).get('cache')) / 2**20, 1)), f[:20])
        # a run
        s = visit('?autostart=1&fresh=1&cls=iop&map=astrub&t=30')
        moved = False
        try:
            pg.wait_for_function("Game.run && Game.state === 'run' && Game.run.time > 0.5", timeout=120000)
            t0 = pg.evaluate("Game.run.time"); time.sleep(4); moved = pg.evaluate("Game.run.time") > t0 + 1
        except Exception as e: errs.append(f'the run did not start: {type(e).__name__}')
        pg.screenshot(path=f'{out}/web_run.png')
        f = http_fails() + failed + errs + ([] if moved else ['the run does not move'])
        rep('run', not f, dict(load_s=s, files=len(net), pixi=pg.evaluate("typeof PX !== 'undefined' && PX.on"), gpu=pg.evaluate("typeof PX !== 'undefined' ? PX.gpu || null : null")), f[:20])
        b.close()
    # every game file the scripts name, by HEAD (exact case)
    if '--no-files' not in args:
        G = f'{ROOT}/game'; names = set(['index.html', 'data/content.json', 'data/sprites.json', 'data/sounds.json'])
        for fn in os.listdir(f'{G}/js'):
            if fn.endswith('.js'):
                names.add('js/' + fn)
                for m in re.finditer(r"['\"`](assets/[^'\"`$?{}]+\.(?:webp|png|jpg|mp3|json|woff2?))['\"`]", open(f'{G}/js/{fn}', encoding='utf-8').read()): names.add(m.group(1))
        miss = []
        for n in sorted(names):
            try:
                rq = urllib.request.Request(url + n + f'?v={build or local_build}', method='HEAD', headers={'User-Agent': 'retro-survivors-qa'})
                with urllib.request.urlopen(rq, timeout=30) as r:
                    if r.status >= 400: miss.append(f'{r.status} {n}')
            except urllib.error.HTTPError as e: miss.append(f'{e.code} {n}')
            except Exception as e: miss.append(f'{type(e).__name__} {n}')
        rep('files', not miss, dict(asked=len(names)), miss[:30])
    rep('compare', build == local_build, dict(deployed=build, local=local_build), [] if build == local_build else [f'the site runs {build}, the local game is {local_build} (not deployed yet — not an error of the site)'])
    json.dump(res, open(f'{out}/web.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    bad = [r for r in res if not r['ok'] and r['check'] != 'compare']
    print(f'WEB {len(res)} checks, {len(bad)} failed -> {out}')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
