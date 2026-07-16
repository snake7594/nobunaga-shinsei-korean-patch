"""Dump G1T container + texture headers for a sample of differing entries."""
import struct, sys, os
import lz4.block
sys.stdout.reconfigure(encoding='utf-8')
SRC = r'D:\nsw\rom\노부나가의 야망 신생_일본판\추출원본'

def kt_unwrap(blob):
    if blob[0] == 1 and blob[1] == 1:
        dec = struct.unpack_from('<Q', blob, 8)[0]
        comp = struct.unpack_from('<Q', blob, 16)[0]
        return lz4.block.decompress(blob[24:24 + comp], uncompressed_size=dec)
    return blob

def get_sub(d, i, j):
    off, size = struct.unpack_from('<II', d, 16 + i * 8)
    blob = d[off:off + size]
    o2, s2 = struct.unpack_from('<II', blob, 16 + j * 8)
    return kt_unwrap(blob[o2:o2 + s2])

with open(os.path.join(SRC, r'romfs\RES_JP\res_lang.bin'), 'rb') as f:
    d = f.read()

def dump_g1t(g, tag):
    magic = g[:4]
    ver = g[4:8].decode('ascii', 'replace')
    total, tbl_off, ntex, plat = struct.unpack_from('<IIII', g, 8)
    print(f'{tag}: magic={magic} ver={ver} total={total:,} tbl=0x{tbl_off:X} ntex={ntex} plat={plat}')
    # global flags area between 0x18? and table — dump raw
    print(f'  pre-table bytes: {g[0x18:tbl_off].hex(" ")}')
    offs = struct.unpack_from(f'<{ntex}I', g, tbl_off)
    for t, o in enumerate(offs):
        th = g[tbl_off + o: tbl_off + o + 32]
        b0, fmt, dxdy = th[0], th[1], th[2]
        w = 1 << (dxdy >> 4)
        h = 1 << (dxdy & 0xF)
        flags = th[3:8].hex(' ')
        print(f'  tex{t}: b0=0x{b0:02X} fmt=0x{fmt:02X} packed_wh={w}x{h} flags={flags}')
        print(f'    next bytes: {th[8:32].hex(" ")}')

for (i, j) in [(0, 2), (0, 28), (0, 43), (1, 2), (2, 3)]:
    g = get_sub(d, i, j)
    dump_g1t(g, f'[{i}][{j}]')
    print()
