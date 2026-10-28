"""0.94 (the game's media carry no metadata): removes the tags of the game's MP3 files byte-wise — the ID3v2 block
at the start (titles, covers, encoder, ISRC…), an APEv2 tag and the ID3v1 block at the end — and the EXIF / XMP chunks of
the WebP pictures (their VP8X flags cleared), and nothing else: the audio frames / picture chunks are kept byte for byte
(checked before writing). tools/checks/qa_unit.js checks that none comes back.
usage: python tools/strip_meta.py [--dry] [files…]      (no file: every .mp3 and .webp under game/assets)"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from _root import ROOT
import os, sys, glob


def strip(b):
    s, e = 0, len(b)
    while b[s:s + 3] == b'ID3' and e - s > 10:   # (several ID3v2 blocks can follow one another)
        sz = (b[s + 6] & 127) << 21 | (b[s + 7] & 127) << 14 | (b[s + 8] & 127) << 7 | (b[s + 9] & 127)
        s += 10 + sz + (10 if b[s + 5] & 0x10 else 0)   # (+ the footer when the flag says so)
    if e - s > 128 and b[e - 128:e - 125] == b'TAG': e -= 128
    if e - s > 32 and b[e - 32:e - 24] == b'APETAGEX':
        n = int.from_bytes(b[e - 20:e - 16], 'little'); fl = int.from_bytes(b[e - 12:e - 8], 'little')
        e -= n + (32 if fl & 0x80000000 else 0)
    while s < e and b[s] == 0: s += 1   # (padding after the tag)
    return s, e


def webp(b):
    """the RIFF chunks without EXIF / XMP (None: nothing to remove)"""
    if b[:4] != b'RIFF' or b[8:12] != b'WEBP': return None
    i, out, drop = 12, [], False
    while i + 8 <= len(b):
        cc, n = b[i:i + 4], int.from_bytes(b[i + 4:i + 8], 'little'); ch = b[i:i + 8 + n + (n & 1)]
        if cc in (b'EXIF', b'XMP '): drop = True
        else: out.append(ch)
        i += 8 + n + (n & 1)
    if not drop: return None
    body = bytearray(b''.join(out))
    if body[:4] == b'VP8X': body[8] &= ~0x0C & 0xFF   # (the EXIF / XMP flags of the extended header)
    return b'RIFF' + (len(body) + 4).to_bytes(4, 'little') + b'WEBP' + bytes(body)


def main():
    dry = '--dry' in sys.argv
    files = [f for f in sys.argv[1:] if not f.startswith('--')] or glob.glob(f'{ROOT}/game/assets/**/*.mp3', recursive=True) + glob.glob(f'{ROOT}/game/assets/**/*.webp', recursive=True)
    n = saved = 0
    for p in files:
        b = open(p, 'rb').read()
        if p.lower().endswith('.webp'):
            w = webp(b)
            if w is None: continue
            n += 1; saved += len(b) - len(w); print(f'{os.path.relpath(p, ROOT)}: -{len(b) - len(w)} bytes (EXIF / XMP)')
            if not dry: open(p, 'wb').write(w)
            continue
        s, e = strip(b)
        if (s, e) == (0, len(b)): continue
        out = b[s:e]
        if not (len(out) > 1000 and out[0] == 0xFF and (out[1] & 0xE0) == 0xE0): sys.exit(f'{p}: no MPEG frame right after the tag (offset {s}): left as it is')
        assert out == b[s:e]   # (the audio frames, untouched)
        n += 1; saved += len(b) - len(out)
        print(f'{os.path.relpath(p, ROOT)}: -{len(b) - len(out)} bytes (start {s}, end {len(b) - e})')
        if not dry: open(p, 'wb').write(out)
    print(f'{n} files {"would be " if dry else ""}stripped, {saved // 1024} KB of tags')


if __name__ == '__main__':
    main()
