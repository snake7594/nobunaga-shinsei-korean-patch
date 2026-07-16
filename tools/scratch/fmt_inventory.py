"""Full inventory of every G1T texture format/dim across all UI-relevant archives.
Flags textures that previous exports silently skipped (BC7 etc.)."""
import struct, os, sys, mmap
import lz4.block
from collections import Counter, defaultdict
sys.stdout.reconfigure(encoding='utf-8')
SRC = r'D:\nsw\rom\노부나가의 야망 신생_일본판\추출원본\romfs'

def unwrap(b):
    if len(b) >= 24 and b[0] == 1 and b[1] == 1:
        try:
            return lz4.block.decompress(b[24:24 + struct.unpack_from('<Q', b, 16)[0]],
                                        uncompressed_size=struct.unpack_from('<Q', b, 8)[0])
        except Exception:
            return None
    return None

def parse_link(d):
    try:
        c = struct.unpack_from('<I', d, 4)[0]
        if c > 500000:
            return []
        return [struct.unpack_from('<II', d, 16 + i * 8) for i in range(c)]
    except Exception:
        return []

def g1t_texinfo(g):
    out = []
    try:
        tbl = struct.unpack_from('<I', g, 0x0C)[0]
        ntex = struct.unpack_from('<I', g, 0x10)[0]
        offs = struct.unpack_from(f'<{ntex}I', g, tbl)
        for o in offs:
            p = tbl + o
            fmt, dxdy = g[p + 1], g[p + 2]
            out.append((fmt, 1 << (dxdy & 0xF), 1 << (dxdy >> 4)))
    except Exception:
        pass
    return out

def walk(blob, path, found, depth=0):
    if blob[:4] == b'GT1G':
        for fmt, w, h in g1t_texinfo(blob):
            found[(fmt)].append((path, w, h))
        return
    if depth < 6 and blob[:4] == b'LINK':
        for i, (off, size) in enumerate(parse_link(blob)):
            if size == 0 or off + size > len(blob):
                continue
            sub = blob[off:off + size]
            dec = unwrap(sub)
            walk(dec if dec else sub, f'{path}[{i}]', found, depth + 1)

FILES = [r'RES_JP\res_lang.bin', r'RES_JP\res_lang_exp.bin', r'RES\res_else.bin',
         r'RES\res_grp.bin', r'RES\res_eff.bin', r'RES\res_event.bin', r'RES\res_exp.bin']
for rel in FILES:
    p = os.path.join(SRC, rel)
    data = open(p, 'rb').read()
    found = defaultdict(list)
    dec = unwrap(data)
    walk(dec if dec else data, rel, found)
    total = sum(len(v) for v in found.values())
    print(f'\n=== {rel}: {total} textures ===')
    for fmt in sorted(found):
        items = found[fmt]
        dims = Counter((w, h) for _, w, h in items)
        supported = fmt in (0x59, 0x5B, 0x01)
        tag = '' if supported else '  <<< PREVIOUSLY SKIPPED'
        top = ', '.join(f'{w}x{h}:{n}' for (w, h), n in dims.most_common(5))
        print(f'  fmt 0x{fmt:02X}: {len(items):4}  [{top}]{tag}')
        if not supported and fmt not in (0x02, 0x04):  # skip 1x1 placeholders detail
            for path, w, h in items[:10]:
                if w >= 32 and h >= 16:
                    print(f'       {path} {w}x{h}')
