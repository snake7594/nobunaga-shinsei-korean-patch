# -*- coding: utf-8 -*-
"""Build AOC LayeredFS mod folders with Korean text:
 - PUK-side new packs from aoc_translations.AOC_TR (3009/300a/300b/300e/300f)
 - base-game crossover packs 3003/3004/3005/3006 reusing dlc_translations by filename
Output: D:\\nsw\\rom\\nobu16_powerupkit\\puk_mod_aoc\\atmosphere\\contents\\<tid>\\romfs\\JP\\*.n16
Token-preservation validated; round-trip checked."""
import sys, os, re, glob
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
from n16_reader import n16_unwrap, n16_wrap, read_section_strings, build_section
from aoc_translations import AOC_TR
import dlc_translations as T

AOC = r'D:\nsw\rom\nobu16_powerupkit\aoc_extract'
OUT = r'D:\nsw\rom\nobu16_powerupkit\puk_mod_aoc\atmosphere\contents'

TOKEN_RE = re.compile(r'<ESC>..|<[0-9A-F]{2}>|\\n|\\t|%[sd0-9]')
def norm_tokens(s):
    return Counter(TOKEN_RE.findall(s))

DLC_BY_NAME = {}
DLC_BY_NAME.update(T.GM); DLC_BY_NAME.update(T.TOM)
DLC_BY_NAME.update(T.SCEM); DLC_BY_NAME.update(T.EVM)

# base-game crossover AOC packs: translate every JP/*.n16 whose basename is in dlc_translations
BASE_PACKS = ['01007ab012873003', '01007ab012873004', '01007ab012873005', '01007ab012873006']

def apply_file(src_path, out_path, tr_map, label):
    d = open(src_path, 'rb').read()
    hdr, dec, was_comp = n16_unwrap(d)
    strs = read_section_strings(dec, 0, len(dec))
    new_strs = list(strs)
    changed = 0
    for idx, ko in tr_map.items():
        orig = strs[idx]
        if norm_tokens(orig) != norm_tokens(ko):
            print(f'TOKEN MISMATCH {label}[{idx}]')
            print('  orig:', repr(orig[:60]))
            print('  ko  :', repr(ko[:60]))
            return 0
        new_strs[idx] = ko
        changed += 1
    dec2 = build_section(new_strs)
    check = read_section_strings(dec2, 0, len(dec2))
    assert check == new_strs, f'{label} round-trip mismatch'
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    open(out_path, 'wb').write(n16_wrap(hdr, dec2, was_comp))
    print(f'{label}: {changed} translated, {len(d)} -> bytes ok')
    return changed

total = 0
# 1) PUK new packs
for tid, files in AOC_TR.items():
    for fname, tr_map in files.items():
        src = os.path.join(AOC, f'romfs_{tid}', 'JP', fname + '.n16')
        dst = os.path.join(OUT, tid, 'romfs', 'JP', fname + '.n16')
        total += apply_file(src, dst, tr_map, f'{tid[-4:]}/{fname}')

# 2) base crossover packs (reuse v3.4 translations by filename)
for tid in BASE_PACKS:
    for src in sorted(glob.glob(os.path.join(AOC, f'romfs_{tid}', 'JP', '*.n16'))):
        name = os.path.splitext(os.path.basename(src))[0]
        tr_map = DLC_BY_NAME.get(name)
        if not tr_map:
            print(f'{tid[-4:]}/{name}: no translation entry (skip)')
            continue
        dst = os.path.join(OUT, tid, 'romfs', 'JP', name + '.n16')
        total += apply_file(src, dst, tr_map, f'{tid[-4:]}/{name}')

print('TOTAL strings translated:', total)
