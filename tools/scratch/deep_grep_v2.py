"""Exhaustive recursive search for radial-menu words: decompress EVERYTHING
(unlimited LINK depth, all wrapped blobs) and raw-search each buffer in UTF-16LE."""
import struct, os, sys, mmap
import lz4.block
sys.stdout.reconfigure(encoding='utf-8')

WORDS = ['評定', '内政', '任命', '軍事', '外交']
NEEDLES = [(w, w.encode('utf-16-le')) for w in WORDS]

def unwrap(b):
    if len(b) >= 24 and b[0] == 1 and b[1] == 1:
        try:
            return lz4.block.decompress(b[24:24 + struct.unpack_from('<Q', b, 16)[0]],
                                        uncompressed_size=struct.unpack_from('<Q', b, 8)[0])
        except Exception:
            return None
    return None

def is_link(b):
    return len(b) >= 16 and b[:4] == b'LINK'

def link_subs(b):
    try:
        c = struct.unpack_from('<I', b, 4)[0]
        if c > 2_000_000:
            return []
        return [struct.unpack_from('<II', b, 16 + i * 8) for i in range(c)]
    except Exception:
        return []

def search_buf(b, path, hits, depth=0):
    for w, n in NEEDLES:
        idx = b.find(n)
        if idx != -1:
            # count and show one context
            cnt = b.count(n)
            a = idx
            while a - 2 >= 0 and b[a-2:a] != b'\x00\x00' and (0x20 <= (b[a-2] | b[a-1] << 8)):
                a -= 2
                if idx - a > 40:
                    break
            e = idx
            while e + 1 < len(b) and b[e:e+2] != b'\x00\x00' and e - idx < 40:
                e += 2
            ctx = b[a:e].decode('utf-16-le', 'replace')
            hits.append((path, w, cnt, ctx))
    if depth < 8 and is_link(b):
        for i, (off, size) in enumerate(link_subs(b)):
            if size == 0 or off + size > len(b) or off < 0:
                continue
            sub = b[off:off + size]
            dec = unwrap(sub)
            if dec is not None:
                search_buf(dec, f'{path}[{i}]', hits, depth + 1)
            elif is_link(sub):
                search_buf(sub, f'{path}[{i}]', hits, depth + 1)

hits = []
SP = os.path.dirname(os.path.abspath(__file__))

# exefs modules
for m in ('main_dec.bin', 'sdk_dec.bin', 'subsdk0_dec.bin', 'subsdk1_dec.bin'):
    p = os.path.join(SP, m)
    if os.path.exists(p):
        search_buf(open(p, 'rb').read(), f'exefs/{m}', hits)

# romfs (skip only truly huge/irrelevant)
SRC = r'D:\nsw\rom\노부나가의 야망 신생_일본판\추출원본\romfs'
SKIP = {'MOVIE', 'SNDRES'}
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
        data = bytes(mm)
        mm.close(); f.close()
        search_buf(data, rel, hits)
        dec = unwrap(data)
        if dec is not None:
            search_buf(dec, rel + '(unwrap)', hits)

# dedup + report
print(f'=== {len(hits)} hit locations ===')
seen = set()
for path, w, cnt, ctx in hits:
    key = (path, w)
    if key in seen:
        continue
    seen.add(key)
    print(f'{path}  [{w} x{cnt}]  "{ctx[:50]}"')
print('done')
