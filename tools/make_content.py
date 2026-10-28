"""Rebuild game/data/content.json (every class, spell, weapon, zone, monster, text in 7 languages…) from its sources.
  python tools/make_content.py            runs the newest tools/content/patch_<version>.py, which imports the previous one,
                                          and so on down to patch_v20.py (applied on work/content_v19.json)
  python tools/make_content.py --check    builds it in memory and only says whether it equals the content.json on disk
The chain must reproduce content.json byte for byte: run --check before and after changing an older patch.
To change content: edit the newest patch, or add tools/content/patch_<new version>.py that starts with
`import patch_<previous> as P` and changes P.C (see tools/README.md); this script always runs the newest one.
Runs Python in UTF-8 mode (the older patches open files with the system's default encoding)."""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _root import ROOT, TOOLS
import os, re, sys, json, runpy, subprocess

if not sys.flags.utf8_mode:   # (re-run in UTF-8 mode, same arguments)
    sys.exit(subprocess.run([sys.executable, '-X', 'utf8', *sys.argv]).returncode)


def newest():
    found = [(tuple(int(x) for x in m.group(1).split('_')), m.group(0)) for f in os.listdir(f'{TOOLS}/content')
             if (m := re.fullmatch(r'patch_(\d+)\.py', f))]
    if not found: sys.exit('no tools/content/patch_<version>.py found')
    return max(found)[1][:-3]


if __name__ == '__main__':
    mod = newest()
    out = f'{ROOT}/game/data/content.json'
    if '--check' in sys.argv:
        print('building', mod, 'in memory...', flush=True)
        C = __import__(mod).C
        new = json.dumps(C, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        old = open(out, 'rb').read()
        if new == old: print(f'OK: {mod} reproduces game/data/content.json byte for byte ({len(new)} bytes)')
        else: sys.exit(f'DIFFERENT: {mod} gives {len(new)} bytes, game/data/content.json has {len(old)}. '
                       f'Run python tools/make_content.py to write it, then look at git diff game/data/content.json.')
    else:
        print('running', mod, flush=True)
        runpy.run_module(mod, run_name='__main__')
        print('written:', out)
