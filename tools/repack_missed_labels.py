# -*- coding: utf-8 -*-
"""Repack res_lang.bin with the two additionally-localized textures (e5 tex1, e8 tex0)."""
import sys, os
sys.path.insert(0,'.'); import koloc
import numpy as np
from PIL import Image
sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))

BASE = os.environ.get('RES_LANG_SRC') or r'D:\nsw\rom\nobu16_powerupkit\patch_build\romfs\RES_JP\res_lang.bin'
OUT  = BASE  # in place

def load(p): return np.array(Image.open(p).convert('RGBA'))

repl = {
    5: {1: load(os.path.join(SP, 'e5_t1_extra_ko.png'))},
    8: {0: load(os.path.join(SP, 'e8_t0_extra_ko.png'))},
}
o, n = koloc.rebuild_reslang(BASE, OUT, repl)
print(f'res_lang.bin: {o:,} -> {n:,} bytes')

# verify: reparse and confirm the fixed labels are gone from JP + present in KO form
res = open(OUT, 'rb').read()
outer = koloc.outer_entries(res)
print('entries:', len(outer), 'all in-bounds:', all(off+sz<=len(res) for off,sz in outer))
e,coff,child,g = koloc.entry_gt1g(res, 5)
texs = koloc.g1t_textures(g)
print('entry5 tex1 dims:', texs[1]['w'], texs[1]['h'])
e2,coff2,child2,g2 = koloc.entry_gt1g(res, 8)
texs2 = koloc.g1t_textures(g2)
print('entry8 tex0 dims:', texs2[0]['w'], texs2[0]['h'])
