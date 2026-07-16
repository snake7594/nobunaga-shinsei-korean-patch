import struct, sys

path = sys.argv[1]
with open(path, 'rb') as f:
    d = f.read()

nsec = struct.unpack_from('<I', d, 0x1C)[0]
secs = [struct.unpack_from('<I', d, 0x20 + 4*i)[0] for i in range(nsec)]
val14 = struct.unpack_from('<I', d, 0x14)[0]
bounds = secs + [val14]
print(f'file={len(d):,}  0x14=0x{val14:X}  sections={[hex(s) for s in secs]}')

for i, s in enumerate(secs):
    end = bounds[i+1]
    size = end - s
    # assume charmap of 0x10000 u16
    cm = struct.unpack_from('<32768H', d, s)  # first 32768 entries (BMP half) — full map maybe 0x10000
    cm_full = struct.unpack_from('<65536H', d, s)
    nz = [(c, g) for c, g in enumerate(cm_full) if g != 0]
    maxg = max(g for _, g in nz) if nz else 0
    print(f'\nsection {i} @0x{s:X} size=0x{size:X} ({size:,})')
    print(f'  charmap(assumed 64K u16): nonzero={len(nz):,} maxglyph={maxg} '
          f'first={[(hex(c), g) for c, g in nz[:5]]} last={[(hex(c), g) for c, g in nz[-3:]]}')
    rem = size - 0x20000
    print(f'  remaining after charmap: 0x{rem:X} ({rem:,}); /8={rem/8:.1f} /12={rem/12:.1f} /16={rem/16:.1f} vs maxglyph+1={maxg+1}')
    # dump the first few 8-byte records after charmap
    mo = s + 0x20000
    print('  post-charmap records (as u32 + 4 bytes):')
    for k in range(6):
        off = mo + k*8
        a, = struct.unpack_from('<I', d, off)
        rest = d[off+4:off+8]
        print(f'    [{k}] u32=0x{a:08X}  bytes={rest.hex(" ")}')
    print('  post-charmap records (as u16 pairs x2):')
    for k in range(6):
        off = mo + k*8
        vals = struct.unpack_from('<4H', d, off)
        print(f'    [{k}] {[hex(v) for v in vals]}')

# what's at 0x14 (glyph data start?)
print(f'\n@0x14 target 0x{val14:X}:')
for i in range(val14, val14+64, 16):
    row = d[i:i+16]
    print(f'{i:08X}  {" ".join(f"{b:02x}" for b in row)}')
