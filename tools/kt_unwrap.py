import struct, sys
import lz4.block

src, dst = sys.argv[1], sys.argv[2]
with open(src, 'rb') as f:
    d = f.read()

assert d[0] == 1 and d[1] == 1, 'unexpected wrapper'
type_hash = struct.unpack_from('<I', d, 2)[0]
dec_size = struct.unpack_from('<Q', d, 8)[0]
comp_size = struct.unpack_from('<Q', d, 16)[0]
print(f'type_hash=0x{type_hash:08X} dec={dec_size:,} comp={comp_size:,} payload={len(d)-24:,}')

payload = d[24:24 + comp_size]
try:
    out = lz4.block.decompress(payload, uncompressed_size=dec_size)
    print('single-block LZ4 OK')
except Exception as e:
    print('single-block failed:', e)
    # try chunked: [u32 chunk_comp_size][chunk]...
    out = bytearray()
    pos = 0
    while pos < len(payload) and len(out) < dec_size:
        csz = struct.unpack_from('<I', payload, pos)[0]
        pos += 4
        remaining = dec_size - len(out)
        chunk = lz4.block.decompress(payload[pos:pos + csz], uncompressed_size=min(65536, remaining))
        out += chunk
        pos += csz
    out = bytes(out)
    print('chunked LZ4 OK')

assert len(out) == dec_size, f'{len(out)} != {dec_size}'
with open(dst, 'wb') as f:
    f.write(out)
print(f'wrote {dst} ({len(out):,} bytes), head:')
print(out[:64].hex(' '))
