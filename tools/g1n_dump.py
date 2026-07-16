import struct, sys

path = sys.argv[1]
with open(path, 'rb') as f:
    d = f.read()

def hexdump(off, n, label):
    print(f'-- {label} @0x{off:X} --')
    for i in range(off, min(off + n, len(d)), 16):
        row = d[i:i+16]
        hx = ' '.join(f'{b:02x}' for b in row)
        asc = ''.join(chr(b) if 32 <= b < 127 else '.' for b in row)
        print(f'{i:08X}  {hx:<48}  {asc}')

total = struct.unpack_from('<I', d, 8)[0]
hdr_first = struct.unpack_from('<I', d, 0x0C)[0]
val10 = struct.unpack_from('<I', d, 0x10)[0]
val14 = struct.unpack_from('<I', d, 0x14)[0]
val18 = struct.unpack_from('<I', d, 0x18)[0]
nsec = struct.unpack_from('<I', d, 0x1C)[0]
secs = [struct.unpack_from('<I', d, 0x20 + 4*i)[0] for i in range(nsec)]
print(f'file size={len(d):,} total_field={total:,} 0x0C=0x{hdr_first:X} 0x10={val10} 0x14=0x{val14:X} 0x18={val18} nsec={nsec}')
print('sections:', ', '.join(f'0x{s:X}' for s in secs))

ramp_off = 0x20 + 4*nsec
hexdump(ramp_off, 80, 'alpha ramp')
after_ramp = ramp_off + 64
hexdump(after_ramp, 160, 'after ramp')
for i, s in enumerate(secs):
    hexdump(s, 96, f'section {i}')
hexdump(len(d) - 64, 64, 'tail')
