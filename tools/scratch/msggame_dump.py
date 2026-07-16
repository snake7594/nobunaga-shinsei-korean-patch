import struct, sys
sys.stdout.reconfigure(encoding='utf-8')

path = sys.argv[1]
with open(path, 'rb') as f:
    d = f.read()
count = struct.unpack_from('<I', d, 0)[0]
print(f'{count} sections')
for i in range(count):
    off, size = struct.unpack_from('<II', d, 4 + i*8)
    head = d[off:off+40]
    hx = ' '.join(f'{b:02x}' for b in head)
    print(f'[{i:2}] off=0x{off:07X} size=0x{size:07X}  {hx}')
    # try utf16 of first bytes
    txt = head.decode('utf-16-le', 'replace')
    print(f'     as utf16: {"".join(c if c.isprintable() else "." for c in txt)}')
