# -*- coding: utf-8 -*-
"""Apply the same dialogue-overflow fix used for the base game's ev_strdata.bin to the
PUK's msgev.bin: strip manual \\n line breaks from segments wider than the dialogue box,
so the engine re-wraps them itself instead of overflowing past 3 lines.

Uses the advance table from the freshly re-tightened PK font (res_lang_pk.bin entry 16,
section 0) -- must run puk_font_tighten.py first."""
import struct, os, re, sys
import numpy as np, lz4.block
sys.stdout.reconfigure(encoding='utf-8')
import apply_translations as A

def kt_dec(b):
    dec=struct.unpack_from('<Q',b,8)[0]; comp=struct.unpack_from('<Q',b,16)[0]
    return lz4.block.decompress(b[24:24+comp],uncompressed_size=dec)

FONT = os.environ.get('PK_RES_OUT') or r'D:\nsw\rom\nobu16_powerupkit\puk_mod\atmosphere\contents\01007ab012872001\romfs\RES_JP_PK\res_lang_pk.bin'
OUT = os.environ.get('PK_MSG_OUT') or r'D:\nsw\rom\nobu16_powerupkit\puk_mod\atmosphere\contents\01007ab012872001\romfs\MSG_PK\JP'

d=open(FONT,'rb').read()
o,s=struct.unpack_from('<II',d,16+16*8)
g=kt_dec(d[o:o+s])
secs=list(struct.unpack_from('<3I',g,0x20))
cm0=np.frombuffer(g,dtype='<u2',count=65536,offset=secs[0]); rec0=secs[0]+0x20000
ADV={}
for cp in range(0x10000):
    gid=int(cm0[cp])
    if gid: ADV[cp]=g[rec0+gid*12+4]
print('adv table:', len(ADV), 'glyphs | 가:',ADV.get(0xAC00),'space:',ADV.get(0x20))

W_STRIP=1000
PLACE=re.compile(r'\[[a-z]+\d+\]')
ESC_TAG=re.compile(r'<ESC>C.')

def seg_width(seg):
    # zero-width control tags (escaped form of ESC+'C'+colorchar)
    stripped = ESC_TAG.sub('', seg)
    stripped = stripped.replace('\\t', '')
    w=0
    for c in stripped:
        w += ADV.get(ord(c), 48)
    for m in PLACE.finditer(stripped):
        lit = sum(ADV.get(ord(c), 48) for c in m.group(0))
        w += max(0, 390 - lit)   # assume substituted name ~10 hangul, same estimate as base game
    return w

path = os.path.join(OUT, 'msgev.bin')
raw = open(path, 'rb').read()
hdr, dec = A.kt_unwrap(raw)
secs_str = A.read_strtable_raw(dec)
n_strip = 0
over = []
new_secs = []
for sec in secs_str:
    ns = []
    for t in sec:
        if '\\n' in t:
            parts = t.split('\\n')
            if any(seg_width(p) > W_STRIP for p in parts):
                t2 = t.replace('\\n', ' ')
                n_strip += 1
                tot = seg_width(t2)
                if tot > 3 * 1056:
                    over.append((tot, t2[:50]))
                t = t2
        ns.append(t)
    new_secs.append(ns)
dec2 = A.build_strtable(new_secs)
open(path, 'wb').write(A.kt_wrap(hdr, dec2))
print(f'msgev.bin: {n_strip} strings had overflow \\n stripped, {len(over)} still >3 lines packed')
for w, t in over[:8]:
    print(f'   {w}u: {t}...')
