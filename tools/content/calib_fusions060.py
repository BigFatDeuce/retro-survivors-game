"""0.60: calibrates the spell fusions' damage (CAL in tools/content/fusions060.py) with the spell bench (tools/checks/sim_node.js BENCH,
level 6, minute 4, 120 s, the mean of 3 maps): a fusion that replaces two spells must do x1.25 the damage of the two
side by side; a spell + weapon fusion (the weapon is kept) x1.6 the spell alone. Rewrites CAL, re-runs patch_060.
usage: python tools/content/calib_fusions060.py [rounds=2]"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
import fusions060 as F6

MAPS = ('astrub', 'cania', 'koalak')
TARGET = {'spell': 1.25, 'global': 1.25, 'weapon': 1.6}


def bench(ids):
    out = {}
    def one(args):
        ids_, m = args
        env = dict(os.environ, BENCH=','.join(ids_), LV='6', DUR='120')
        r = subprocess.run(['node', f'{ROOT}/tools/checks/sim_node.js', 'x', m, '0'], capture_output=True, text=True, env=env, timeout=3600)
        return m, [json.loads(l) for l in r.stdout.splitlines() if l.startswith('{')]
    chunks = [ids[i:i + 6] for i in range(0, len(ids), 6)]
    with ThreadPoolExecutor(6) as ex:
        for m, rows in ex.map(one, [(c, m) for c in chunks for m in MAPS]):
            for r in rows: out.setdefault(r['id'], []).append(r['dps'])
    return {k: sum(v) / len(v) for k, v in out.items()}


def patch():
    subprocess.run([sys.executable, '-X', 'utf8', f'{ROOT}/tools/content/patch_060.py'], check=True, capture_output=True)


def main(rounds=2):
    C = json.load(open(f'{ROOT}/game/data/content.json', encoding='utf-8'))
    ings = sorted({x for v in F6.F.values() for x in (v[1], v[2]) if x in C['spells']})
    base = bench(ings); print('ingredients', {k: round(v) for k, v in base.items()}, flush=True)
    cal = dict(F6.CAL)
    for rd in range(rounds):
        got = bench(list(F6.F))
        for fid, v in F6.F.items():
            kind, a, b = v[3], v[1], v[2]
            want = TARGET[kind] * (base.get(a, 0) + (0 if kind == 'weapon' else base.get(b, 0)))
            k = want / max(1, got.get(fid, 0)); k = min(2.5, max(0.4, k))   # (one step at most x2.5 / x0.4 per round)
            cal[fid] = round(cal.get(fid, 1.0) * k, 3)
            print(f'{rd} {fid:18s} {got.get(fid, 0):7.0f} -> want {want:7.0f}  cal {cal[fid]}', flush=True)
        src = open(f'{ROOT}/tools/content/fusions060.py', encoding='utf-8').read()
        src = re.sub(r'^CAL = \{.*?\}$', 'CAL = ' + json.dumps(cal, sort_keys=True).replace('"', "'"), src, flags=re.M | re.S)
        open(f'{ROOT}/tools/content/fusions060.py', 'w', encoding='utf-8').write(src)
        F6.CAL = cal; patch()
    got = bench(list(F6.F))
    for fid, v in F6.F.items():
        kind, a, b = v[3], v[1], v[2]; sep = base.get(a, 0) + (0 if kind == 'weapon' else base.get(b, 0))
        print(f'final {fid:18s} {got.get(fid, 0):7.0f}  vs  {sep:7.0f}  x{got.get(fid, 0) / max(1, sep):.2f}')


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 2)
