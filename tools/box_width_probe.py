# -*- coding: utf-8 -*-
"""Distinguish full-width (wrapping) vs nameplate (shrinking) boxes by measuring JP original
per-line pixel width. Designers fit each JP line to its box, so line-width distributions
reveal the box each group of strings targets.
Groups: msgev FLOW-referenced (proven full-width), msgev bands, msggame (nameplate)."""
import struct, os, re, sys
import numpy as np, lz4.block
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import apply_translations as A

def kt_dec(b):
    dec = struct.unpack_from('<Q', b, 8)[0]; comp = struct.unpack_from('<Q', b, 16)[0]
    return lz4.block.decompress(b[24:24+comp], uncompressed_size=dec)

FONT = r'D:\nsw\rom\1.1.7\extract\Program 1\romfs\RES_JP_PK\res_lang_pk.bin'
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
NL = '\\n'
def load(p):
    _, dec = A.kt_unwrap(open(p, 'rb').read())
    return [s for sec in A.read_strtable_raw(dec) for s in sec]
def msggame_runs(p):
    _, dec = A.kt_unwrap(open(p, 'rb').read()); cnt = struct.unpack_from('<I', dec, 0)[0]; out = []
    for i in range(cnt):
        off, size = struct.unpack_from('<II', dec, 4 + i*8)
        n = struct.unpack_from('<I', dec, off)[0]
        offs = struct.unpack_from(f'<{n}I', dec, off+4); ends = list(offs[1:]) + [size]
        for j in range(n):
            blob = dec[off+offs[j]:off+ends[j]]; p2 = 0
            while True:
                a = blob.find(b'\x07\x07\x01', p2)
                if a < 0: break
                b_ = blob.find(b'\x07\x07\x02', a+3)
                if b_ < 0: break
                raw = blob[a+3:b_]
                if len(raw) % 2 == 0 and raw:
                    out.append(A.esc(struct.unpack_from(f'<{len(raw)//2}H', raw)))
                p2 = b_ + 3
    return out

R = r'D:\nsw\rom\1.1.7\extract\Program 1\romfs\MSG_PK\JP'
ev = load(os.path.join(R, 'msgev.bin'))
gm = msggame_runs(os.path.join(R, 'msggame.bin'))

# FLOW-referenced msgev indices
FL = r'D:\nsw\rom\1.1.7\extract\Program 1\romfs\FLOW_PK'
flow_idx = set()
for fn in os.listdir(FL):
    b = open(os.path.join(FL, fn), 'rb').read(); o2 = 0
    while True:
        o2 = b.find(b'\x78\x00\x00\x00', o2)
        if o2 < 0: break
        idx = struct.unpack_from('<I', b, o2+4)[0]
        if 0 <= idx < len(ev): flow_idx.add(idx)
        o2 += 4

def maxline(s):
    return max((seg_w(p) for p in s.split(NL)), default=0)

def stats(name, strings):
    ml = sorted(maxline(s) for s in strings if NL in s)
    if not ml:
        print(f'{name:32s} n=0'); return
    n = len(ml)
    print(f'{name:32s} n={n:5d}  p50={ml[n//2]:4d}  p90={ml[int(n*0.9)]:4d}  p95={ml[int(n*0.95)]:4d}  max={ml[-1]:4d}')

stats('msgev FLOW-ref (proven full-w)', [ev[i] for i in flow_idx])
stats('msgev 2000-4000 (narration)', [ev[i] for i in range(2000,4000)])
stats('msgev 4000-6000', [ev[i] for i in range(4000,6000)])
stats('msgev 6000-9000', [ev[i] for i in range(6000,9000)])
stats('msgev 9000-12000 (dialogue?)', [ev[i] for i in range(9000,12000)])
stats('msggame (nameplate, shrink)', gm)
print(f'\nfont: full-width box ~960u. FLOW-ref & narration should approach box width;')
print(f'nameplate box would cap lower. hangul 가={ADV.get(0xAC00)}, JP kana width varies.')
