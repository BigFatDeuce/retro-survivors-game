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
