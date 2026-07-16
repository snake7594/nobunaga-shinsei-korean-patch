import sys

path = sys.argv[1]
with open(path, 'rb') as f:
    d = f.read()

print(f'file: {path}  size: {len(d):,}')
print('head:', d[:64].hex(' '))

# signatures to look for
sigs = {
    b'OTTO': 'OTF (CFF font)',
    b'ttcf': 'TTC collection',
    b'glyf': 'TTF glyf table tag',
    b'GLYF': 'GLYF',
    b'cmap': 'TTF cmap table tag',
    b'DSIG': 'TTF DSIG tag',
    b'G1TG': 'KT texture (G1TG)',
    b'GT1G': 'KT texture (GT1G)',
    b'G1M_': 'KT model',
    b'KTGL': 'KTGL',
    b'G1N_': 'KT font G1N',
    b'_N1G': 'KT font G1N (LE)',
    b'FFNT': 'bffnt',
    b'CFNT': 'bcfnt',
    b'RFNT': 'brfnt',
    b'sfnt': 'sfnt',
    b'true': 'ttf true',
    b'OS/2': 'TTF OS/2 tag',
    b'hmtx': 'TTF hmtx tag',
    b'FSST': 'FSST',
    b'SRST': 'KT SRST',
    b'RDBF': 'KT RDB',
}
from collections import defaultdict
hits = defaultdict(list)
for sig, name in sigs.items():
    start = 0
    while True:
        i = d.find(sig, start)
        if i < 0:
            break
        hits[name].append(i)
        start = i + 1
        if len(hits[name]) > 20:
            break

# TTF version header 00 01 00 00 00 <numtables u16> ... too noisy; instead check right after OTTO/near cmap
for name, offs in sorted(hits.items()):
    shown = ', '.join(f'0x{o:X}' for o in offs[:10])
    more = ' ...' if len(offs) > 10 else ''
    print(f'{name:24} x{len(offs):<4} {shown}{more}')
