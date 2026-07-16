import struct, sys

path = sys.argv[1]
with open(path, 'rb') as f:
    d = f.read()

count = struct.unpack_from('<I', d, 0)[0]
print(f'file={len(d):,} sections={count}')
secs = []
for i in range(count):
    off, size = struct.unpack_from('<II', d, 4 + i*8)
    secs.append((off, size))
    hdr = struct.unpack_from('<5I', d, off)
    print(f'[{i:2}] off=0x{off:07X} size=0x{size:07X} ({size:9,})  '
          f'id=0x{hdr[0]:X} f1=0x{hdr[1]:X} f2=0x{hdr[2]:X} f3=0x{hdr[3]:X} f4=0x{hdr[4]:08X}')

def hexdump(off, n, label):
    print(f'-- {label} @0x{off:X} --')
    for i in range(off, min(off + n, len(d)), 16):
        row = d[i:i+16]
        hx = ' '.join(f'{b:02x}' for b in row)
        asc = ''.join(chr(b) if 32 <= b < 127 else '.' for b in row)
        print(f'{i:08X}  {hx:<48}  {asc}')

# inspect section 0 in detail
off, size = secs[0]
sid, f1, f2, f3, f4 = struct.unpack_from('<5I', d, off)
# offset table at off+f3?
tab = off + f3
print(f'\nsection0: table@+0x{f3:X}, f1=0x{f1:X} f2=0x{f2:X}')
first = struct.unpack_from('<8I', d, tab)
print('first table entries:', [hex(v) for v in first])
# dump around f2 (string data start?)
hexdump(off + f2, 160, 'sec0 + f2')
# dump at first offset interpreted rel to section and rel to f2
hexdump(off + first[0], 96, 'sec0 + tab[0]')
if off + f2 + first[0] < len(d):
    hexdump(off + f2 + first[0], 96, 'sec0 + f2 + tab[0]')
