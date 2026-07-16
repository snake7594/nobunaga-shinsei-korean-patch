import struct, sys
sys.stdout.reconfigure(encoding='utf-8')

for path in sys.argv[1:]:
    with open(path, 'rb') as f:
        d = f.read()
    count = struct.unpack_from('<I', d, 0)[0]
    name = path.split('\\')[-1]
    print(f'=== {name}: {count} sections ===')
    for i in range(count):
        off, size = struct.unpack_from('<II', d, 4 + i*8)
        sid, f1, f2, f3, f4 = struct.unpack_from('<5I', d, off)
        tab = off + f3
        first_val = struct.unpack_from('<I', d, tab)[0]
        n = first_val // 4
        entries = struct.unpack_from(f'<{n}I', d, tab)
        pool_start = first_val
        pool_end = size - f3
        # candidates
        print(f'[{i:2}] size=0x{size:08X} f1=0x{f1:08X} f2=0x{f2:08X} f3=0x{f3:X} f4=0x{f4:08X} '
              f'n={n:6} pool=0x{pool_start:X}..0x{pool_end:X} '
              f'size-f1=0x{size-f1:X} size-f2=0x{size-f2:X} f2-f1=0x{f2-f1:X}')
