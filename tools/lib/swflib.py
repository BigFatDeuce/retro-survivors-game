"""Minimal SWF reader/writer for the Dofus Retro client files (AS2, SWF <= 8).
Tags keep their raw bytes; DefineSprite tags also get their sub-tags parsed (tag.sub) and are re-serialised from them."""
import struct, zlib

T_END, T_SHOWFRAME, T_SHAPE, T_PLACE, T_REMOVE = 0, 1, 2, 4, 5
T_DOACTION = 12
T_SHAPE2, T_PLACE2, T_REMOVE2, T_SHAPE3 = 22, 26, 28, 32
T_SPRITE = 39
T_FRAMELABEL = 43
T_MORPH = 46
T_EXPORT = 56
T_DOINIT = 59
T_PLACE3 = 70
T_SHAPE4 = 83
T_MORPH2 = 84
SHAPE_CODES = {T_SHAPE, T_SHAPE2, T_SHAPE3, T_SHAPE4, T_MORPH, T_MORPH2}
# definition tags whose first u16 is the character id
DEF_CODES = {2, 6, 7, 10, 11, 13, 14, 20, 21, 22, 32, 33, 34, 35, 36, 37, 39, 46, 48, 60, 62, 75, 83, 84, 87, 88, 90, 91}


class BitReader:
    def __init__(self, data, pos=0):
        self.d = data; self.p = pos; self.bit = 0; self.cur = 0

    def align(self): self.bit = 0

    def ub(self, n):
        v = 0
        for _ in range(n):
            if self.bit == 0:
                self.cur = self.d[self.p]; self.p += 1; self.bit = 8
            self.bit -= 1
            v = (v << 1) | ((self.cur >> self.bit) & 1)
        return v

    def sb(self, n):
        if n == 0: return 0
        v = self.ub(n)
        if v & (1 << (n - 1)): v -= 1 << n
        return v

    def fb(self, n): return self.sb(n) / 65536.0

    def u8(self):
        self.align(); v = self.d[self.p]; self.p += 1; return v

    def u16(self):
        self.align(); v = struct.unpack_from('<H', self.d, self.p)[0]; self.p += 2; return v

    def s16(self):
        self.align(); v = struct.unpack_from('<h', self.d, self.p)[0]; self.p += 2; return v

    def u32(self):
        self.align(); v = struct.unpack_from('<I', self.d, self.p)[0]; self.p += 4; return v

    def string(self):
        self.align(); e = self.d.index(b'\0', self.p); s = self.d[self.p:e]; self.p = e + 1
        try: return s.decode('utf8')
        except UnicodeDecodeError: return s.decode('latin1')

    def rect(self):
        self.align(); n = self.ub(5)
        r = (self.sb(n), self.sb(n), self.sb(n), self.sb(n)); self.align(); return r

    def matrix(self):
        self.align()
        a = d = 1.0; b = c = 0.0
        if self.ub(1):
            n = self.ub(5); a = self.fb(n); d = self.fb(n)
        if self.ub(1):
            n = self.ub(5); b = self.fb(n); c = self.fb(n)
        n = self.ub(5); tx = self.sb(n); ty = self.sb(n)
        self.align()
        return [a, b, c, d, float(tx), float(ty)]

    def cxform(self, alpha):
        self.align()
        add = self.ub(1); mul = self.ub(1); n = self.ub(4)
        k = 4 if alpha else 3
        m = [256] * 4; o = [0] * 4
        if mul:
            for i in range(k): m[i] = self.sb(n)
        if add:
            for i in range(k): o[i] = self.sb(n)
        self.align()
        return (tuple(m), tuple(o))


class BitWriter:
    def __init__(self): self.out = bytearray(); self.cur = 0; self.n = 0

    def ub(self, v, n):
        for i in range(n - 1, -1, -1):
            self.cur = (self.cur << 1) | ((v >> i) & 1); self.n += 1
            if self.n == 8: self.out.append(self.cur); self.cur = 0; self.n = 0

    def sb(self, v, n): self.ub(v & ((1 << n) - 1), n)

    def flush(self):
        if self.n: self.out.append(self.cur << (8 - self.n)); self.cur = 0; self.n = 0
        return bytes(self.out)


