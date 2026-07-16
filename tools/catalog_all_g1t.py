"""Catalog every G1T texture dimension across all romfs archives — find label clusters."""
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
    return b

def parse_link(d, base=0):
    try:
        c = struct.unpack_from('<I', d, base + 4)[0]
        if c > 200000:
            return []
        return [struct.unpack_from('<II', d, base + 16 + i * 8) for i in range(c)]
    except Exception:
        return []

def g1t_dims(g):
    try:
        tbl = struct.unpack_from('<I', g, 0x0C)[0]
        ntex = struct.unpack_from('<I', g, 0x10)[0]
        offs = struct.unpack_from(f'<{ntex}I', g, tbl)
        out = []
        for o in offs:
            p = tbl + o
            fmt, dxdy = g[p + 1], g[p + 2]
            out.append((fmt, 1 << (dxdy & 0xF), 1 << (dxdy >> 4)))
        return out
    except Exception:
        return []

# label-shaped: wide (aspect 2:1..12:1), height 32..160
def is_label(w, h):
    return 32 <= h <= 160 and 1.8 <= w / h <= 14

clusters = defaultdict(list)  # file -> list of (loc, fmt, w, h)

SKIP = {'MOVIE', 'SNDRES', 'CONTENTS'}
BIG_OK = {'res_grp.bin', 'res_else.bin', 'res_lang.bin', 'res_lang_exp.bin', 'res_eff.bin',
          'res_event.bin', 'res_exp.bin', 'res_shader.bin'}
for root, dirs, files in os.walk(SRC):
    dirs[:] = [x for x in dirs if x not in SKIP]
    for fn in files:
        p = os.path.join(root, fn)
        sz = os.path.getsize(p)
        if sz > 780 * 1024 * 1024:
            continue
        rel = os.path.relpath(p, SRC)
        f = open(p, 'rb')
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        data = mm
        head = bytes(data[:4])
        def handle(blob_getter, size, loc):
            raw = blob_getter()
            dec = unwrap(raw)
            if dec is None:
                dec = raw
            if dec[:4] == b'GT1G':
                for fmt, w, h in g1t_dims(dec):
                    if is_label(w, h):
                        clusters[rel].append((loc, fmt, w, h))
            elif dec[:4] == b'LINK':
                for j, (o2, s2) in enumerate(parse_link(dec)):
                    if s2 == 0:
                        continue
                    sub = dec[o2:o2 + s2]
                    d2 = unwrap(sub) or sub
                    if d2[:4] == b'GT1G':
                        for fmt, w, h in g1t_dims(d2):
                            if is_label(w, h):
                                clusters[rel].append((f'{loc}[{j}]', fmt, w, h))
        if head == b'LINK':
            toc = parse_link(data)
            for i, (off, size) in enumerate(toc):
                handle(lambda off=off, size=size: bytes(data[off:off + size]), size, f'{i}')
        else:
            handle(lambda: bytes(data[:sz]), sz, 'root')
        mm.close()
        f.close()

for rel, items in sorted(clusters.items()):
    print(f'\n{rel}: {len(items)} label-shaped textures')
    dc = Counter((w, h) for _, _, w, h in items)
    for (w, h), n in sorted(dc.items(), key=lambda x: -x[1])[:8]:
        print(f'   {w}x{h}: {n}')
print('\ndone')
