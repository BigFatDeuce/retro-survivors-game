"""Retro Survivors -> a Linux x86_64 AppImage (Electron + the game), from Windows OR Linux, nothing to install but Python.
  python tools/make_appimage.py        (or make_appimage.bat / make_appimage.sh at the repo's root)
It adapts by itself to the project: the version is read from game/js/assets.js (BUILD), the Electron version from
tools/lib/release.py (ELECTRON, shared with make_exe.py: the same shell as the Windows build, tools/win/main.js + icon),
the whole game/ folder is copied. Downloads (kept in dist/cache, Internet the first time only): Electron for Linux, the official AppImage runtime
(AppImage/type2-runtime), and to build the squashfs image either nothing (Linux with mksquashfs), or appimagetool
(Linux without it), or squashfs-tools-ng's gensquashfs (Windows; it writes the Linux file modes from a pack file, so
AppRun and Electron stay executable). Result: dist/RetroSurvivors-<version>-x86_64.AppImage.
On the Linux PC: `chmod +x RetroSurvivors-*.AppImage` once if the file came from Windows, then run it."""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _root import ROOT
import os, shutil, subprocess, sys, zipfile, json, platform
import release as RL
from release import fetch

CACHE = RL.CACHE
APPDIR = f'{ROOT}/dist/appimage/RetroSurvivors.AppDir'
NAME = 'retro-survivors'
RUNTIME_URL = 'https://github.com/AppImage/type2-runtime/releases/download/continuous/runtime-x86_64'
TOOL_URL = 'https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage'
SQFS_URL = 'https://infraroot.at/pub/squashfs/windows/squashfs-tools-ng-1.3.2-mingw64.zip'
EXEC = {'AppRun', NAME, 'chrome-sandbox', 'chrome_crashpad_handler'}   # (plus every .so)

APPRUN = """#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/lib/retro-survivors/retro-survivors" --no-sandbox "$@"
"""
DESKTOP = """[Desktop Entry]
Type=Application
Name=Retro Survivors
Comment=Unofficial fan game set in the Dofus Retro universe
Exec=retro-survivors
Icon=retro-survivors
Categories=Game;ArcadeGame;
Terminal=false
"""


def is_exec(name): return name in EXEC or name.endswith('.so') or '.so.' in name


def appdir(ver, ev):
    shutil.rmtree(os.path.dirname(APPDIR), ignore_errors=True)
    lib = f'{APPDIR}/usr/lib/{NAME}'; os.makedirs(lib)
    with zipfile.ZipFile(fetch(f'https://github.com/electron/electron/releases/download/v{ev}/electron-v{ev}-linux-x64.zip', f'{CACHE}/electron-v{ev}-linux-x64.zip')) as z:
        z.extractall(lib)
    os.rename(f'{lib}/electron', f'{lib}/{NAME}')
    for f in ('resources/default_app.asar', 'LICENSES.chromium.html'):
        if os.path.exists(f'{lib}/{f}'): os.remove(f'{lib}/{f}')
    keep = {'en-US', 'en-GB', 'fr', 'de', 'es', 'it', 'nl', 'pt-BR', 'pt-PT'}
    for f in os.listdir(f'{lib}/locales'):
        if f.endswith('.pak') and f[:-4] not in keep: os.remove(f'{lib}/locales/{f}')
    app = f'{lib}/resources/app'; os.makedirs(app)
    for f in ('main.js', 'icon.png'): shutil.copy(f'{ROOT}/tools/win/{f}', app)
    json.dump({'name': NAME, 'productName': 'Retro Survivors', 'version': f'{ver}.0', 'main': 'main.js'}, open(f'{app}/package.json', 'w'))
    print('Copying the game...', flush=True)
    RL.copy_game(f'{app}/game')
    shutil.copy(f'{ROOT}/tools/win/icon.png', f'{APPDIR}/{NAME}.png'); shutil.copy(f'{ROOT}/tools/win/icon.png', f'{APPDIR}/.DirIcon')
    open(f'{APPDIR}/{NAME}.desktop', 'w', newline='\n', encoding='utf-8').write(DESKTOP)
    open(f'{APPDIR}/AppRun', 'w', newline='\n').write(APPRUN)
    if os.name != 'nt':
        for root, dirs, files in os.walk(APPDIR):
            for f in files: os.chmod(os.path.join(root, f), 0o755 if is_exec(f) else 0o644)


