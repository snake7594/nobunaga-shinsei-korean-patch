# -*- coding: utf-8 -*-
"""Extract .tik files and small .nca files from game_puk.nsp (PFS0), build a
rightsID->titlekey map, then run hactool per NCA to identify and extract romfs."""
import struct, sys, os, subprocess
sys.stdout.reconfigure(encoding='utf-8')

NSP = r'D:\nsw\rom\nobu16_powerupkit\game_puk.nsp'
OUT = r'D:\nsw\rom\nobu16_powerupkit\aoc_extract'
HACTOOL = r'D:\nsw\NCA-NSP-XCI_TO_LayeredFS_v1.6.5\hactool.exe'
KEYS = r'D:\nsw\NCA-NSP-XCI_TO_LayeredFS_v1.6.5\prod.keys'
SKIP_BYTES = 300 * 1024 * 1024   # skip NCAs bigger than this for now

os.makedirs(OUT, exist_ok=True)
f = open(NSP, 'rb')
hdr = f.read(1 << 20)
assert hdr[:4] == b'PFS0'
nf, strsz = struct.unpack_from('<II', hdr, 4)
tab = 16
stroff = tab + nf * 24
body = stroff + strsz
entries = []
for i in range(nf):
    off, sz, ns, _ = struct.unpack_from('<QQII', hdr, tab + i * 24)
    name = hdr[stroff + ns:hdr.find(b'\0', stroff + ns)].decode()
    entries.append((name, body + off, sz))

# 1) tickets -> titlekeys
tk = {}
for name, off, sz in entries:
    if name.endswith('.tik'):
        f.seek(off)
        t = f.read(sz)
        titlekey = t[0x180:0x190].hex()
        rights = t[0x2A0:0x2B0].hex()
        tk[rights] = titlekey
print('titlekeys:', len(tk))
with open(os.path.join(OUT, 'titlekeys.txt'), 'w') as fh:
    for r, k in sorted(tk.items()):
        fh.write(f'{r} = {k}\n')
        print(' ', r, '=', k)

# 2) extract small NCAs
for name, off, sz in entries:
    if not name.endswith('.nca') or sz > SKIP_BYTES:
        continue
    dst = os.path.join(OUT, name)
    if os.path.isfile(dst) and os.path.getsize(dst) == sz:
        continue
    f.seek(off)
    with open(dst, 'wb') as o:
        remain = sz
        while remain:
            chunk = f.read(min(16 << 20, remain))
            o.write(chunk)
            remain -= len(chunk)
print('extracted small NCAs')
