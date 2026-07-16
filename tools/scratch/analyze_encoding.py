"""Analyze how glyph bitmap values are encoded: plain alpha vs layered/SDF."""
import struct, sys
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')

path = sys.argv[1]  # original g1n
with open(path, 'rb') as f:
    d = f.read()
pool = struct.unpack_from('<I', d, 0x14)[0]
nsec = struct.unpack_from('<I', d, 0x1C)[0]
secs = [struct.unpack_from('<I', d, 0x20 + 4 * i)[0] for i in range(nsec)]
npal = struct.unpack_from('<I', d, 0x18)[0]
pal_off = 0x20 + 4 * nsec

# 1) dump unique palettes
print(f'{npal} palettes:')
seen = {}
for k in range(npal):
    p = d[pal_off + k * 64: pal_off + k * 64 + 64]
    key = p.hex()
    if key not in seen:
        seen[key] = [k]
        cols = [p[i*4:i*4+4] for i in range(16)]
        desc = ' '.join(f'{c[0]:02x}{c[1]:02x}{c[2]:02x}{c[3]:02x}' for c in cols)
        print(f'  pal{k}: {desc}')
    else:
        seen[key].append(k)
print(f'unique palettes: {len(seen)}; groups: {[v[:3] for v in list(seen.values())[:8]]}')

def glyph_pix(sec, ch):
    gid = struct.unpack_from('<H', d, sec + ord(ch) * 2)[0]
    rec = sec + 0x20000 + gid * 12
    w, h = d[rec], d[rec + 1]
    base = pool + struct.unpack_from('<I', d, rec + 8)[0]
    pix = [[0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            i = y * w + x
            b = d[base + i // 2]
            pix[y][x] = (b & 0xF) if i % 2 == 0 else (b >> 4)
    return w, h, pix

# 2) value histogram + row slice of kanji
for ch in '登一':
    w, h, pix = glyph_pix(secs[0], ch)
    hist = Counter(v for row in pix for v in row)
    print(f'\n{ch} histogram: {dict(sorted(hist.items()))}')
    # print middle rows as hex digits
    print(f'{ch} rows:')
    for y in range(0, h):
        row = ''.join(f'{v:x}' for v in pix[y])
        if row.strip('0'):
            print(f'  y{y:2}: {row}')
