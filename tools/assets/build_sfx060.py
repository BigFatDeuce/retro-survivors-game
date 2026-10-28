"""0.60: the sound effects from the up-to-date Dofus Retro client. Measured: 828 of its 905 effects are the same as in
1.41.9 and 76 are better (44.1 kHz, up to 256 kb/s; 11 of them are used by the game); the old pack had re-encoded the
client's sounds (a lossy copy of a lossy file): the client's own MP3 data is taken again, untouched.
Rebuilds game/assets/audio/sfx_pack.mp3 (MP3 frames of each sound one after the other) and the offsets in
game/data/sounds.json ('pack': name -> [byte offset, byte length]): every name of the pack found among the new client's
exported sounds takes its new MP3 data, the others keep the old bytes.
The new client is read from RS_NEWCLIENT (default: %LOCALAPPDATA%/Ankama/Retro/resources/app/retroclient).
Also extracts whole tracks of the new client's audio/musics.swf: `python tools/assets/build_sfx060.py music name[,name…]`
writes game/assets/audio/music/<name>.mp3 from the client's MP3 data (160 kb/s there).
usage: python tools/assets/build_sfx060.py [music loc_incarnam,fig_tower_normal,loc_tower_minigame]"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import json, os, struct, sys
import swflib as S

from _root import CLIENT as NEW   # the up-to-date installed client (_root.py)
RATES = [5512, 11025, 22050, 44100]


def sounds_of(path):
    """name -> (format, rate, mp3 bytes) for every exported DefineSound of a SWF"""
    sw = S.read_swf(path); ex = S.exports(sw['tags']); by_id = {}
    for t in sw['tags']:
        if t.code != 14: continue
        b = t.data; sid = struct.unpack_from('<H', b, 0)[0]; f = b[2]
        by_id[sid] = (f >> 4, RATES[(f >> 2) & 3], bytes(b[9:]) if (f >> 4) == 2 else None)
    return {name: by_id[i] for name, i in ex.items() if i in by_id}


def pcm(mp3):
    """mono 4 kHz 16-bit samples of an MP3 (imageio-ffmpeg's ffmpeg)"""
    import subprocess, imageio_ffmpeg, numpy as np
    r = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-v', 'quiet', '-f', 'mp3', '-i', 'pipe:0', '-ac', '1', '-ar', '4000', '-f', 's16le', 'pipe:1'], input=mp3, capture_output=True)
    return np.frombuffer(r.stdout, dtype='<i2').astype('float32')


def envelope(x, n=48):
    import numpy as np
    if len(x) < 8: return None
    w = max(1, len(x) // n); e = np.array([np.sqrt(np.mean(x[i * w:(i + 1) * w] ** 2) + 1e-9) for i in range(n)])
    return (e - e.mean()) / (e.std() + 1e-9)


def keymap(old_pack, snd):
    """the pack's names were the client's sound keys, re-encoded (no byte match): each one is found back among the 1.41.9
    client's exported sounds by its decoded length and loudness envelope, cached in work/sfx_keymap060.json"""
    import numpy as np
    cache = f'{ROOT}/work/sfx_keymap060.json'
    if os.path.exists(cache): return json.load(open(cache, encoding='utf-8'))
    olds = sounds_of(f'{ROOT}/raw/rc/audio/effects.swf'); feats = {}
    for n, (f, r, d) in olds.items():
        if d: x = pcm(d); feats[n] = (len(x), envelope(x))
    out = {}
    for name, (off, ln) in snd['pack'].items():
        x = pcm(old_pack[off:off + ln]); L, e = len(x), envelope(x); best, bs = None, -2
        if e is None: continue
        for n, (l2, e2) in feats.items():
            if e2 is None or not (0.85 < (l2 + 1) / (L + 1) < 1.18): continue
            c = float(np.dot(e, e2) / len(e)); c -= abs(l2 - L) / max(L, 1) * 0.5
            if c > bs: bs, best = c, n
        if best and bs > 0.8: out[name] = best
    json.dump(out, open(cache, 'w', encoding='utf-8'), indent=0); return out


def build_pack():
    sp = f'{ROOT}/game/data/sounds.json'; snd = json.load(open(sp, encoding='utf-8'))
    old = open(f'{ROOT}/game/assets/audio/sfx_pack.mp3', 'rb').read()
    new = sounds_of(os.path.join(NEW, 'audio', 'effects.swf'))
    KM = keymap(old, snd); RENAMED = {'EVENT': 'game_event'}
    out, pack, hd, kept = bytearray(), {}, 0, []
    for name, (off, ln) in snd['pack'].items():
        k = name if name in new else RENAMED.get(name) if name in RENAMED else KM.get(name, name); k = RENAMED.get(k, k)   # (an exported name first, else the key found by its sound)
        data = new[k][2] if k in new and new[k][2] else None
        if data and k not in (name, RENAMED.get(name)):   # found by its sound: kept only if as loud as the old one (else it was another sound)
            import numpy as np
            a_, b_ = pcm(old[off:off + ln]), pcm(data)
            ra = float(np.sqrt((a_ ** 2).mean())) if len(a_) else 0; rb = float(np.sqrt((b_ ** 2).mean())) if len(b_) else 0
            if not rb or not (0.75 < ra / rb < 1.33): data = None
        if data: hd += 1
        else: data = old[off:off + ln]; kept.append(name)
        pack[name] = [len(out), len(data)]; out += data
    open(f'{ROOT}/game/assets/audio/sfx_pack.mp3', 'wb').write(out)
    snd['pack'] = pack
    json.dump(snd, open(sp, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(f'pack: {hd} sounds taken from the new client (its own MP3 data: no re-encoding; 11 of them better than in 1.41.9), {len(kept)} kept from the old pack ({", ".join(kept[:12])}{"…" if len(kept) > 12 else ""}), {len(old) // 1024} -> {len(out) // 1024} KB')


def build_music(names):
    mus = sounds_of(os.path.join(NEW, 'audio', 'musics.swf'))
    for n in names:
        k = next((x for x in (n, n + '.mp3') if x in mus), None) or next((x for x in mus if x.lower() in (n.lower(), n.lower() + '.mp3')), None)
        if not k or not mus[k][2]: print('missing', n, '(exports:', ', '.join(sorted(mus)[:60]), ')'); continue
        open(f'{ROOT}/game/assets/audio/music/{n}.mp3', 'wb').write(mus[k][2]); print('music', n, len(mus[k][2]) // 1024, 'KB', mus[k][1], 'Hz')


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == 'music': build_music(sys.argv[2].split(','))
    else: build_pack()
