# -*- coding: utf-8 -*-
"""Verify every Hangul syllable used in the AOC mod files exists in the shipped fonts:
PUK font (res_lang_pk e16) for PUK packs, base font (res_lang e6) for base packs."""
import sys, os, glob, struct, re
sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
from n16_reader import n16_unwrap, read_section_strings
import numpy as np, lz4.block

def kt_dec(b):
    dec = struct.unpack_from('<Q', b, 8)[0]; comp = struct.unpack_from('<Q', b, 16)[0]
    return lz4.block.decompress(b[24:24+comp], uncompressed_size=dec)

def charmap(font_path, entry):
    d = open(font_path, 'rb').read()
    o, s = struct.unpack_from('<II', d, 16 + entry*8)
    g = kt_dec(d[o:o+s])
    secs = list(struct.unpack_from('<3I', g, 0x20))
    return np.frombuffer(g, dtype='<u2', count=65536, offset=secs[0])

PUK_FONT = charmap(r'D:\nsw\rom\nobu16_powerupkit\puk_mod\atmosphere\contents\01007ab012872001\romfs\RES_JP_PK\res_lang_pk.bin', 16)
BASE_FONT = charmap(r'D:\nsw\rom\nobu16_powerupkit\patch_build\romfs\RES_JP\res_lang.bin', 6)

OUT = r'D:\nsw\rom\nobu16_powerupkit\puk_mod_aoc\atmosphere\contents'
HANGUL = re.compile(r'[가-힣]')
PUK_TIDS = {'01007ab012873009', '01007ab01287300a', '01007ab01287300b', '01007ab01287300e', '01007ab01287300f'}

problems = 0
for tid_dir in sorted(glob.glob(os.path.join(OUT, '*'))):
    tid = os.path.basename(tid_dir)
    font = PUK_FONT if tid in PUK_TIDS else BASE_FONT
    chars = set()
    for f in glob.glob(os.path.join(tid_dir, 'romfs', 'JP', '*.n16')):
        hdr, dec, _ = n16_unwrap(open(f, 'rb').read())
        for s in read_section_strings(dec, 0, len(dec)):
            chars.update(c for c in s if HANGUL.match(c))
    missing = [c for c in sorted(chars) if not font[ord(c)]]
    print(f'{tid}: {len(chars)} hangul chars, missing from font: {missing if missing else 0}')
    problems += len(missing)
print('FONT CHECK', 'PASS' if problems == 0 else f'FAIL ({problems})')
