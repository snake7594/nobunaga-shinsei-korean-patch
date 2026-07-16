"""Hypothesis: wheel labels stored as FONT GLYPH INDICES, not Unicode.
Get glyph IDs for the wheel kanji from the font charmap, then search all files
for those glyph-id sequences (u16 LE and BE)."""
import struct, os, sys, mmap
import lz4.block
sys.stdout.reconfigure(encoding='utf-8')
SRC = r'D:\nsw\rom\노부나가의 야망 신생_일본판\추출원본\romfs'
SP = os.path.dirname(os.path.abspath(__file__))

def unwrap(b):
    if len(b) >= 24 and b[0] == 1 and b[1] == 1:
        try:
            return lz4.block.decompress(b[24:24 + struct.unpack_from('<Q', b, 16)[0]],
                                        uncompressed_size=struct.unpack_from('<Q', b, 8)[0])
        except Exception:
            return None
    return None

# load font (original res_lang entry 6) charmap section 0
res = open(os.path.join(SRC, r'RES_JP\res_lang.bin'), 'rb').read()
def parse_link(d):
    c = struct.unpack_from('<I', d, 4)[0]
    return [struct.unpack_from('<II', d, 16 + i * 8) for i in range(c)]
toc = parse_link(res)
off, size = toc[6]
g = unwrap(res[off:off + size])
sec0 = struct.unpack_from('<I', g, 0x20)[0]
def gid(ch):
    return struct.unpack_from('<H', g, sec0 + ord(ch) * 2)[0]

WORDS = ['評定', '内政', '任命', '軍事', '外交', '知行', '代官']
gids = {w: [gid(c) for c in w] for w in WORDS}
print('glyph IDs:')
for w, ids in gids.items():
    print(f'  {w}: {ids}')

# build search patterns: each word as glyph-id u16 sequence (LE and BE)
patterns = []
for w, ids in gids.items():
    le = b''.join(struct.pack('<H', i) for i in ids)
    be = b''.join(struct.pack('>H', i) for i in ids)
    patterns.append((w, 'gidLE', le))
    patterns.append((w, 'gidBE', be))

hits = []
def search(b, path, depth=0):
    for w, name, pat in patterns:
        idx = b.find(pat)
        if idx != -1:
            hits.append((path, w, name, b.count(pat), idx))
    if depth < 6 and b[:4] == b'LINK':
        for i, (o, s) in enumerate(parse_link(b) if b[:4] == b'LINK' else []):
            if s == 0 or o + s > len(b):
                continue
            sub = b[o:o + s]
            dec = unwrap(sub)
            search(dec if dec else sub, f'{path}[{i}]', depth + 1)

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

print(f'\n=== glyph-id sequence hits: {len(hits)} ===')
seen = set()
for path, w, name, c, idx in sorted(hits):
    k = (path, w, name)
    if k in seen: continue
    seen.add(k)
    print(f'  {path}: {w} ({name}) x{c} @0x{idx:X}')
print('done' if hits else 'NO glyph-id hits')