def nbits_s(*vals):
    n = 1
    for v in vals:
        v = int(v)
        b = (v if v >= 0 else ~v).bit_length() + 1
        n = max(n, b)
    return n


def write_rect(r):
    w = BitWriter(); n = nbits_s(*r); w.ub(n, 5)
    for v in r: w.sb(int(v), n)
    return w.flush()


def write_matrix(m):
    a, b, c, d, tx, ty = m
    w = BitWriter()
    if a != 1.0 or d != 1.0:
        A, D = int(round(a * 65536)), int(round(d * 65536)); n = nbits_s(A, D)
        w.ub(1, 1); w.ub(n, 5); w.sb(A, n); w.sb(D, n)
    else: w.ub(0, 1)
    if b != 0.0 or c != 0.0:
        B, C = int(round(b * 65536)), int(round(c * 65536)); n = nbits_s(B, C)
        w.ub(1, 1); w.ub(n, 5); w.sb(B, n); w.sb(C, n)
    else: w.ub(0, 1)
    tx, ty = int(round(tx)), int(round(ty))
    n = nbits_s(tx, ty) if (tx or ty) else 0
    w.ub(n, 5)
    if n: w.sb(tx, n); w.sb(ty, n)
    return w.flush()


def write_cxform_alpha(cx):
    (m, o) = cx
    w = BitWriter()
    hasmul = any(v != 256 for v in m); hasadd = any(v != 0 for v in o)
    vals = (list(m) if hasmul else []) + (list(o) if hasadd else [])
    n = nbits_s(*vals) if vals else 1
    w.ub(1 if hasadd else 0, 1); w.ub(1 if hasmul else 0, 1); w.ub(n, 4)
    if hasmul:
        for v in m: w.sb(int(v), n)
    if hasadd:
        for v in o: w.sb(int(v), n)
    return w.flush()


class Tag:
    __slots__ = ('code', 'data', 'sub', 'sprite_id', 'frames')

    def __init__(self, code, data, sub=None):
        self.code = code; self.data = data; self.sub = sub; self.sprite_id = None; self.frames = None
        if code == T_SPRITE:
            self.sprite_id, self.frames = struct.unpack_from('<HH', data, 0)
            if sub is None: self.sub = parse_tags(data, 4)

    @property
    def cid(self):
        return struct.unpack_from('<H', self.data, 0)[0] if self.code in DEF_CODES and len(self.data) >= 2 else None

    def body(self):
        if self.code == T_SPRITE and self.sub is not None:
            nf = sum(1 for t in self.sub if t.code == T_SHOWFRAME)
            return struct.pack('<HH', self.sprite_id, nf) + write_tags(self.sub)
        return self.data

    def __repr__(self): return f'Tag({self.code}, {len(self.data)}b)'


def parse_tags(d, p=0):
    out = []
    while p + 2 <= len(d):
        h = struct.unpack_from('<H', d, p)[0]; p += 2
        code = h >> 6; ln = h & 0x3f
        if ln == 0x3f: ln = struct.unpack_from('<I', d, p)[0]; p += 4
        data = d[p:p + ln]; p += ln
        if code == T_END: break
        out.append(Tag(code, bytes(data)))
    return out


def tag_bytes(code, body, long=False):
    if len(body) >= 0x3f or long or code in (6, 20, 21, 35, 36, 90):
        return struct.pack('<HI', (code << 6) | 0x3f, len(body)) + body
    return struct.pack('<H', (code << 6) | len(body)) + body


def write_tags(tags):
    out = bytearray()
    for t in tags: out += tag_bytes(t.code, t.body())
    out += b'\0\0'
    return bytes(out)


