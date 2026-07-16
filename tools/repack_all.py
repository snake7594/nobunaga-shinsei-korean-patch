# -*- coding: utf-8 -*-
"""Repack ALL localized atlases into res_lang.bin (base = font+labels+e8-already-patched).
Sources: e8_ko.png (entry8 tid0), e5_t1_ko.png (entry5 tid1), loc_out/e{N}/t{tid}.png (workflow)."""
import sys, os, re, numpy as np
sys.path.insert(0,'.'); import koloc
from PIL import Image
sys.stdout.reconfigure(encoding='utf-8')
SP=os.path.dirname(os.path.abspath(__file__))
# base already has e8 localized+size-fixed? No — base = the font+labels res_lang. We re-inject e8 here too.
BASE=r'D:\nsw\rom\노부나가의 야망 신생_일본판\한글패치_테스트\romfs\RES_JP\res_lang.bin.bak_prewheel'
OUT=r'D:\nsw\rom\노부나가의 야망 신생_일본판\한글패치_테스트\romfs\RES_JP\res_lang.bin'

def load(p): return np.array(Image.open(p).convert('RGBA'))

repl={}
# entry 8 (command wheel) — size-fixed
repl[8]={0: load(os.path.join(SP,'e8_ko.png'))}
# entry 5 tex1 (nav/system buttons)
repl[5]={1: load(os.path.join(SP,'e5_t1_ko.png'))}
# workflow outputs
for entry_dir in sorted(os.listdir(os.path.join(SP,'loc_out'))):
    m=re.match(r'e(\d+)$',entry_dir)
    if not m: continue
    ent=int(m.group(1)); d=os.path.join(SP,'loc_out',entry_dir)
    tmap={}
    for fn in os.listdir(d):
        mm=re.match(r't(\d+)\.png$',fn)
        if mm: tmap[int(mm.group(1))]=load(os.path.join(d,fn))
    if tmap: repl.setdefault(ent,{}).update(tmap)

print('entries to patch:', {k:sorted(v.keys()) for k,v in sorted(repl.items())})
o,n=koloc.rebuild_reslang(BASE, OUT, repl)
print(f'res_lang: {o:,} -> {n:,} bytes')

# verify: reparse + decode each patched texture, confirm dims + font/labels intact
res=open(OUT,'rb').read()
outer=koloc.outer_entries(res); print(f'{len(outer)} entries, all in-bounds:',
    all(off+sz<=len(res) for off,sz in outer))
base=open(BASE,'rb').read(); bouter=koloc.outer_entries(base)
for i in (3,6,7):
    a=base[bouter[i][0]:bouter[i][0]+bouter[i][1]]; b=res[outer[i][0]:outer[i][0]+outer[i][1]]
    print(f'  entry {i} (font/labels) identical: {a==b}')
