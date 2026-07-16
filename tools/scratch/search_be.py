"""Search all files for wheel words in UTF-16 BIG-ENDIAN and other layouts."""
import struct, os, sys, mmap
import lz4.block
sys.stdout.reconfigure(encoding='utf-8')
SRC = r'D:\nsw\rom\노부나가의 야망 신생_일본판\추출원본\romfs'

WORDS = ['評定', '内政', '任命', '軍事', '外交']
# multiple encodings/layouts
def variants(w):
    return {
        'utf16le': w.encode('utf-16-le'),
        'utf16be': w.encode('utf-16-be'),
    }
ALL = [(w, name, b) for w in WORDS for name, b in variants(w).items()]

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
        return [] if c > 500000 else [struct.unpack_from('<II', d, 16 + i * 8) for i in range(c)]
    except Exception:
        return []

hits = []
def search(b, path, depth=0):
    for w, name, nb in ALL:
        if name == 'utf16be' and b.find(nb) != -1:  # only report BE (LE already known)
            c = b.count(nb)
            idx = b.find(nb)
            hits.append((path, w, name, c, idx))
    if depth < 6 and b[:4] == b'LINK':
        for i, (off, size) in enumerate(parse_link(b)):
            if size == 0 or off + size > len(b):
                continue
            sub = b[off:off + size]
            dec = unwrap(sub)
            search(dec if dec else sub, f'{path}[{i}]', depth + 1)

# exefs
SP = os.path.dirname(os.path.abspath(__file__))
for m in ('main_dec.bin', 'sdk_dec.bin', 'subsdk0_dec.bin', 'subsdk1_dec.bin'):
    p = os.path.join(SP, m)
    if os.path.exists(p):
        search(open(p, 'rb').read(), f'exefs/{m}')

SKIP = {'MOVIE', 'SNDRES'}
for root, dirs, files in os.walk(SRC):
    dirs[:] = [x for x in dirs if x not in SKIP]
    for fn in files:
        p = os.path.join(root, fn)
        if os.path.getsize(p) > 780 * 1024 * 1024:
            continue
        rel = os.path.relpath(p, SRC)
        f = open(p, 'rb'); mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        data = bytes(mm); mm.close(); f.close()
        search(data, rel)
        dec = unwrap(data)
        if dec:
            search(dec, rel + '(unwrap)')

print(f'=== UTF-16BE hits: {len(hits)} ===')
seen = set()
for path, w, name, c, idx in hits:
    k = (path, w)
    if k in seen: continue
    seen.add(k)
    print(f'  {path}: {w} ({name}) x{c} @0x{idx:X}')
print('done' if hits else 'NO big-endian hits anywhere')