def read_swf(path_or_bytes):
    raw = open(path_or_bytes, 'rb').read() if isinstance(path_or_bytes, str) else path_or_bytes
    sig = raw[:3]; ver = raw[3]
    if sig == b'CWS': body = zlib.decompress(raw[8:])
    elif sig == b'FWS': body = raw[8:]
    elif sig == b'ZWS':
        import lzma
        props = raw[12:17]; body = lzma.LZMADecompressor(lzma.FORMAT_RAW, filters=[lzma._decode_filter_properties(lzma.FILTER_LZMA1, props)]).decompress(raw[17:])
    else: raise ValueError('not a swf')
    r = BitReader(body); rect = r.rect(); p = r.p
    rate = struct.unpack_from('<H', body, p)[0] / 256.0; count = struct.unpack_from('<H', body, p + 2)[0]
    return dict(version=ver, rect=rect, rate=rate, count=count, tags=parse_tags(body, p + 4))


def write_swf(sw, path=None, compress=True):
    nf = sum(1 for t in sw['tags'] if t.code == T_SHOWFRAME)
    body = write_rect(sw['rect']) + struct.pack('<HH', int(round(sw.get('rate', 24) * 256)), nf or 1) + write_tags(sw['tags'])
    ver = max(sw.get('version', 8), 6)
    if compress: raw = b'CWS' + bytes([ver]) + struct.pack('<I', len(body) + 8) + zlib.compress(body, 6)
    else: raw = b'FWS' + bytes([ver]) + struct.pack('<I', len(body) + 8) + body
    if path: open(path, 'wb').write(raw)
    return raw


def defs(tags):
    out = {}
    for t in tags:
        c = t.cid
        if c is not None: out[c] = t
    return out


def exports(tags):
    out = {}
    for t in tags:
        if t.code == T_EXPORT:
            r = BitReader(t.data); n = r.u16()
            for _ in range(n):
                i = r.u16(); out[r.string()] = i
    return out


def labels(tags):
    """frame labels of a timeline: {label: frame index}"""
    out = {}; fi = 0
    for t in tags:
        if t.code == T_FRAMELABEL: out[BitReader(t.data).string()] = fi
        elif t.code == T_SHOWFRAME: fi += 1
    return out


def parse_place(tag):
    r = BitReader(tag.data)
    if tag.code == T_PLACE:
        out = dict(char=r.u16(), depth=r.u16()); out['matrix'] = r.matrix()
        if r.p < len(tag.data): out['cx'] = r.cxform(False)
        return out
    f = r.u8(); f2 = r.u8() if tag.code == T_PLACE3 else 0
    out = dict(depth=r.u16(), move=bool(f & 1))
    if tag.code == T_PLACE3 and (f2 & 8 or (f2 & 16 and f & 2)): out['class'] = r.string()
    if f & 2: out['char'] = r.u16()
    if f & 4: out['matrix'] = r.matrix()
    if f & 8: out['cx'] = r.cxform(True)
    if f & 16: out['ratio'] = r.u16()
    if f & 32: out['name'] = r.string()
    if f & 64: out['clipdepth'] = r.u16()
    return out


def make_place2(depth, char=None, matrix=None, cx=None, name=None, move=False, clipdepth=None, ratio=None):
    f = (1 if move else 0) | (2 if char is not None else 0) | (4 if matrix is not None else 0) | (8 if cx is not None else 0) | \
        (16 if ratio is not None else 0) | (32 if name is not None else 0) | (64 if clipdepth is not None else 0)
    b = bytes([f]) + struct.pack('<H', depth)
    if char is not None: b += struct.pack('<H', char)
    if matrix is not None: b += write_matrix(matrix)
    if cx is not None: b += write_cxform_alpha(cx)
    if ratio is not None: b += struct.pack('<H', ratio)
    if name is not None: b += name.encode('utf8') + b'\0'
    if clipdepth is not None: b += struct.pack('<H', clipdepth)
    return Tag(T_PLACE2, b)


