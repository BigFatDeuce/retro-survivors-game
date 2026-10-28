"""0.94: ONE command for every automated test of the game — what exists already (check.py,
stress.py, tests/t_*.py through pw_test.py) and the 0.94 suites (qa_unit.js, qa_func.py, qa_web.py) — run one after the
other (never two at once: some open the same saves' code paths and measure the machine), each judged PASS / FAIL, or
NOT-RUN with the reason (a tool missing, a step not asked for). Nothing here touches the player's saves (every browser
test uses a fresh profile and a local server on a free port), the exe or the deployed site (qa_web.py only reads it).

  quick   (~5 min)  qa_unit (data, saves, rules, every spell / weapon / zone run in node) + qa_spells (every spell does
                    what it says: its effects seen on dummies) + qa_func boot / saves / import /
                    nav / shop / runs + t_save (export / import through the options)
  full    (~1 h)    quick + check.py + qa_func restart / settings / profiles / sizes + t_freeze + t_tmap + t_levelup and
                    t_cards (PC and phone both ways) + t_noscroll + t_uiaudit (6 PC sizes, phone upright / sideways) +
                    t_overlap (6 phones, upright and sideways) + t_pixicmp + stress.py (one pass) + the run tests on the
                    Canvas 2D renderer and in Edge
  --web             adds qa_web.py (the deployed site, read only)
  --only a,b        just those steps (names as printed);  --list   the steps

usage: python tools/qa.py quick|full [--web] [--only a,b] [--out DIR]
report: work/qa/<date>/report.md (+ results.json, each step's log); exit code 1 if a step failed"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _root import ROOT
import sys, os, re, json, time, shutil, datetime, subprocess

PY, NODE = sys.executable, shutil.which('node')
PW = [PY, 'tools/checks/pw_test.py']
PC = ['1280x720', '1920x1080', '2560x1440', '3840x2160', '3440x1440', '2560x1080']
PHONE_UP, PHONE_SIDE = dict(VW='390', VH='844', DPR='3', MOBILE='1'), dict(VW='844', VH='390', DPR='3', MOBILE='1')


def generic(out, rc):
    """the conventions of the older tests: FAIL / PROB lines, 'FAILS n', 'SUMMARY … problems n', page errors"""
    L = out.splitlines()
    f = [l for l in L if l.startswith(('FAIL ', 'PROB ')) or '[pageerror]' in l]
    for i, l in enumerate(L):   # (a traceback of the test itself; the local server's own, a page closed mid-file, is not one)
        if l.startswith('Traceback') and not any('socketserver.py' in x or 'http/server.py' in x.replace(chr(92), '/') for x in L[i + 1:i + 6]): f.append('Traceback: ' + ' | '.join(L[i + 1:i + 8])[:400])
    for m in re.finditer(r'^FAILS (\d+)', out, re.M):
        if int(m.group(1)): f.append(m.group(0))
    for m in re.finditer(r'^SUMMARY .*problems (\d+)', out, re.M):
        if int(m.group(1)): f.append(m.group(0))
    if rc and not f: f.append(f'exit code {rc}')
    return f


def noscroll(out, rc):
    """t_noscroll: a window cut by the screen, or a menu that scrolls — but the long lists keep their scroll (0.65: armory,
    achievements, statistics)"""
    f, cur = generic(out, rc), None
    for l in out.splitlines():
        if l.startswith('== '): cur = l[3:].split(':')[0]
        elif l.strip().startswith('CUT') or (l.strip().startswith('SCROLL') and cur not in ('armory', 'achievements', 'stats')): f.append(f'{cur}: {l.strip()}')
    return f


def jsonl(key):
    def p(out, rc):
        f = []
        for l in out.splitlines():
            if l.startswith('{'):
                try: r = json.loads(l)
                except ValueError: continue
                if r.get('ok') is False: f.append(f"{r.get(key)}: {'; '.join(map(str, r.get('fails') or [r.get('detail') or r.get('name')]))[:400]}")
        if rc and not f: f.append(f'exit code {rc}')
        if 'Traceback' in out: f.append('Traceback: ' + out[out.index('Traceback'):][:300])
        return f
    return p


def unit(out, rc):
    f = [f"{r['suite']} / {r['name']}: {r.get('detail')}" for r in (json.loads(l) for l in out.splitlines() if l.startswith('{')) if not r.get('ok')]
    return f or ([f'exit code {rc}'] if rc else [])


def pixicmp(out, rc):
    f = generic(out, rc)
    for m in re.finditer(r'^(\S+)\s+mean\s+([\d.]+)', out, re.M):
        if float(m.group(2)) > 3.0: f.append(f'{m.group(1)}: mean difference {m.group(2)} / 255 (over 3)')
    m = re.search(r"^ERRS (\[.*\])", out, re.M)
    if m and m.group(1) != '[]': f.append('errors: ' + m.group(1)[:300])
    return f


def stress(out, rc):
    return [] if re.search(r'^PASS ->', out, re.M) and not rc else [l for l in out.splitlines() if l.startswith('  ERR')][:10] or [f'stress FAIL (exit {rc})']


def check(out, rc):
    return [] if '== PASS' in out and not rc else [l for l in out.splitlines() if 'FAIL' in l or 'error' in l.lower()][:10] or [f'exit code {rc}']


# name, suites, command, extra env, parser, timeout (s)
def steps(out):
    S = [('unit', 'quick', [NODE, 'tools/checks/qa_unit.js'], {}, unit, 900),
         ('spells', 'quick', [NODE, 'tools/checks/qa_spells.js'], {}, jsonl('id'), 900),
         ('func-core', 'quick', [PY, 'tools/checks/qa_func.py', 'boot', 'saves', 'import', 'nav', 'shop', 'runs', '--out', f'{out}/func-core'], {}, jsonl('test'), 2400),
         ('t_save', 'quick', PW + ['tests/t_save.py', f'{out}/t_save'], {}, generic, 900),
         ('check', 'full', [PY, 'tools/check.py'], {}, check, 1800),
         ('func-more', 'full', [PY, 'tools/checks/qa_func.py', 'restart', 'settings', 'profiles', 'sizes', '--out', f'{out}/func-more'], {}, jsonl('test'), 3600),
         ('t_freeze', 'full', PW + ['tests/t_freeze.py', f'{out}/t_freeze'], {}, generic, 3600),
         ('t_tmap', 'full', PW + ['tests/t_tmap.py', f'{out}/t_tmap'], {}, generic, 1800)]
    for tag, env in [('pc', {}), ('phone-up', PHONE_UP), ('phone-side', PHONE_SIDE)]:
        S.append((f't_levelup-{tag}', 'full', PW + ['tests/t_levelup.py', f'{out}/t_levelup-{tag}'], env, generic, 900))
        S.append((f't_cards-{tag}', 'full', PW + ['tests/t_cards.py', f'{out}/t_cards-{tag}'], env, generic, 2400))
    S.append(('t_noscroll', 'full', PW + ['tests/t_noscroll.py', f'{out}/t_noscroll'], dict(VW='1920', VH='1080'), noscroll, 1800))
    for sz in PC:
        w, h = sz.split('x'); S.append((f't_uiaudit-{sz}', 'full', PW + ['tests/t_uiaudit.py', f'{out}/t_uiaudit-{sz}'], dict(VW=w, VH=h), generic, 2400))
    S.append(('t_uiaudit-phone-up', 'full', PW + ['tests/t_uiaudit.py', f'{out}/t_uiaudit-phone-up'], PHONE_UP, generic, 2400))
    S.append(('t_uiaudit-phone-side', 'full', PW + ['tests/t_uiaudit.py', f'{out}/t_uiaudit-phone-side'], PHONE_SIDE, generic, 2400))
    for sz in ['390x844', '360x800', '412x915', '844x390', '800x360', '915x412']:   # (0.94: phones both ways — what overlaps, what is cut, squeezed lists)
        w, h = sz.split('x'); S.append((f't_overlap-{sz}', 'full', PW + ['tests/t_overlap.py', f'{out}/t_overlap-{sz}'], dict(VW=w, VH=h, DPR='3', MOBILE='1'), generic, 2400))
    S += [('t_pixicmp', 'full', PW + ['tests/t_pixicmp.py', f'{out}/t_pixicmp'], {}, pixicmp, 2400),
          ('stress', 'full', [PY, 'tools/checks/stress.py', '--reps', '1', '--max-min', '20', '--out', f'{out}/stress'], {}, stress, 2400),
          ('canvas2d', 'full', [PY, 'tools/checks/qa_func.py', 'boot', 'runs', '--renderer', 'canvas', '--out', f'{out}/canvas2d'], {}, jsonl('test'), 1800),
          ('edge', 'full', [PY, 'tools/checks/qa_func.py', 'boot', 'saves', 'runs', '--out', f'{out}/edge'], dict(QA_CHANNEL='msedge'), jsonl('test'), 1800),
          ('web', 'web', [PY, 'tools/checks/qa_web.py', '--out', f'{out}/web'], {}, jsonl('check'), 1800)]
    return S


def main():
    try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception: pass
    a = sys.argv[1:]
    if not a or a[0] not in ('quick', 'full', '--list'): sys.exit(__doc__)
    out = a[a.index('--out') + 1] if '--out' in a else f"{ROOT}/work/qa/{datetime.datetime.now():%Y%m%d-%H%M%S}-{a[0]}"
    S = steps(out)
    if a[0] == '--list':
        for s in S: print(f'{s[0]:24s} {s[1]}')
        return 0
    os.makedirs(out, exist_ok=True)
    only = a[a.index('--only') + 1].split(',') if '--only' in a else None
    want = {'quick'} | ({'full'} if a[0] == 'full' else set()) | ({'web'} if '--web' in a else set())
    res = []; t00 = time.time()
    for name, suite, cmd, env, parse, tmo in S:
        if only and name not in only: continue
        if not only and suite not in want:
            res.append(dict(step=name, suite=suite, status='NOT-RUN', reason='not in this suite' if suite != 'web' else 'the deployed site: --web', s=0, fails=[])); continue
        if cmd[0] is None:
            res.append(dict(step=name, suite=suite, status='NOT-RUN', reason='node not found', s=0, fails=[])); continue
        if name == 'edge' and not any(os.path.exists(p) for p in [r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe', r'C:\Program Files\Microsoft\Edge\Application\msedge.exe', '/usr/bin/microsoft-edge']):
            res.append(dict(step=name, suite=suite, status='NOT-RUN', reason='Edge is not installed', s=0, fails=[])); continue
        print(f'-- {name} ...', flush=True); t = time.time()
        e = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8', **env); e.pop('PORT', None)
        try:
            p = subprocess.run(cmd, cwd=ROOT, env=e, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=tmo)
            o, rc = p.stdout + ('\n' + p.stderr if p.stderr.strip() else ''), p.returncode
        except subprocess.TimeoutExpired as x:
            o, rc = (x.stdout or b'').decode('utf-8', 'replace') if isinstance(x.stdout, bytes) else (x.stdout or ''), -1
            o += f'\n(timeout after {tmo} s)'
        open(f'{out}/{name}.log', 'w', encoding='utf-8').write(o)
        f = parse(o, rc) if rc != -1 else [f'timeout after {tmo} s']
        r = dict(step=name, suite=suite, status='FAIL' if f else 'PASS', s=round(time.time() - t), fails=f[:40]); res.append(r)
        print(f"   {r['status']} ({r['s']} s)" + (''.join(f'\n     {x[:300]}' for x in f[:8]) if f else ''), flush=True)
    ran = [r for r in res if r['status'] != 'NOT-RUN']; bad = [r for r in ran if r['status'] == 'FAIL']
    L = [f"# Retro Survivors — QA {a[0]} — {datetime.datetime.now():%Y-%m-%d %H:%M}", '',
         f"**{'PASS' if not bad else 'FAIL'}** — {len(ran)} steps run, {len(bad)} failed, {len(res) - len(ran)} not run, {round((time.time() - t00) / 60, 1)} min", '',
         '| step | suite | result | s | details |', '|---|---|---|---|---|']
    for r in res:
        d = r.get('reason') or ('; '.join(r['fails'][:3])[:300].replace('|', '/') if r['fails'] else '')
        L.append(f"| {r['step']} | {r['suite']} | {'**FAIL**' if r['status'] == 'FAIL' else r['status']} | {r['s']} | {d} |")
    for r in bad: L += ['', f"## {r['step']}", ''] + [f'- {x}' for x in r['fails']] + ['', f"log: `{out}/{r['step']}.log`"]
    open(f'{out}/report.md', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    json.dump(res, open(f'{out}/results.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(('PASS' if not bad else 'FAIL'), '->', f'{out}/report.md')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
