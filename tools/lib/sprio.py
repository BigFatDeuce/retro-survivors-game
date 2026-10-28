"""safe read-modify-write of game/data/sprites.json between concurrent builders (lock + atomic replace)"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import json, os, time
try: import fcntl
except ImportError: fcntl = None   # Windows: one builder at a time

P = f'{ROOT}/game/data/sprites.json'


def _win_lock():
    """0.91: Windows has no flock: an exclusive lock file (created atomically), taken over when older than 10 min"""
    lp = f'{ROOT}/work/sprites.wlock'
    for i in range(1200):
        try: fd = os.open(lp, os.O_CREAT | os.O_EXCL | os.O_WRONLY); os.write(fd, str(os.getpid()).encode()); os.close(fd); return lp
        except FileExistsError:
            try:
                if time.time() - os.path.getmtime(lp) > 600: os.remove(lp)
            except OSError: pass
            time.sleep(0.25)
    raise TimeoutError('sprites.json lock')


def update(fn):
    with open(f'{ROOT}/work/sprites.lock', 'w') as lk:
        fcntl and fcntl.flock(lk, fcntl.LOCK_EX)
        wl = None if fcntl else _win_lock()
        try:
            for i in range(20):
                try: S = json.load(open(P)); break
                except json.JSONDecodeError: time.sleep(0.5)
            fn(S)
            tmp = f'{P}.{os.getpid()}.tmp'
            with open(tmp, 'w') as f: json.dump(S, f, separators=(',', ':'))
            for i in range(40):   # (0.91: Windows refuses the replace while another process reads the file: try again)
                try: os.replace(tmp, P); break
                except PermissionError: time.sleep(0.25)
            else: os.replace(tmp, P)
        finally:
            if wl:
                try: os.remove(wl)
                except OSError: pass
    return S