def shape_bounds(tag):
    r = BitReader(tag.data, 2); x0, x1, y0, y1 = r.rect()
    if tag.code in (T_MORPH, T_MORPH2):   # morph shapes: start and end bounds
        a0, a1, b0, b1 = r.rect(); return (min(x0, a0), max(x1, a1), min(y0, b0), max(y1, b1))
    return (x0, x1, y0, y1)


def scripts_of(tags):
    """{frame index: [action bytes]} for DoAction tags of a timeline"""
    out = {}; fi = 0
    for t in tags:
        if t.code == T_DOACTION: out.setdefault(fi, []).append(t.data)
        elif t.code == T_SHOWFRAME: fi += 1
    return out


OPS = {0x04: 'nextFrame', 0x05: 'prevFrame', 0x06: 'play', 0x07: 'stop', 0x81: 'gotoFrame', 0x8c: 'goToLabel', 0x9f: 'gotoFrame2'}


def action_strings(b):
    """flat token list of an AS2 action block: pushed values ('s', str) / ('n', number) / ('r', reg) / ('b', bool) / ('u', None)
    and a few timeline ops ('op', name). Function bodies are walked inline."""
    toks = []; pool = []; p = 0; n = len(b)
    while p < n:
        code = b[p]; p += 1
        if code == 0: continue
        ln = 0
        if code >= 0x80:
            if p + 2 > n: break
            ln = struct.unpack_from('<H', b, p)[0]; p += 2
        data = b[p:p + ln]; p += ln
        if code == 0x88:   # constant pool
            r = BitReader(data); k = r.u16(); pool = [r.string() for _ in range(k)]
        elif code == 0x96:  # push
            r = BitReader(data)
            while r.p < len(data):
                t = r.u8()
                if t == 0: toks.append(('s', r.string()))
                elif t == 1: toks.append(('n', struct.unpack_from('<f', data, r.p)[0])); r.p += 4
                elif t == 2: toks.append(('u', None))
                elif t == 3: toks.append(('u', None))
                elif t == 4: toks.append(('r', r.u8()))
                elif t == 5: toks.append(('b', bool(r.u8())))
                elif t == 6:
                    raw = data[r.p:r.p + 8]; r.p += 8
                    toks.append(('n', struct.unpack('<d', raw[4:] + raw[:4])[0]))
                elif t == 7: toks.append(('n', struct.unpack_from('<i', data, r.p)[0])); r.p += 4
                elif t == 8:
                    i = r.u8(); toks.append(('s', pool[i] if i < len(pool) else None))
                elif t == 9:
                    i = r.u16(); toks.append(('s', pool[i] if i < len(pool) else None))
                else: break
        elif code == 0x8c:
            toks.append(('op', 'goToLabel')); toks.append(('s', BitReader(data).string()))
        elif code in OPS:
            toks.append(('op', OPS[code]))
        elif code == 0x9b or code == 0x8e:   # function bodies are inline: nothing to do (the body follows)
            pass
    return toks


# ---------------------------------------------------------------- shape styles (in-place patching of line widths)
def _skip_fillstyles(r, shape_ver, bits=None):
    n = r.u8()
    if n == 0xff: n = r.u16()
    for _ in range(n):
        t = r.u8()
        if t == 0x00: r.p += 4 if shape_ver >= 3 else 3
        elif t in (0x10, 0x12, 0x13):
            r.matrix(); r.align()
            g = r.u8(); k = g & 0x0f
            r.p += k * (5 if shape_ver >= 3 else 4)
            if t == 0x13: r.p += 2
        elif t in (0x40, 0x41, 0x42, 0x43):
            b = r.u16(); r.matrix(); r.align()
            if bits is not None: bits.append(b)


def _linestyles(r, shape_ver, out):
    n = r.u8()
    if n == 0xff: n = r.u16()
    for _ in range(n):
        if shape_ver == 4:
            pos = r.p; w = r.u16(); f1 = r.u8(); f2 = r.u8()
            join = (f1 >> 4) & 3 if False else (f1 & 0x30) >> 4
            if join == 2: r.u16()
            if f1 & 0x08: _skip_fillstyles_single(r, shape_ver); out.append((pos, w, None))
            else: col = tuple(r.d[r.p:r.p + 4]); r.p += 4; out.append((pos, w, col))
        else:
            pos = r.p; w = r.u16(); k = 4 if shape_ver >= 3 else 3
            col = tuple(r.d[r.p:r.p + k]); r.p += k; out.append((pos, w, col))
    return n


