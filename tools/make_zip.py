"""Build a maximally-compatible ZIP with Python's zipfile:
- forward-slash separators
- NO UTF-8 language flag on ASCII names (Windows Explorer friendly)
- single clean top-level folder
"""
import zipfile, os, sys

GAME = r'D:\nsw\rom\노부나가의 야망 신생_일본판'
SRC = os.path.join(GAME, '한글패치_테스트')
VER = sys.argv[1] if len(sys.argv) > 1 else 'v1.1'
TOP = 'NobunagaShinsei_KR'   # single top-level folder
out_zip = os.path.join(GAME, f'NobunagaShinsei_KoreanPatch_{VER}.zip')

# files to include: arcname -> source path
SP = os.path.dirname(os.path.abspath(__file__))
members = [
    (f'{TOP}/README.md', os.path.join(SRC, 'README.md')),
    (f'{TOP}/romfs/MSG/JP/strdata.bin', os.path.join(SRC, r'romfs\MSG\JP\strdata.bin')),
    (f'{TOP}/romfs/MSG/JP/ev_strdata.bin', os.path.join(SRC, r'romfs\MSG\JP\ev_strdata.bin')),
    (f'{TOP}/romfs/MSG/JP/msggame.bin', os.path.join(SRC, r'romfs\MSG\JP\msggame.bin')),
    (f'{TOP}/romfs/RES_JP/res_lang.bin', os.path.join(SRC, r'romfs\RES_JP\res_lang.bin')),
    (f'{TOP}/exefs/main', os.path.join(SP, 'main_patched')),
]
# SC/TC MSG (Korean, same-index copies) so the radial menu shows Korean regardless of language slot
for lang in ('SC', 'TC'):
    for f in ('strdata.bin', 'ev_strdata.bin', 'msggame.bin'):
        p = os.path.join(SRC, 'romfs', 'MSG', lang, f)
        if os.path.exists(p):
            members.append((f'{TOP}/romfs/MSG/{lang}/{f}', p))

if os.path.exists(out_zip):
    os.remove(out_zip)

with zipfile.ZipFile(out_zip, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    # explicit directory entries (helps some extractors build the tree)
    for d in [f'{TOP}/', f'{TOP}/romfs/', f'{TOP}/romfs/MSG/', f'{TOP}/romfs/MSG/JP/', f'{TOP}/romfs/MSG/SC/', f'{TOP}/romfs/MSG/TC/', f'{TOP}/romfs/RES_JP/', f'{TOP}/exefs/']:
        zi = zipfile.ZipInfo(d)
        zi.external_attr = (0o40755 << 16) | 0x10  # dir flag
        z.writestr(zi, b'')
    for arc, path in members:
        z.write(path, arc)

# verify: flag bits, names, testzip
with zipfile.ZipFile(out_zip) as z:
    assert z.testzip() is None
    print(f'{out_zip}')
    print(f'size: {os.path.getsize(out_zip):,} bytes')
    for i in z.infolist():
        assert '\\' not in i.filename
        assert i.filename.isascii()
        assert (i.flag_bits >> 11) & 1 == 0, f'UTF8 flag set on {i.filename}'
        print(f'  flag=0x{i.flag_bits:04X} {"DIR " if i.is_dir() else "    "} {i.filename}')
print('OK: forward slashes, ascii names, no UTF-8 flag, valid')
