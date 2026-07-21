# -*- coding: utf-8 -*-
"""Patch res_lang_exp.bin: replace entry3/child0 texture1 (nav-button atlas, identical
to base e5 t1) with the existing Korean atlas e5_t1_ko.png. Verify by re-parsing."""
import sys, os, struct
sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import koloc
import numpy as np
from PIL import Image

SRC = r'D:\nsw\rom\1.1.5\Program 0\romfs\RES_JP\res_lang_exp.bin'
OUT = os.path.join(SP, 'res_lang_exp_ko.bin')

ko = np.array(Image.open(os.path.join(SP, 'e5_t1_ko.png')).convert('RGBA'))
o, n = koloc.rebuild_reslang(SRC, OUT, {3: {1: ko}})
print(f'res_lang_exp: {o:,} -> {n:,} bytes')

# verify: reparse and template-check Korean text present
res = open(OUT, 'rb').read()
e, coff, child, g = koloc.entry_gt1g(res, 3)
texs = koloc.g1t_textures(g)
print('entry3 texs:', [(t['tid'], t['w'], t['h']) for t in texs])
t1 = texs[1]['rgba']
ref = np.array(Image.open(os.path.join(SP, 'e5_t1_ko.png')).convert('RGBA'))
diff = np.abs(t1.astype(int) - ref.astype(int)).mean()
print('t1 vs e5_t1_ko mean-abs-diff (BC3 recompress loss expected, small):', round(diff, 2))
# sanity: all other textures unchanged vs source
src = open(SRC, 'rb').read()
_, _, _, g0 = koloc.entry_gt1g(src, 3)
t0s = koloc.g1t_textures(g0)
same = sum(1 for a, b in zip(t0s, texs) if a['tid'] != 1 and b['rgba'] is not None and a['rgba'] is not None
           and np.array_equal(a['rgba'], b['rgba']))
print('other textures byte-identical rgba:', same, '/ 12 expected')
# outer integrity
pairs = [struct.unpack_from('<II', res, 16 + i*8) for i in range(struct.unpack_from('<I', res, 4)[0])]
print('entries in-bounds:', all(off + sz <= len(res) for off, sz in pairs))
