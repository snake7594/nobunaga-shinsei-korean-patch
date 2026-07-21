# -*- coding: utf-8 -*-
"""Assemble the v3.6 release zip: everything from v3.5 (patch_build + puk_mod + README)
plus the AOC LayeredFS mod folders from puk_mod_aoc. Same zip conventions."""
import zipfile, os, sys, glob
sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))

PB = r'D:\nsw\rom\nobu16_powerupkit\patch_build'
PM = r'D:\nsw\rom\nobu16_powerupkit\puk_mod\atmosphere\contents\01007ab012872001'
PA = r'D:\nsw\rom\nobu16_powerupkit\puk_mod_aoc\atmosphere\contents'
OUT = r'D:\nsw\rom\nobu16_powerupkit\NobunagaShinsei_PUK_KR_v3.6.zip'

C0 = 'atmosphere/contents/01007ab012872000'
C1 = 'atmosphere/contents/01007ab012872001'
members = [
    (f'{C0}/exefs/main', os.path.join(PB, r'exefs\main')),
    (f'{C0}/romfs/MSG/JP/strdata.bin', os.path.join(PB, r'romfs\MSG\JP\strdata.bin')),
    (f'{C0}/romfs/MSG/JP/ev_strdata.bin', os.path.join(PB, r'romfs\MSG\JP\ev_strdata.bin')),
    (f'{C0}/romfs/MSG/JP/msggame.bin', os.path.join(PB, r'romfs\MSG\JP\msggame.bin')),
    (f'{C0}/romfs/RES_JP/res_lang.bin', os.path.join(PB, r'romfs\RES_JP\res_lang.bin')),
    (f'{C1}/exefs/main', os.path.join(PM, r'exefs\main')),
    (f'{C1}/romfs/RES_JP_PK/res_lang_pk.bin', os.path.join(PM, r'romfs\RES_JP_PK\res_lang_pk.bin')),
]
for f in ['msgdata.bin', 'msgev.bin', 'msgui.bin', 'msgbre.bin', 'msgire.bin', 'msgstf.bin', 'msggame.bin']:
    members.append((f'{C1}/romfs/MSG_PK/JP/{f}', os.path.join(PM, 'romfs', 'MSG_PK', 'JP', f)))
for f in sorted(os.listdir(os.path.join(PM, 'romfs', 'DLC_PK', 'JP'))):
    members.append((f'{C1}/romfs/DLC_PK/JP/{f}', os.path.join(PM, 'romfs', 'DLC_PK', 'JP', f)))
# AOC mod folders
for p in sorted(glob.glob(os.path.join(PA, '*', 'romfs', 'JP', '*.n16'))):
    rel = os.path.relpath(p, PA).replace(os.sep, '/')
    members.append((f'atmosphere/contents/{rel}', p))
members.append(('README.md', os.path.join(SP, 'README_puk_final.md')))

for arc, path in members:
    assert os.path.isfile(path), path
if os.path.exists(OUT):
    os.remove(OUT)
with zipfile.ZipFile(OUT, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for arc, path in members:
        z.write(path, arc)
with zipfile.ZipFile(OUT) as z:
    assert z.testzip() is None
    for i in z.infolist():
        assert '\\' not in i.filename and i.filename.isascii()
        assert (i.flag_bits >> 11) & 1 == 0
    print(f'OK {OUT}')
    print(f'size: {os.path.getsize(OUT):,} bytes, members: {len(z.namelist())}')
    aoc = [n for n in z.namelist() if '/2873' in n or '28730' in n]
    print('AOC members:', len(aoc))
