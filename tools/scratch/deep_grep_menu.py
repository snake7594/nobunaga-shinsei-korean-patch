"""Exhaustively search main executable + every romfs file (raw, wrapped, and LINK subs)
for the radial-menu command words in UTF-16LE."""
import struct, os, sys, mmap
import lz4.block
sys.stdout.reconfigure(encoding='utf-8')

WORDS = ['評定', '内政', '任命', '軍事', '外交', '知行']
NEEDLES = [(w, w.encode('utf-16-le')) for w in WORDS]

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
        return [struct.unpack_from('<II', d, 16 + i * 8) for i in range(c)] if c < 500000 else []
    except Exception:
        return []

def count(data, tag):
    hits = {w: data.count(n) for w, n in NEEDLES}
    hits = {k: v for k, v in hits.items() if v}
    if hits:
        print(f'{tag}: {hits}')
        return True
    return False

# 1) main executable (decompressed)
SP = os.path.dirname(os.path.abspath(__file__))
mainp = os.path.join(SP, 'main_dec.bin')
if os.path.exists(mainp):
    count(open(mainp, 'rb').read(), 'exefs/main(decompressed)')
for m in ('sdk_dec.bin', 'subsdk0_dec.bin', 'subsdk1_dec.bin'):
    p = os.path.join(SP, m)
    if os.path.exists(p):
        count(open(p, 'rb').read(), f'exefs/{m}')

# 2) all romfs files
SRC = r'D:\nsw\rom\노부나가의 야망 신생_일본판\추출원본\romfs'
SKIP = {'MOVIE', 'SNDRES'}
for root, dirs, files in os.walk(SRC):
    dirs[:] = [x for x in dirs if x not in SKIP]
    for fn in files:
        p = os.path.join(root, fn)
        if os.path.getsize(p) > 780 * 1024 * 1024:
            continue
        rel = os.path.relpath(p, SRC)
        if rel.startswith('MSG'):
            continue  # already translated
        f = open(p, 'rb')
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        data = bytes(mm)
        mm.close(); f.close()
        # raw
        count(data, rel + '(raw)')
        # whole-file unwrap
        dec = unwrap(data)
        if dec:
            count(dec, rel + '(unwrapped)')
        # LINK subs (one level)
        top = dec if (dec and dec[:4] == b'LINK') else (data if data[:4] == b'LINK' else None)
        if top:
            for i, (off, size) in enumerate(parse_link(top)):
                if size == 0 or off + size > len(top):
                    continue
                sub = top[off:off + size]
                d2 = unwrap(sub)
                if d2:
                    count(d2, f'{rel}[{i}](unwrapped)')
                elif count(sub, f'{rel}[{i}](raw sub)'):
                    pass
print('done')
