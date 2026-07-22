# -*- coding: utf-8 -*-
"""Rebuild MSG_PK against the 1.1.7 extracted source, using the merged dict
(big_dict.json = all existing KO + new117 translations). Output to the 1.1.7 mod tree."""
import os, sys, struct, shutil, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import apply_translations as A

PK_IN = r'D:\nsw\rom\1.1.7\extract\Program 1\romfs\MSG_PK\JP'
OUT   = r'D:\nsw\rom\nobu16_powerupkit\puk_mod_117\atmosphere\contents\01007ab012872001\romfs\MSG_PK\JP'
os.makedirs(OUT, exist_ok=True)

tr = json.load(open(os.path.join(os.path.dirname(__file__), 'tr_all_117.json'), encoding='utf-8'))
print('dict entries:', len(tr))

STR_FILES  = ['msgdata.bin', 'msgev.bin', 'msgui.bin', 'msgbre.bin', 'msgire.bin']
PASS_FILES = ['msgstf.bin', 'msgstf_ce.bin']   # credits — passthrough per policy

used = [0]
for f in STR_FILES:
    hdr, dec = A.kt_unwrap(open(os.path.join(PK_IN, f), 'rb').read())
    secs = A.read_strtable_raw(dec)
    secs = [[A.translate_str(s, tr, used) for s in sec] for sec in secs]
    dec2 = A.build_strtable(secs)
    open(os.path.join(OUT, f), 'wb').write(A.kt_wrap(hdr, dec2))
    print(f'  {f:16} {len(dec):,} -> {len(dec2):,}')
for f in PASS_FILES:
    src = os.path.join(PK_IN, f)
    if os.path.isfile(src):
        shutil.copy2(src, os.path.join(OUT, f))
        print(f'  {f:16} passthrough')
hdr, dec = A.kt_unwrap(open(os.path.join(PK_IN, 'msggame.bin'), 'rb').read())
dec2 = A.rebuild_msggame(dec, tr, used)
open(os.path.join(OUT, 'msggame.bin'), 'wb').write(A.kt_wrap(hdr, dec2))
print(f'  msggame.bin      {len(dec):,} -> {len(dec2):,}')
print('translated in-place:', used[0])

# report untranslated JP that slipped through (should be only yomigana/dummy)
import re
JPCH = re.compile(r'[ぁ-ゖァ-ヺ一-鿿々]')
KANA = re.compile(r'^[ぁ-ゖ]+$|^[ァ-ヺー]+$')
miss = set()
for f in STR_FILES:
    hdr, dec = A.kt_unwrap(open(os.path.join(OUT, f), 'rb').read())
    for sec in A.read_strtable_raw(dec):
        for s in sec:
            if JPCH.search(s) and not KANA.match(s):
                miss.add(s)
print('residual JP (non-yomigana) in built string tables:', len(miss))
for s in sorted(miss, key=len)[:20]:
    print('   ', repr(s[:50]))
