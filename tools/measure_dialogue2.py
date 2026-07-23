# -*- coding: utf-8 -*-
"""Re-measure with box=960; cover msgev (scenario) + msggame (in-game dialogue).
Report Korean dialogue strings whose \\n-segments overflow the real box, i.e. lines that
run off the right edge (the visible overflow the user reports)."""
import struct, os, re, sys
import numpy as np, lz4.block
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import apply_translations as A

def kt_dec(b):
    dec = struct.unpack_from('<Q', b, 8)[0]; comp = struct.unpack_from('<Q', b, 16)[0]
    return lz4.block.decompress(b[24:24+comp], uncompressed_size=dec)
FONT = r'D:\nsw\rom\nobu16_powerupkit\puk_mod_117\atmosphere\contents\01007ab012872001\romfs\RES_JP_PK\res_lang_pk.bin'
d = open(FONT, 'rb').read(); o, s = struct.unpack_from('<II', d, 16 + 16*8); g = kt_dec(d[o:o+s])
secs = list(struct.unpack_from('<3I', g, 0x20))
cm0 = np.frombuffer(g, dtype='<u2', count=65536, offset=secs[0]); rec0 = secs[0] + 0x20000
ADV = {cp: g[rec0 + int(cm0[cp])*12 + 4] for cp in range(0x10000) if int(cm0[cp])}
ESC = re.compile(r'<ESC>C.'); PLACE = re.compile(r'\[[a-z]+\d+\]')
def seg_w(seg):
    st = ESC.sub('', seg).replace('\\t', '')
    w = sum(ADV.get(ord(c), 48) for c in st)
    for m in PLACE.finditer(st):
        w += max(0, 390 - sum(ADV.get(ord(c), 48) for c in m.group(0)))
    return w

BOX = 960
KO_ROOT = r'D:\nsw\rom\nobu16_powerupkit\puk_mod_117\atmosphere\contents\01007ab012872001\romfs\MSG_PK\JP'
KANA = re.compile(r'[ぁ-ゖァ-ヺ]')
def strtable_strings(path):
    _, dec = A.kt_unwrap(open(path, 'rb').read())
    return [s for sec in A.read_strtable_raw(dec) for s in sec]
def msggame_runs(path):
    _, dec = A.kt_unwrap(open(path, 'rb').read())
    cnt = struct.unpack_from('<I', dec, 0)[0]; out = []
    for i in range(cnt):
        off, size = struct.unpack_from('<II', dec, 4 + i*8)
        n = struct.unpack_from('<I', dec, off)[0]
        offs = struct.unpack_from(f'<{n}I', dec, off+4); ends = list(offs[1:]) + [size]
        for j in range(n):
            blob = dec[off+offs[j]:off+ends[j]]; p = 0
            while True:
                a = blob.find(b'\x07\x07\x01', p)
                if a < 0: break
                b_ = blob.find(b'\x07\x07\x02', a+3)
                if b_ < 0: break
                raw = blob[a+3:b_]
                if len(raw) % 2 == 0 and raw:
                    out.append(A.esc(struct.unpack_from(f'<{len(raw)//2}H', raw)))
                p = b_ + 3
    return out

for label, strs in [('msgev', strtable_strings(os.path.join(KO_ROOT, 'msgev.bin'))),
                    ('msgdata', strtable_strings(os.path.join(KO_ROOT, 'msgdata.bin'))),
                    ('msggame', msggame_runs(os.path.join(KO_ROOT, 'msggame.bin')))]:
    over = []
    n_nl = 0
    for t in strs:
        if '\\n' not in t:
            continue
        n_nl += 1
        wide = [(seg_w(p), p) for p in t.split('\\n') if seg_w(p) > BOX]
        if wide:
            over.append((max(w for w, _ in wide), t))
    over.sort(reverse=True)
    print(f'== {label}: strings with \\n={n_nl}, with a segment > box({BOX}): {len(over)}')
    for w, t in over[:6]:
        segs = [f'{seg_w(p)}' for p in t.split('\\n')]
        print(f'   maxseg={w}u  segwidths={segs}  {t[:54]!r}')
