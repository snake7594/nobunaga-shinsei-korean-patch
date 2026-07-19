# -*- coding: utf-8 -*-
"""Apply DLC_PK crossover-character translations to evm_/gm_/scem_/tom_ .n16 files,
validate token preservation, rebuild, and write to the mod output tree."""
import sys, os, re, glob, shutil
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'.')
from n16_reader import n16_unwrap, n16_wrap, read_section_strings, build_section
import dlc_translations as T

SRC = os.environ.get('DLC_PK_SRC') or r'D:\nsw\rom\1.1.5\Program 1\romfs\DLC_PK\JP'
OUT = os.environ.get('DLC_PK_OUT') or r'D:\nsw\rom\nobu16_powerupkit\puk_mod\atmosphere\contents\01007ab012872001\romfs\DLC_PK\JP'
os.makedirs(OUT, exist_ok=True)

TOKEN_RE = re.compile(r'<ESC>..|<[0-9A-F]{2}>|\\n|\\t|%[sd0-9]')
def norm_tokens(s):
    return Counter(TOKEN_RE.findall(s))

ALL = {}
ALL.update(T.GM); ALL.update(T.TOM); ALL.update(T.SCEM); ALL.update(T.EVM)

total_changed = 0
for f in sorted(glob.glob(os.path.join(SRC, '*.n16'))):
    name = os.path.splitext(os.path.basename(f))[0]
    d = open(f, 'rb').read()
    hdr, dec, was_comp = n16_unwrap(d)
    if len(dec) < 4 or int.from_bytes(dec[:4], 'little') != 0x134C58:
        shutil.copy2(f, os.path.join(OUT, os.path.basename(f)))
        continue  # not a string-table n16 (e.g. non-JP-text files, if any slip through)
    strs = read_section_strings(dec, 0, len(dec))
    tr = ALL.get(name, {})
    changed = 0
    new_strs = list(strs)
    for idx, ko in tr.items():
        orig = strs[idx]
        ot, kt = norm_tokens(orig), norm_tokens(ko)
        if ot != kt:
            print(f'MISMATCH {name}[{idx}]')
            print('  orig:', repr(orig))
            print('  ko  :', repr(ko))
            print('  orig tokens:', ot)
            print('  ko   tokens:', kt)
            continue
        new_strs[idx] = ko
        changed += 1
    total_changed += changed
    dec2 = build_section(new_strs)
    # round-trip check
    check = read_section_strings(dec2, 0, len(dec2))
    assert check == new_strs, f'{name} round-trip mismatch'
    out_blob = n16_wrap(hdr, dec2, was_comp)
    open(os.path.join(OUT, os.path.basename(f)), 'wb').write(out_blob)
    print(f'{name}: {len(strs)} strings, {changed} translated, {len(d)} -> {len(out_blob)} bytes')

print(f'\nTOTAL translated: {total_changed}')

# copy any remaining DLC_PK/JP files untouched (n16 files this pass didn't target, if any)
for f in glob.glob(os.path.join(SRC, '*')):
    dst = os.path.join(OUT, os.path.basename(f))
    if not os.path.isfile(dst):
        shutil.copy2(f, dst)
        print('copied unchanged:', os.path.basename(f))
