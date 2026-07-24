# -*- coding: utf-8 -*-
"""Assemble the v3.9 (game 1.1.7) release zip.
 - 872000 (base game): romfs identical in 1.1.7 -> reuse v3.8 MSG/RES files;
   exefs/main re-derived from the 1.1.7 executable.
 - 872001 (PUK): MSG_PK + DLC_PK rebuilt against 1.1.7; res_lang_pk / res_lang_exp_pk
   unchanged in 1.1.7 -> reuse the Korean versions; exefs/main re-derived.
 - AOC scenario DLC: unchanged -> reuse."""
import zipfile, os, sys, glob
sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))
V37 = os.path.join(SP, 'v37_out')

PB  = r'D:\nsw\rom\nobu16_powerupkit\patch_build'                      # v3.8 base-game build
M117 = r'D:\nsw\rom\nobu16_powerupkit\puk_mod_117'                     # new 1.1.7 PUK build
PM  = r'D:\nsw\rom\nobu16_powerupkit\puk_mod\atmosphere\contents\01007ab012872001'
PA  = r'D:\nsw\rom\nobu16_powerupkit\puk_mod_aoc\atmosphere\contents'  # AOC mods
OUT = r'D:\nsw\rom\nobu16_powerupkit\NobunagaShinsei_PUK_KR_v3.9.zip'

C0 = 'atmosphere/contents/01007ab012872000'
C1 = 'atmosphere/contents/01007ab012872001'
R1 = os.path.join(M117, 'atmosphere', 'contents', '01007ab012872001', 'romfs')

# Ensure the Korean-input-method main (main_872001_hangul) is present/fresh before packaging.
import subprocess
_rc = subprocess.run([sys.executable, os.path.join(SP, 'apply_hangul_kbd.py')], cwd=SP)
if _rc.returncode != 0:
    sys.exit('apply_hangul_kbd.py failed — 한글 입력기 main 생성 실패, 빌드 중단')

members = [
    # --- base game (872000) ---
    (f'{C0}/exefs/main',                    os.path.join(M117, 'main_872000')),
    (f'{C0}/romfs/MSG/JP/strdata.bin',      os.path.join(PB, r'romfs\MSG\JP\strdata.bin')),
    (f'{C0}/romfs/MSG/JP/ev_strdata.bin',   os.path.join(PB, r'romfs\MSG\JP\ev_strdata.bin')),
    (f'{C0}/romfs/MSG/JP/msggame.bin',      os.path.join(PB, r'romfs\MSG\JP\msggame.bin')),
    (f'{C0}/romfs/RES_JP/res_lang.bin',     os.path.join(PB, r'romfs\RES_JP\res_lang.bin')),
    (f'{C0}/romfs/RES_JP/res_lang_exp.bin', os.path.join(V37, 'res_lang_exp_ko.bin')),
    # --- PUK (872001) ---
    # exefs/main carries the Korean input method (한글 입력기 + 성명/독음 검증 바이패스),
    # applied from issue #1's xdelta via apply_hangul_kbd.py -> main_872001_hangul.
    (f'{C1}/exefs/main',                        os.path.join(M117, 'main_872001_hangul')),
    (f'{C1}/romfs/RES_JP_PK/res_lang_pk.bin',     os.path.join(V37, 'res_lang_pk_v37.bin')),
    (f'{C1}/romfs/RES_JP_PK/res_lang_exp_pk.bin', os.path.join(V37, 'res_lang_exp_pk_ko.bin')),
    (f'{C1}/romfs/RES_JP/res_lang.bin',           os.path.join(PB, r'romfs\RES_JP\res_lang.bin')),
    (f'{C1}/romfs/RES_JP/res_lang_exp.bin',       os.path.join(V37, 'res_lang_exp_ko.bin')),
]
for f in sorted(os.listdir(os.path.join(R1, 'MSG_PK', 'JP'))):
    members.append((f'{C1}/romfs/MSG_PK/JP/{f}', os.path.join(R1, 'MSG_PK', 'JP', f)))
for f in sorted(os.listdir(os.path.join(R1, 'DLC_PK', 'JP'))):
    members.append((f'{C1}/romfs/DLC_PK/JP/{f}', os.path.join(R1, 'DLC_PK', 'JP', f)))
for p in sorted(glob.glob(os.path.join(PA, '*', 'romfs', 'JP', '*.n16'))):
    rel = os.path.relpath(p, PA).replace(os.sep, '/')
    members.append((f'atmosphere/contents/{rel}', p))
members.append(('README.md', os.path.join(SP, 'README_puk_final.md')))

missing = [(a, p) for a, p in members if not os.path.isfile(p)]
if missing:
    for a, p in missing:
        print('MISSING SOURCE:', a, '<-', p)
    sys.exit('aborting')

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
    print('MSG_PK members:', sum(1 for n in z.namelist() if 'MSG_PK' in n))
    print('DLC_PK members:', sum(1 for n in z.namelist() if 'DLC_PK' in n))
    print('AOC members   :', sum(1 for n in z.namelist() if '/01007ab0128730' in n))
