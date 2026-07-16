"""Last-resort hunt: search res_face + check for interleaved/split kanji in MSG,
and scan every PARAM/FLOW file raw for individual wheel kanji."""
import struct, os, sys, mmap
import lz4.block
sys.stdout.reconfigure(encoding='utf-8')
SRC = r'D:\nsw\rom\노부나가의 야망 신생_일본판\추출원본\romfs'

WORDS = ['評定', '内政', '任命', '軍事', '外交']
# individual chars for interleave detection
CHARS = list('評定内政任命軍事外交')

def unwrap(b):
    if len(b) >= 24 and b[0] == 1 and b[1] == 1:
        try:
            return lz4.block.decompress(b[24:24 + struct.unpack_from('<Q', b, 16)[0]],
                                        uncompressed_size=struct.unpack_from('<Q', b, 8)[0])
        except Exception:
            return None
    return None

# 1) res_face raw search (memory-mapped)
print('--- res_face.bin raw UTF-16 search ---')
p = os.path.join(SRC, r'RES\res_face.bin')
f = open(p, 'rb'); mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
for w in WORDS:
    n = w.encode('utf-16-le')
    c = 0; idx = mm.find(n)
    while idx != -1 and c < 3:
        c += 1; idx = mm.find(n, idx + 2)
    if c:
        print(f'  {w}: found (>= {c})')
print('  (none above = not in res_face)')
mm.close(); f.close()

# 2) interleaved check: in original msggame/strdata, find 評 then 定 within 8 bytes
print('\n--- interleaved kanji check in MSG (original, decompressed) ---')
for fn in ('strdata', 'msggame', 'ev_strdata'):
    d = unwrap(open(os.path.join(SRC, f'MSG\\JP\\{fn}.bin'), 'rb').read())
    for a, b in (('評', '定'), ('内', '政'), ('任', '命'), ('軍', '事'), ('外', '交')):
        na, nb = a.encode('utf-16-le'), b.encode('utf-16-le')
        # find pairs where a and b are 2..8 bytes apart (interleaved, not adjacent)
        found = 0
        i = d.find(na)
        while i != -1:
            j = d.find(nb, i + 2, i + 12)
            if j != -1 and j != i + 2:  # not immediately adjacent
                found += 1
            i = d.find(na, i + 2)
        if found:
            print(f'  {fn}: {a}..{b} interleaved(non-adjacent) x{found}')

# 3) PARAM/FLOW/AI raw scan for individual wheel chars (any pattern)
print('\n--- PARAM/FLOW/AI/SUBMIT scan for wheel kanji (raw + unwrap) ---')
for sub in ('PARAM', 'FLOW', 'AI', 'SUBMIT', 'SCENARIO'):
    root = os.path.join(SRC, sub)
    if not os.path.isdir(root):
        continue
    hits = {}
    for r, _, files in os.walk(root):
        for fn in files:
            fp = os.path.join(r, fn)
            data = open(fp, 'rb').read()
            bufs = [data]
            dec = unwrap(data)
            if dec:
                bufs.append(dec)
            for buf in bufs:
                for w in WORDS:
                    if buf.count(w.encode('utf-16-le')):
                        hits.setdefault(os.path.relpath(fp, SRC), []).append(w)
    if hits:
        for k, v in hits.items():
            print(f'  {k}: {set(v)}')
    else:
        print(f'  {sub}: none')
print('done')