def _skip_fillstyles_single(r, shape_ver):
    t = r.u8()
    if t == 0x00: r.p += 4
    elif t in (0x10, 0x12, 0x13):
        r.matrix(); r.align(); g = r.u8(); r.p += (g & 0x0f) * 5
        if t == 0x13: r.p += 2
    elif t in (0x40, 0x41, 0x42, 0x43): r.u16(); r.matrix(); r.align()


def line_styles(tag, bits=None):
    """[(byte offset of the width, width twips, colour)] of every line style of a DefineShape (initial + new styles);
    bits: a list that receives the ids of the bitmaps used by its fills"""
    ver = {T_SHAPE: 1, T_SHAPE2: 2, T_SHAPE3: 3, T_SHAPE4: 4}[tag.code]
    r = BitReader(tag.data, 2); r.rect()
    if ver == 4: r.rect(); r.u8()
    out = []
    _skip_fillstyles(r, ver, bits); _linestyles(r, ver, out)
    r.align(); nf = r.ub(4); nl = r.ub(4)
    while True:
        if r.ub(1) == 0:
            fl = r.ub(5)
            if fl == 0: break
            if fl & 1:
                n = r.ub(5); r.sb(n); r.sb(n)
            if fl & 2: r.ub(nf)
            if fl & 4: r.ub(nf)
            if fl & 8: r.ub(nl)
            if fl & 16:
                _skip_fillstyles(r, ver, bits); _linestyles(r, ver, out); r.align(); nf = r.ub(4); nl = r.ub(4)
        else:
            if r.ub(1):  # straight
                n = r.ub(4) + 2
                if r.ub(1): r.sb(n); r.sb(n)
                else: r.ub(1); r.sb(n)
            else:
                n = r.ub(4) + 2; r.sb(n); r.sb(n); r.sb(n); r.sb(n)
    return out


def scale_lines(tag, factor, pred=lambda w, col: True, minw=0):
    """returns a copy of a shape tag whose line widths are multiplied (in place, same byte size)"""
    d = bytearray(tag.data)
    for pos, w, col in line_styles(tag):
        if pred(w, col):
            nw = min(65535, max(minw, int(round(w * factor))))
            struct.pack_into('<H', d, pos, nw)
    return Tag(tag.code, bytes(d))


BITMAP_CODES = {6, 20, 21, 35, 36, 90}
FONT_CODES = {10, 48, 75}


def deps(tags, root_ids):
    """the character ids a set of characters needs (sprites -> placed characters, shapes -> fill bitmaps,
    texts -> every font); used to write small SWFs holding only what one symbol draws"""
    D = defs(tags); need = set(); todo = list(root_ids); fonts = False
    while todo:
        c = todo.pop()
        if c in need or c not in D: continue
        need.add(c); t = D[c]
        if t.code == T_SPRITE:
            for x in t.sub:
                if x.code in (T_PLACE, T_PLACE2, T_PLACE3):
                    p = parse_place(x)
                    if 'char' in p: todo.append(p['char'])
        elif t.code in (T_SHAPE, T_SHAPE2, T_SHAPE3, T_SHAPE4):
            b = []
            try: line_styles(t, b)
            except Exception: b = [k for k, v in D.items() if v.code in BITMAP_CODES]
            todo += b
        elif t.code in (T_MORPH, T_MORPH2):
            todo += [k for k, v in D.items() if v.code in BITMAP_CODES]
        elif t.code in (11, 33, 37): fonts = True
        elif t.code in (7, 34): todo += [k for k, v in D.items() if v.code not in BITMAP_CODES]
    if fonts: need |= {k for k, v in D.items() if v.code in FONT_CODES}
    return need
