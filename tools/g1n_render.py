import struct, sys

path = sys.argv[1]
chars = sys.argv[2]  # characters to render
sec_idx = int(sys.argv[3]) if len(sys.argv) > 3 else 0

with open(path, 'rb') as f:
    d = f.read()

pool = struct.unpack_from('<I', d, 0x14)[0]
nsec = struct.unpack_from('<I', d, 0x1C)[0]
secs = [struct.unpack_from('<I', d, 0x20 + 4*i)[0] for i in range(nsec)]
s = secs[sec_idx]

RAMP = ' .:-=+*#%@'
for ch in chars:
    code = ord(ch)
    gid = struct.unpack_from('<H', d, s + code*2)[0]
    rec_off = s + 0x20000 + gid*12
    m = d[rec_off:rec_off+8]
    bmp_off, = struct.unpack_from('<I', d, rec_off+8)
    print(f"char '{ch}' U+{code:04X} glyph={gid} metrics={m.hex(' ')} bmp=0x{bmp_off:X}")
    w, h = m[0], m[1]
    base = pool + bmp_off
    # 4bpp, assume row-major w*h/2 bytes
    rows = []
    for y in range(h):
        row = ''
        for x in range(w):
            idx = y*w + x
            b = d[base + idx//2]
            v = (b & 0xF) if idx % 2 == 0 else (b >> 4)
            row += RAMP[min(v * (len(RAMP)-1) // 15, len(RAMP)-1)]
        rows.append(row)
    print('\n'.join(rows))
    print()
