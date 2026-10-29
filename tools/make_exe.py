"""Retro Survivors -> the playable Windows folder dist/RetroSurvivors (RetroSurvivors.exe = Electron + the game, nothing to
install, no zip), from Windows OR Linux.
  python tools/make_exe.py [--out DIR]        (or make_exe.bat / make_exe.sh at the repo's root)
The version comes from game/js/assets.js (BUILD), Electron's from tools/lib/release.py (shared with the AppImage), the
shell is tools/win/main.js + icon, the whole game/ folder is copied. Downloads (kept in dist/cache, Internet the first
time only): Electron for Windows x64 (~110 MB) and rcedit, which gives the exe its icon and version (on Linux through
wine when it is installed, else the exe keeps Electron's icon). The game must be closed: a running RetroSurvivors.exe
locks its folder."""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _root import ROOT
import os, sys, json, shutil, subprocess, zipfile
import release as RL

RCEDIT = '2.0.0'
LOCALES = {'en-US', 'fr', 'de', 'es', 'it', 'nl', 'pt-BR', 'pt-PT'}
README = """Retro Survivors {v} - unofficial fan game, Dofus universe (c) Ankama Games.

Play: double-click RetroSurvivors.exe (nothing to install).
If Windows shows "Windows protected your PC": click "More info", then "Run anyway"
(the exe is not signed, which is normal for a fan game).
F11 = full screen. Saves are kept in %APPDATA%\\Retro Survivors.
"""


def rcedit(exe, ver):
    try: rc = RL.fetch(f'https://github.com/electron/rcedit/releases/download/v{RCEDIT}/rcedit-x64.exe', f'{RL.CACHE}/rcedit-x64.exe')
    except OSError as e: print('rcedit unavailable (', e, "): the exe keeps Electron's icon."); return
    cmd = [rc, exe, '--set-icon', f'{ROOT}/tools/win/icon.ico', '--set-version-string', 'ProductName', 'Retro Survivors',
           '--set-version-string', 'FileDescription', 'Retro Survivors', '--set-version-string', 'CompanyName', 'Fan-made',
           '--set-file-version', RL.parts(ver, 4), '--set-product-version', RL.parts(ver, 4)]
    if os.name != 'nt':
        if not shutil.which('wine'): print("(no wine: the exe keeps Electron's icon; make_exe.bat on Windows sets it)"); return
        cmd = ['wine'] + cmd
    if subprocess.run(cmd).returncode: print("rcedit failed: the exe keeps Electron's icon.")


def main():
    out = f'{ROOT}/dist/RetroSurvivors'
    if '--out' in sys.argv: out = os.path.abspath(sys.argv[sys.argv.index('--out') + 1]).replace('\\', '/')
    ver, ev = RL.version(), RL.ELECTRON
    print(f'=== Retro Survivors {ver} -> {out} (Electron {ev}) ===', flush=True)
    ez = RL.fetch(f'https://github.com/electron/electron/releases/download/v{ev}/electron-v{ev}-win32-x64.zip', f'{RL.CACHE}/electron-v{ev}-win32-x64.zip')
    print('Preparing the folder...', flush=True)
    if os.path.exists(out):
        try: shutil.rmtree(out)
        except OSError: sys.exit(f'Cannot replace {out}: close Retro Survivors (and any Explorer window open in it), then run this again.')
    with zipfile.ZipFile(ez) as z: z.extractall(out)
    os.rename(f'{out}/electron.exe', f'{out}/RetroSurvivors.exe')
    for f in ('resources/default_app.asar', 'LICENSES.chromium.html'):
        if os.path.exists(f'{out}/{f}'): os.remove(f'{out}/{f}')
    for f in os.listdir(f'{out}/locales'):
        if f.endswith('.pak') and f[:-4] not in LOCALES: os.remove(f'{out}/locales/{f}')
    app = f'{out}/resources/app'; os.makedirs(app)
    for f in ('main.js', 'icon.png'): shutil.copy(f'{ROOT}/tools/win/{f}', app)
    json.dump({'name': 'retro-survivors', 'productName': 'Retro Survivors', 'version': RL.parts(ver, 3), 'main': 'main.js'}, open(f'{app}/package.json', 'w'))
    print('Copying the game...', flush=True)
    n = RL.copy_game(f'{app}/game')
    rcedit(f'{out}/RetroSurvivors.exe', ver)
    open(f'{out}/README.txt', 'w', encoding='utf-8', newline='\r\n').write(README.format(v=ver))
    size = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(out) for f in fs)
    print(f'Done: {out}/RetroSurvivors.exe ({n} game files, {size / 1e6:.0f} MB)')


if __name__ == '__main__':
    main()
