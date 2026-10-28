"""0.81: the ambers' worth, computed (no bot runs): a player who kills every monster as it comes and picks up every
amber. The waves then come every wave[3] x pk x 0.5 s with (2 + floor(em / 3)) x late x pk monsters (game.js spawn),
so with amberRate = wave[3] / ref ambers a kill, every map gives 2 (2 + floor(em / 3)) late / ref ambers a second.
Each is worth v0 (1 + grow) ^ floor(t / 30) (x xpPace in addXP). The target: level TARGET_LV (4 spells and the weapon at
their 4th level = 1 + 15 + 4 picks) at TARGET_T seconds. Elites' / bosses' ancestral ambers and chests come on top.
usage: python tools/content/calc_amber081.py   -> prints v0 and the level reached minute by minute (copy v0 into patch_081)"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
C = json.load(open(f'{ROOT}/game/data/content.json', encoding='utf8'))
R = C['run']
# 0.83: EVERYTHING maxed at 7:30 = 4 spells (1 given + 3 x 4 picks + 3 more levels each... 15 picks), the weapon
# (4), 5 characteristics x 4 (20): level 1 + 15 + 4 + 20 = 40
TARGET_LV, TARGET_T = int(os.environ.get('LV', 40)), int(os.environ.get('T', 450))
GROW, STEP, REF = float(os.environ.get('GROW', 0.15)), 30, 0.34
XE = R.get('xpEarly') or []


def xp_next(lv):   # (game.js addXP: what the level lv needs)
    b = 5 + (lv - 1) * 10 if lv < 20 else 195 + (lv - 20) * 22 if lv < 40 else 640 + (lv - 40) * 40
    return round(b * (XE[lv - 1] if lv - 1 < len(XE) else 1))


def ambers_per_s(t):
    m = t / 60
    em = m * R.get('pace', 2) * (0.7 + 0.3 * min(1, m / 10))
    lt, K = R.get('spawnLateT', 1e9), R.get('spawnLateK')
    late = 1 if not K or m < lt else K[0] + (K[1] - K[0]) * min(1, max(0, (m - lt) / max(0.01, R.get('spawnLateEnd', 10) - lt)))
    if m >= R.get('spawnStopT', 1e9): return 0
    return 2 * (2 + math.floor(em / 3)) * late / REF


def levels(v0, until=600, dt=0.5):
    lv, xp, need, out, t = 1, 0.0, xp_next(1), {}, 0.0
    while t < until:
        xp += ambers_per_s(t) * dt * v0 * (1 + GROW) ** math.floor(t / STEP) * R.get('xpPace', 1)
        while xp >= need: xp -= need; lv += 1; need = xp_next(lv)
        t += dt
        if abs(t % 30) < 1e-9: out[int(t)] = lv
    return out


lo, hi = 0.0001, 0.3
for _ in range(60):
    mid = (lo + hi) / 2
    if levels(mid)[TARGET_T] >= TARGET_LV: hi = mid
    else: lo = mid
v0 = math.ceil(hi * 1e4) / 1e4
L = levels(v0)
print('v0', v0, '(grow', GROW, 'every', STEP, 's, ref', REF, ')')
for t in range(60, 601, 60): print(f'{t // 60:2d}:00  level {L[t]:3d}  amber worth {v0 * (1 + GROW) ** (t // STEP):.3f}  ambers/s {ambers_per_s(t - 1):.1f}')
print('7:30  level', L[450], ' 8:30  level', L[510])
