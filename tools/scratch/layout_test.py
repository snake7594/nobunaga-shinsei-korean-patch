"""Determine the true 4bpp pixel layout by smoothness scoring on original kanji."""
import struct, sys
sys.stdout.reconfigure(encoding='utf-8')

path = sys.argv[1]
with open(path, 'rb') as f:
    d = f.read()
pool = struct.unpack_from('<I', d, 0x14)[0]
secs = [struct.unpack_from('<I', d, 0x20 + 4 * i)[0] for i in range(3)]

def raw_glyph(sec, ch):
    gid = struct.unpack_from('<H', d, sec + ord(ch) * 2)[0]
    rec = sec + 0x20000 + gid * 12
    w, h = d[rec], d[rec + 1]
    base = pool + struct.unpack_from('<I', d, rec + 8)[0]
    return w, h, d[base:base + w * h // 2]

def decode(raw, w, h, mode):
    pix = [[0] * w for _ in range(h)]
    if mode in ('h_lo', 'h_hi'):          # horizontal pairs, row-major
        for y in range(h):
            for x in range(w):
                i = y * w + x
                b = raw[i // 2]
                lo, hi = b & 0xF, b >> 4
                pix[y][x] = (lo if i % 2 == 0 else hi) if mode == 'h_lo' else (hi if i % 2 == 0 else lo)
    elif mode in ('v_lo', 'v_hi'):        # vertical pairs: byte = (x,2y),(x,2y+1)
        k = 0
        for yy in range(h // 2):
            for x in range(w):
                b = raw[k]; k += 1
                lo, hi = b & 0xF, b >> 4
                if mode == 'v_lo':
                    pix[2 * yy][x], pix[2 * yy + 1][x] = lo, hi
                else:
                    pix[2 * yy][x], pix[2 * yy + 1][x] = hi, lo
    elif mode in ('c_lo', 'c_hi'):        # column-major, vertical nibble pairs down each column
        k = 0
        for x in range(w):
            for yy in range(h // 2):
                b = raw[k]; k += 1
                lo, hi = b & 0xF, b >> 4
                if mode == 'c_lo':
                    pix[2 * yy][x], pix[2 * yy + 1][x] = lo, hi
                else:
                    pix[2 * yy][x], pix[2 * yy + 1][x] = hi, lo
    return pix

def smoothness(pix, w, h):
    s = 0
    for y in range(h):
        for x in range(w):
            if x + 1 < w:
                s += abs(pix[y][x] - pix[y][x + 1])
            if y + 1 < h:
                s += abs(pix[y][x] - pix[y + 1][x])
    return s

for ch in '登一口':
    w, h, raw = raw_glyph(secs[0], ch)
    scores = {m: smoothness(decode(raw, w, h, m), w, h) for m in
              ('h_lo', 'h_hi', 'v_lo', 'v_hi', 'c_lo', 'c_hi')}
    best = min(scores, key=scores.get)
    print(f'{ch}: ' + '  '.join(f'{m}={v}' for m, v in scores.items()) + f'   BEST={best}')

# show best-mode render of 登
w, h, raw = raw_glyph(secs[0], '一')
RAMP = ' .:-=+*#%@'
for mode in ('h_lo', 'v_lo', 'v_hi'):
    pix = decode(raw, w, h, mode)
    print(f'\n-- 一 decoded as {mode} --')
    for y in range(h):
        row = ''.join(RAMP[pix[y][x] * 9 // 15] for x in range(w))
        if row.strip():
            print(f'  y{y:2}: {row}')
