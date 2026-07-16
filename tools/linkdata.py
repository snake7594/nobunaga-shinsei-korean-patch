import struct, sys, os

def identify(blob):
    if len(blob) < 8:
        return 'tiny'
    m4 = blob[:4]
    if m4 == b'GT1G' or m4 == b'G1TG':
        return 'G1T texture'
    if m4 == b'_N1G' or m4 == b'G1N_':
        return 'G1N FONT'
    if m4 == b'LINK':
        return 'LINKDATA (nested)'
    if m4 == b'_M1G' or m4 == b'G1M_':
        return 'G1M model'
    if m4[:2] == b'\x78\x9c' or m4[:2] == b'\x78\xda':
        return 'zlib'
    if m4 == b'OTTO':
        return 'OTF'
    if m4 == b'\x00\x01\x00\x00':
        return 'TTF?'
    if m4 == b'KTSR':
        return 'KTSR sound'
    if m4 == b'KSHL':
        return 'shader'
    return m4.hex(' ') + ' / ' + ''.join(chr(c) if 32 <= c < 127 else '.' for c in m4)

def parse(path, extract_idx=None, outdir=None):
    with open(path, 'rb') as f:
        d = f.read()
    assert d[:4] == b'LINK'
    count, ver, zero = struct.unpack_from('<III', d, 4)
    print(f'{path}: {count} entries, ver={ver}')
    entries = []
    for i in range(count):
        off, size = struct.unpack_from('<II', d, 16 + i * 8)
        entries.append((off, size))
        blob = d[off:off + min(size, 16)]
        kind = identify(d[off:off + 16])
        print(f'  [{i:2}] off=0x{off:08X} size={size:12,}  {kind}')
    if extract_idx is not None:
        for i in extract_idx:
            off, size = entries[i]
            out = os.path.join(outdir, f'entry_{i:02d}.bin')
            with open(out, 'wb') as f:
                f.write(d[off:off + size])
            print(f'extracted [{i}] -> {out}')

if __name__ == '__main__':
    path = sys.argv[1]
    if len(sys.argv) > 2:
        idx = [int(x) for x in sys.argv[2].split(',')]
        parse(path, idx, sys.argv[3])
    else:
        parse(path)
