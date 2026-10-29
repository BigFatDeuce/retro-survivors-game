"""What the build scripts share (tools/make_dist.py, make_exe.py, make_appimage.py, make_apk.py): the game's version, the
Electron version of the desktop builds, the files of game/ a build ships, and cached downloads (dist/cache)."""
import os, re, shutil, sys, urllib.request
from _root import ROOT

GAME = f'{ROOT}/game'
CACHE = f'{ROOT}/dist/cache'
ELECTRON = '33.2.1'   # the desktop builds' Electron (Windows folder and Linux AppImage): change it here only

# left behind by tools, never shipped: an interrupted sprites.json write (sprio's .tmp), downloads, editor backups
SKIP_EXT = ('.tmp', '.part', '.lock', '.wlock', '.bak', '.orig', '.swp')
SKIP_NAMES = {'Thumbs.db', '.DS_Store', 'desktop.ini'}


def version():
    """BUILD in game/js/assets.js (set by tools/bump_build.py)"""
    m = re.search(r"const BUILD = '([^']+)'", open(f'{GAME}/js/assets.js', encoding='utf-8').read())
    if not m: sys.exit('version (BUILD) not found in game/js/assets.js')
    return m.group(1)


def parts(ver, n):
    """0.98 / 0.98.1 as n numbers (0.98.1: a patch release): '0.98.1' -> 0.98.1 (n 3, Electron's package.json, semver),
    0.98.1.0 (n 4, the Windows file version)"""
    p = [str(int(x)) for x in re.findall(r'\d+', ver)][:n]
    return '.'.join(p + ['0'] * (n - len(p)))


def android_code(ver):
    """the APK's versionCode, always growing: major x 10000 + minor x 100 + patch (0.98.1 -> 9801, 0.99 -> 9900; the
    versions up to 0.98 had minor x 1 (98): the new ones stay above them)"""
    p = [int(x) for x in re.findall(r'\d+', ver)] + [0, 0, 0]
    return p[0] * 10000 + p[1] * 100 + p[2] or 1


def shipped(name):
    return name not in SKIP_NAMES and not name.lower().endswith(SKIP_EXT)


def game_files(sub=''):
    """(absolute path, path relative to game/ with '/') of every file a build ships, under game/<sub>"""
    base = f'{GAME}/{sub}' if sub else GAME
    for d, dirs, fs in os.walk(base):
        dirs.sort()
        for f in sorted(fs):
            if shipped(f):
                p = os.path.join(d, f); yield p, os.path.relpath(p, GAME).replace('\\', '/')


def copy_game(dst):
    """game/ -> dst (a new folder), without the files a build does not ship; returns the number of files"""
    n = 0
    for p, rel in game_files():
        os.makedirs(os.path.dirname(f'{dst}/{rel}'), exist_ok=True)
        shutil.copy2(p, f'{dst}/{rel}'); n += 1
    return n


def fetch(url, path):
    """download once into the cache (Internet the first time only)"""
    if os.path.exists(path): return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    print('Downloading', url, flush=True)
    req = urllib.request.Request(url, headers={'User-Agent': 'retro-survivors-build'})
    with urllib.request.urlopen(req) as r, open(path + '.part', 'wb') as f: shutil.copyfileobj(r, f, 1 << 20)
    os.replace(path + '.part', path); return path