def pack_file(path):
    """gensquashfs pack file: every directory and file of the AppDir with its Linux mode (Windows has none)"""
    q = lambda s: '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'
    with open(path, 'w', encoding='utf-8', newline='\n') as out:
        for root, dirs, files in os.walk(APPDIR):
            rel = os.path.relpath(root, APPDIR).replace('\\', '/')
            base = '' if rel == '.' else '/' + rel
            if base: out.write(f'dir {q(base)} 0755 0 0\n')
            for f in sorted(files):
                p = f'{base}/{f}'   # (the source path relative to -D, NOT quoted: the Windows build keeps the quotes in it)
                if ' ' in p: sys.exit(f'a space in a file name is not supported: {p}')
                out.write(f'file {q(p)} {"0755" if is_exec(f) else "0644"} 0 0 {p[1:]}\n')


def squashfs(img):
    if os.name == 'nt':
        z = fetch(SQFS_URL, f'{CACHE}/squashfs-tools-ng-mingw64.zip'); d = f'{CACHE}/sqfs-ng'
        if not os.path.isdir(d): zipfile.ZipFile(z).extractall(d)
        gen = next(os.path.join(r, f) for r, _, fs in os.walk(d) for f in fs if f == 'gensquashfs.exe')
        pf = f'{ROOT}/dist/appimage/pack.txt'; pack_file(pf)
        subprocess.run([gen, '-F', pf, '-D', APPDIR, '-c', 'zstd', '-b', '1048576', '-j', str(os.cpu_count() or 4), '--all-root', '-f', '-q', img], check=True)
        return True
    if shutil.which('mksquashfs'):
        subprocess.run(['mksquashfs', APPDIR, img, '-root-owned', '-noappend', '-comp', 'zstd', '-b', '1M', '-quiet'], check=True)
        return True
    return False


def main():
    if platform.machine().lower() not in ('amd64', 'x86_64'): print('(not an x86_64 machine: the AppImage still targets x86_64)')
    ver, ev = RL.version(), RL.ELECTRON
    out = f'{ROOT}/dist/RetroSurvivors-{ver}-x86_64.AppImage'
    print(f'=== Retro Survivors {ver} -> AppImage (Electron {ev}) ===', flush=True)
    appdir(ver, ev)
    img = f'{ROOT}/dist/appimage/game.squashfs'
    if squashfs(img):
        runtime = open(fetch(RUNTIME_URL, f'{CACHE}/runtime-x86_64'), 'rb').read()
        with open(out, 'wb') as f:
            f.write(runtime)
            with open(img, 'rb') as s: shutil.copyfileobj(s, f, 1 << 20)
    else:   # Linux without mksquashfs: the official appimagetool does it all
        tool = fetch(TOOL_URL, f'{CACHE}/appimagetool-x86_64.AppImage'); os.chmod(tool, 0o755)
        subprocess.run([tool, '--appimage-extract-and-run', '--comp', 'zstd', '-n', APPDIR, out], check=True, env=dict(os.environ, ARCH='x86_64'))
    if os.name != 'nt': os.chmod(out, 0o755)
    shutil.rmtree(f'{ROOT}/dist/appimage', ignore_errors=True)
    print(f'Done: {out} ({os.path.getsize(out) / 1e6:.0f} MB)')
    if os.name == 'nt': print('On the Linux PC: chmod +x the file once copied, then double-click it.')


if __name__ == '__main__':
    main()
