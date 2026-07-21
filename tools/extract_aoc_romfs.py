# -*- coding: utf-8 -*-
"""For each extracted AOC NCA: read rights ID via hactool -i, then extract romfs
with the matching titlekey into aoc_extract/romfs_<titleid>/."""
import os, re, subprocess, sys, glob
sys.stdout.reconfigure(encoding='utf-8')
OUT = r'D:\nsw\rom\nobu16_powerupkit\aoc_extract'
HACTOOL = r'D:\nsw\NCA-NSP-XCI_TO_LayeredFS_v1.6.5\hactool.exe'
KEYS = r'D:\nsw\NCA-NSP-XCI_TO_LayeredFS_v1.6.5\prod.keys'

tk = {}
for line in open(os.path.join(OUT, 'titlekeys.txt')):
    r, k = line.strip().split(' = ')
    tk[r.lower()] = k

for nca in sorted(glob.glob(os.path.join(OUT, '*.nca'))):
    base = os.path.basename(nca)
    r = subprocess.run([HACTOOL, '-k', KEYS, '--disablekeywarns', '-i', nca],
                       capture_output=True, text=True)
    out = r.stdout
    m = re.search(r'Rights ID:\s*([0-9a-fA-F]{32})', out)
    mt = re.search(r'Content Type:\s*(\w+)', out)
    ctype = mt.group(1) if mt else '?'
    if not m:
        print(f'{base}: type={ctype} no-rights-id (standard crypto)')
        rights = None
    else:
        rights = m.group(1).lower()
        tid = rights[:16]
        key = tk.get(rights)
        print(f'{base}: type={ctype} title={tid} key={"OK" if key else "MISSING"}')
        if ctype in ('Data', 'PublicData') and key:
            dst = os.path.join(OUT, f'romfs_{tid}')
            if os.path.isdir(dst) and os.listdir(dst):
                continue
            r2 = subprocess.run([HACTOOL, '-k', KEYS, '--disablekeywarns',
                                 f'--titlekey={key}', f'--romfsdir={dst}', nca],
                                capture_output=True, text=True)
            n = sum(len(fs) for _, _, fs in os.walk(dst))
            print(f'    extracted {n} files -> romfs_{tid}')
