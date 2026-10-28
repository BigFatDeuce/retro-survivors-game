"""Dofus Retro lang files (AS2 SWFs that build plain objects) -> JSON, with a tiny AS2 interpreter.
usage: lang2json.py <swf dir> <out dir>  (keeps the newest version of every <kind>_<lang>)"""
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))   # tools/ (its folders: _root)
from _root import ROOT
import sys, os, re, json, struct
import swflib as S


class Undef: pass
UNDEF = None


def to_key(k):
    if isinstance(k, float) and k.is_integer(): k = int(k)
    return str(k)


def run_actions(b, G):
    stack = []; pool = []; regs = [None] * 256; p = 0; n = len(b)
    def pop():
        return stack.pop() if stack else None
    while p < n:
        code = b[p]; p += 1
        if code == 0: break
        ln = 0
        if code >= 0x80:
            ln = struct.unpack_from('<H', b, p)[0]; p += 2
        data = b[p:p + ln]; p += ln
        if code == 0x88:
            r = S.BitReader(data); k = r.u16(); pool = [r.string() for _ in range(k)]
        elif code == 0x96:
            r = S.BitReader(data)
            while r.p < len(data):
                t = r.u8()
                if t == 0: stack.append(r.string())
                elif t == 1: stack.append(struct.unpack_from('<f', data, r.p)[0]); r.p += 4
                elif t in (2, 3): stack.append(None)
                elif t == 4: stack.append(regs[r.u8()])
                elif t == 5: stack.append(bool(r.u8()))
                elif t == 6:
                    raw = data[r.p:r.p + 8]; r.p += 8; stack.append(struct.unpack('<d', raw[4:] + raw[:4])[0])
                elif t == 7: stack.append(struct.unpack_from('<i', data, r.p)[0]); r.p += 4
                elif t == 8: stack.append(pool[r.u8()])
                elif t == 9: stack.append(pool[r.u16()])
        elif code == 0x87: regs[data[0]] = stack[-1] if stack else None   # StoreRegister
        elif code == 0x17: pop()
        elif code == 0x4C: stack.append(stack[-1] if stack else None)
        elif code == 0x4D: a = pop(); b2 = pop(); stack.append(a); stack.append(b2)   # swap
        elif code == 0x1C: name = pop(); stack.append(G.get(name))
        elif code == 0x1D: v = pop(); name = pop(); G[name] = v
        elif code == 0x3C: v = pop(); name = pop(); G[name] = v
        elif code == 0x41: name = pop(); G.setdefault(name, None)
        elif code == 0x4E:
            k = pop(); o = pop()
            if isinstance(o, dict): stack.append(o.get(to_key(k)))
            elif isinstance(o, list):
                try: stack.append(o[int(k)])
                except Exception: stack.append(None)
            else: stack.append(None)
        elif code == 0x4F:
            v = pop(); k = pop(); o = pop()
            if isinstance(o, dict): o[to_key(k)] = v
            elif isinstance(o, list):
                try:
                    i = int(k)
                    while len(o) <= i: o.append(None)
                    o[i] = v
                except Exception: pass
        elif code == 0x43:  # InitObject
            cnt = int(pop() or 0); o = {}
            for _ in range(cnt):
                v = pop(); k = pop(); o[to_key(k)] = v
            stack.append(o)
        elif code == 0x42:  # InitArray
            cnt = int(pop() or 0); stack.append([pop() for _ in range(cnt)])
        elif code == 0x40:  # NewObject
            name = pop(); cnt = int(pop() or 0); args = [pop() for _ in range(cnt)]
            stack.append([] if name == 'Array' else {})
        elif code == 0x53:  # NewMethod
            name = pop(); obj = pop(); cnt = int(pop() or 0); [pop() for _ in range(cnt)]; stack.append({})
        elif code == 0x3D:  # CallFunction
            name = pop(); cnt = int(pop() or 0); [pop() for _ in range(cnt)]; stack.append(None)
        elif code == 0x52:  # CallMethod
            name = pop(); obj = pop(); cnt = int(pop() or 0); [pop() for _ in range(cnt)]; stack.append(None)
        elif code in (0x0A, 0x47):
            a = pop(); b2 = pop()
            try: stack.append(b2 + a)
            except Exception: stack.append(str(b2) + str(a))
        elif code == 0x0B: a = pop(); b2 = pop(); stack.append((b2 or 0) - (a or 0))
        elif code == 0x0C: a = pop(); b2 = pop(); stack.append((b2 or 0) * (a or 0))
        elif code == 0x0D: a = pop(); b2 = pop(); stack.append((b2 or 0) / a if a else 0)
        elif code == 0x12: a = pop(); stack.append(not a)
        elif code == 0x99: off = struct.unpack('<h', data)[0]; p += off       # jump
        elif code == 0x9D:
            off = struct.unpack('<h', data)[0]
            if pop(): p += off
        elif code == 0x9B:  # DefineFunction: skip its body
            r = S.BitReader(data); r.string(); k = r.u16()
            for _ in range(k): r.string()
            size = r.u16(); p += size
        elif code == 0x8E:
            r = S.BitReader(data); r.string(); k = r.u16(); r.u8(); r.u16()
            for _ in range(k): r.u8(); r.string()
            size = r.u16(); p += size
        else:
            pass
    return G


def convert(path):
    sw = S.read_swf(path); G = {}
    def walk(tags):
        for t in tags:
            if t.code == S.T_DOACTION: run_actions(t.data, G)
            elif t.code == S.T_DOINIT: run_actions(t.data[2:], G)
            elif t.code == S.T_SPRITE: walk(t.sub)
    walk(sw['tags'])
    return G


def main(src, out):
    os.makedirs(out, exist_ok=True)
    best = {}
    for f in os.listdir(src):
        m = re.match(r'([a-z]+)_([a-z]{2})_(\d+)\.swf$', f)
        if not m: continue
        k = (m.group(1), m.group(2)); v = int(m.group(3))
        if k not in best or v > best[k][0]: best[k] = (v, f)
    for (kind, lg), (v, f) in sorted(best.items()):
        try:
            G = convert(os.path.join(src, f))
            json.dump(G, open(f'{out}/{kind}_{lg}.json', 'w'), ensure_ascii=False)
            print(kind, lg, v, len(json.dumps(G)) // 1024, 'KB', list(G)[:6], flush=True)
        except Exception as e:
            print('FAIL', f, e, flush=True)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
