# -*- coding: utf-8 -*-
"""Assemble the v3.7 release zip: v3.6 contents plus
 - patched res_lang_exp.bin (872000, and a copy under 872001/RES_JP)
 - patched res_lang_exp_pk.bin (872001)
 - res_lang_pk.bin with Korean battle banners (872001)
 - Korean res_lang.bin copy under 872001/RES_JP (cross-program fallback)"""
import zipfile, os, sys, glob
sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))
V37 = os.path.join(SP, 'v37_out')

PB = r'D:\nsw\rom\nobu16_powerupkit\patch_build'
PM = r'D:\nsw\rom\nobu16_powerupkit\puk_mod\atmosphere\contents\01007ab012872001'
PA = r'D:\nsw\rom\nobu16_powerupkit\puk_mod_aoc\atmosphere\contents'
OUT = r'D:\nsw\rom\nobu16_powerupkit\NobunagaShinsei_PUK_KR_v3.7.zip'

C0 = 'atmosphere/contents/01007ab012872000'
C1 = 'atmosphere/contents/01007ab012872001'
members = [
    (f'{C0}/exefs/main', os.path.join(PB, r'exefs\main')),
    (f'{C0}/romfs/MSG/JP/strdata.bin', os.path.join(PB, r'romfs\MSG\JP\strdata.bin')),
    (f'{C0}/romfs/MSG/JP/ev_strdata.bin', os.path.join(PB, r'romfs\MSG\JP\ev_strdata.bin')),
    (f'{C0}/romfs/MSG/JP/msggame.bin', os.path.join(PB, r'romfs\MSG\JP\msggame.bin')),
    (f'{C0}/romfs/RES_JP/res_lang.bin', os.path.join(PB, r'romfs\RES_JP\res_lang.bin')),
    (f'{C0}/romfs/RES_JP/res_lang_exp.bin', os.path.join(V37, 'res_lang_exp_ko.bin')),
    (f'{C1}/exefs/main', os.path.join(PM, r'exefs\main')),
    (f'{C1}/romfs/RES_JP_PK/res_lang_pk.bin', os.path.join(V37, 'res_lang_pk_v37.bin')),
    (f'{C1}/romfs/RES_JP_PK/res_lang_exp_pk.bin', os.path.join(V37, 'res_lang_exp_pk_ko.bin')),
    (f'{C1}/romfs/RES_JP/res_lang.bin', os.path.join(PB, r'romfs\RES_JP\res_lang.bin')),
    (f'{C1}/romfs/RES_JP/res_lang_exp.bin', os.path.join(V37, 'res_lang_exp_ko.bin')),
]
for f in ['msgdata.bin', 'msgev.bin', 'msgui.bin', 'msgbre.bin', 'msgire.bin', 'msgstf.bin', 'msggame.bin']:
    members.append((f'{C1}/romfs/MSG_PK/JP/{f}', os.path.join(PM, 'romfs', 'MSG_PK', 'JP', f)))
for f in sorted(os.listdir(os.path.join(PM, 'romfs', 'DLC_PK', 'JP'))):
    members.append((f'{C1}/romfs/DLC_PK/JP/{f}', os.path.join(PM, 'romfs', 'DLC_PK', 'JP', f)))
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
