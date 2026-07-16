import struct, sys
import lz4.block

src = sys.argv[1]
dst = sys.argv[2]

with open(src, 'rb') as f:
    d = f.read()

assert d[:4] == b'NSO0', 'not an NSO'
flags = struct.unpack_from('<I', d, 0x0C)[0]

segs = []
for i, base in enumerate((0x10, 0x20, 0x30)):
    file_off, mem_off, size = struct.unpack_from('<III', d, base)
    comp_size = struct.unpack_from('<I', d, 0x60 + i * 4)[0]
    compressed = bool(flags & (1 << i))
    segs.append((file_off, mem_off, size, comp_size, compressed))

names = ['.text', '.rodata', '.data']
total = max(mem_off + size for _, mem_off, size, _, _ in segs)
out = bytearray(total)

for name, (file_off, mem_off, size, comp_size, compressed) in zip(names, segs):
    blob = d[file_off:file_off + (comp_size if compressed else size)]
    if compressed:
        blob = lz4.block.decompress(blob, uncompressed_size=size)
    assert len(blob) == size, f'{name}: got {len(blob)}, want {size}'
    out[mem_off:mem_off + size] = blob
    print(f'{name}: file_off=0x{file_off:X} mem_off=0x{mem_off:X} size=0x{size:X} comp=0x{comp_size:X} compressed={compressed}')

with open(dst, 'wb') as f:
    f.write(out)
print(f'wrote {dst} ({len(out)} bytes)')
