import struct, sys
import lz4.block
sys.stdout.reconfigure(encoding='utf-8')

path = sys.argv[1]
with open(path, 'rb') as f:
    res = f.read()

count, ver = struct.unpack_from('<II', res, 4)
print(f'res_lang: {count} entries ver={ver} size={len(res):,}')

def kt_unwrap(blob):
    dec_size = struct.unpack_from('<Q', blob, 8)[0]
    comp_size = struct.unpack_from('<Q', blob, 16)[0]
    return lz4.block.decompress(blob[24:24 + comp_size], uncompressed_size=dec_size)

# all entries unwrap or parse as LINKDATA
ok = 0
for i in range(count):
    off, size = struct.unpack_from('<II', res, 16 + i * 8)
    blob = res[off:off + size]
    try:
        if blob[:4] == b'LINK':
            ok += 1
        elif blob[0] == 1 and blob[1] == 1:
            kt_unwrap(blob)
            ok += 1
        else:
            print(f'  entry {i}: unknown magic {blob[:4].hex()}')
    except Exception as e:
        print(f'  entry {i}: FAIL {e}')
print(f'entries OK: {ok}/{count}')

RAMP = ' .:-=+*#%@'
for idx in (6, 7):
    off, size = struct.unpack_from('<II', res, 16 + idx * 8)
    g1n = kt_unwrap(res[off:off + size])
    assert g1n[:4] == b'_N1G'
    total = struct.unpack_from('<I', g1n, 8)[0]
    assert total == len(g1n), (total, len(g1n))
    pool = struct.unpack_from('<I', g1n, 0x14)[0]
    nsec = struct.unpack_from('<I', g1n, 0x1C)[0]
    secs = [struct.unpack_from('<I', g1n, 0x20 + 4 * i)[0] for i in range(nsec)]
    bounds = secs + [pool]
    print(f'\nentry {idx}: {len(g1n):,}B sections={[hex(s) for s in secs]} pool=0x{pool:X}')
    for si in range(nsec):
        nrec = (bounds[si + 1] - secs[si] - 0x20000) // 12
        # verify kanji glyph still intact + hangul present
        cm = secs[si]
        g_kanji = struct.unpack_from('<H', g1n, cm + ord('織') * 2)[0]
        g_han = struct.unpack_from('<H', g1n, cm + ord('한') * 2)[0]
        g_gug = struct.unpack_from('<H', g1n, cm + ord('뷁') * 2)[0]  # not in KS2350
        print(f'  sec{si}: {nrec} records, 織={g_kanji} 한={g_han} 뷁={g_gug}')
    # render 한 from sec0
    s = secs[0]
    gid = struct.unpack_from('<H', g1n, s + ord('한') * 2)[0]
    rec = s + 0x20000 + gid * 12
    w, h = g1n[rec], g1n[rec + 1]
    bmp = pool + struct.unpack_from('<I', g1n, rec + 8)[0]
    print(f'  한 sec0 {w}x{h}:')
    step = 2 if h > 30 else 1
    for y in range(0, h, step):
        row = ''
        for x in range(w):
            i2 = y * w + x
            b = g1n[bmp + i2 // 2]
            v = (b >> 4) if i2 % 2 == 0 else (b & 0xF)
            row += RAMP[v * 9 // 15]
        print('    ' + row)
