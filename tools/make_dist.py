"""Build the publishable web folder: dist/web = game/ with the JS and fonts inlined into index.html.
Usage: make_dist.py <baseline_dir>  -> also writes dist/changed.json {changed: [...], stale: [...]} against the baseline."""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _root import ROOT
import sys, os, re, json, shutil, base64, hashlib
import release as RL

G = f'{ROOT}/game'
D = f'{ROOT}/dist/web'


def h(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


def build():
    if os.path.exists(D): shutil.rmtree(D)
    os.makedirs(D)
    s = open(f'{G}/index.html', encoding='utf8').read()

    def js(m):
        return '<script>\n' + open(f'{G}/{m.group(1)}', encoding='utf8').read() + '</script>'
    s = re.sub(r'<script src="([^"?]+)(?:\?[^"]*)?"></script>', js, s)   # (0.48: the tags carry ?v=BUILD)

    def font(m):
        return "url('data:font/woff2;base64," + base64.b64encode(open(f'{G}/{m.group(1)}', 'rb').read()).decode() + "')"
    s = re.sub(r"url\('(assets/fonts/[^']+\.woff2)'\)", font, s)
    open(f'{D}/index.html', 'w', encoding='utf8').write(s)
    for sub in ('data', 'assets', 'lib'):   # (0.61: lib/pixi.min.js, loaded only by the PixiJS renderer)
        for src, rel in RL.game_files(sub):
            if rel.startswith('assets/fonts/'): continue   # (inlined above)
            os.makedirs(os.path.dirname(f'{D}/{rel}'), exist_ok=True)
            shutil.copy2(src, f'{D}/{rel}')


def diff(base):
    cur = {}
    for root, _, files in os.walk(D):
        for f in files:
            p = os.path.join(root, f); cur[os.path.relpath(p, D)] = p
    old = {}
    for root, _, files in os.walk(base):
        for f in files:
            p = os.path.join(root, f); old[os.path.relpath(p, base)] = p
    changed = sorted(k for k, p in cur.items() if k not in old or h(p) != h(old[k]))
    stale = sorted(k for k in old if k not in cur)
    json.dump(dict(changed=changed, stale=stale), open(f'{ROOT}/dist/changed.json', 'w'), indent=0)
    tot = sum(os.path.getsize(cur[k]) for k in changed)
    print('changed', len(changed), round(tot / 1e6, 1), 'MB; stale', len(stale))


if __name__ == '__main__':
    build()
    if len(sys.argv) > 1: diff(sys.argv[1])
