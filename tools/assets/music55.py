"""0.55: the HD Dofus musics (work/music_src/hd, FLAC) replace the client's under the same keys, + the phonk /
lofi sets (work/music_src/phonk|lofi: 3 menu tracks each + 5 zone tracks) as music/<style>/<key>.mp3.
usage: python tools/assets/music55.py   (needs ffmpeg)"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import subprocess, glob
from concurrent.futures import ThreadPoolExecutor

SRC, OUT = f'{ROOT}/work/music_src', f'{ROOT}/game/assets/audio/music'
HD = {1: 'loc_amakna', 2: 'fig_amakna', 3: 'loc_bonta', 4: 'loc_cania', 5: 'fig_cania', 6: 'cls_cra', 7: 'cls_ecaflip',
      8: 'cls_eniripsa', 9: 'cls_enutrof', 10: 'loc_kutan', 11: 'fig_kutan', 12: 'loc_brakmar', 13: 'loc_sidimote',
      14: 'fig_sidimote', 15: 'cls_feca', 16: 'cls_iop', 17: 'cls_osamodas', 18: 'cls_sacrieur', 19: 'loc_ilyzaelle',
      20: 'fig_ilyzaelle', 21: 'loc_moon', 22: 'loc_trool', 23: 'loc_otomai', 24: 'fig_otomai', 25: 'loc_wabbit',
      26: 'loc_dragoturkey1', 27: 'loc_dragoturkey2', 28: 'cls_sadida', 29: 'cls_sram', 30: 'cls_xelor',
      31: 'loc_pandawaforest', 32: 'loc_pandavillage', 33: 'loc_pandawafight'}
jobs = []
for f in glob.glob(f'{SRC}/hd/*.flac'):
    n = int(_os.path.basename(f).split('.')[0])
    if n in HD: jobs.append((f, f'{OUT}/{HD[n]}.mp3'))
for st in ('phonk', 'lofi'):
    for f in glob.glob(f'{SRC}/{st}/*.wav'):
        k = _os.path.basename(f)[:-4].replace('loc_ankama', 'loc_amakna'); jobs.append((f, f'{OUT}/{st}/{k}.mp3'))
def enc(j):
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', j[0], '-vn', '-ac', '2', '-ar', '44100', '-b:a', '192k', j[1]], check=True); return j[1]
# 0.56b: the class themes without a track of their own take one
for n, k in ((32, 'cls_pandawa'), (14, 'cls_roublard'), (2, 'cls_bandit')):
    jobs += [(f, f'{OUT}/{k}.mp3') for f in glob.glob(f'{SRC}/hd/{n:02d}. *.flac')]
with ThreadPoolExecutor(4) as ex: done = list(ex.map(enc, jobs))
print(len(done), 'tracks')
