"""Search romfs data files for the radial-menu command words (UTF-16LE),
inside raw files and KT-wrapped/LINK containers."""
import os, struct, sys
import lz4.block
sys.stdout.reconfigure(encoding='utf-8')
SRC = r'D:\nsw\rom\노부나가의 야망 신생_일본판\추출원본\romfs'

NEEDLES = [w.encode('utf-16-le') for w in ('評定', '任命', '内政', '軍事')]

def kt_unwrap(blob):
    if len(blob) >= 24 and blob[0] == 1 and blob[1] == 1:
        dec = struct.unpack_from('<Q', blob, 8)[0]
        comp = struct.unpack_from('<Q', blob, 16)[0]
        try:
            return lz4.block.decompress(blob[24:24 + comp], uncompressed_size=dec)
        except Exception:
            return None
    return None

def scan_blob(data, path, depth=0):
    hits = sum(data.count(n) for n in NEEDLES)
    if hits and depth == 0:
        print(f'{path}: {hits} hits (raw)')
    if data[:4] == b'LINK' and depth < 2:
        count = struct.unpack_from('<I', data, 4)[0]
        if count > 100000:
            return
        for i in range(count):
            off, size = struct.unpack_from('<II', data, 16 + i * 8)
            if size == 0 or off + size > len(data):
                continue
            sub = data[off:off + size]
            dec = kt_unwrap(sub)
            if dec:
                h = sum(dec.count(n) for n in NEEDLES)
                if h:
                    print(f'{path} [entry {i}]: {h} hits (wrapped, dec {len(dec):,}B, magic {dec[:4]})')
                if dec[:4] == b'LINK':
                    scan_blob(dec, f'{path}[{i}]', depth + 1)
            elif sub[:4] == b'LINK':
                scan_blob(sub, f'{path}[{i}]', depth + 1)
            else:
                h = sum(sub.count(n) for n in NEEDLES)
                if h:
                    print(f'{path} [entry {i}]: {h} hits (raw sub, {size:,}B, magic {sub[:4].hex()})')

SKIP_DIRS = {'MOVIE', 'SNDRES', 'CONTENTS'}
SKIP_FILES = {'res_face.bin', 'res_stage.bin', 'res_still.bin', 'res_grp.bin', 'res_nature.bin'}
for root, dirs, files in os.walk(SRC):
    dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
    for fn in files:
        if fn in SKIP_FILES:
            continue
        p = os.path.join(root, fn)
        if os.path.getsize(p) > 200 * 1024 * 1024:
            continue
        with open(p, 'rb') as f:
            data = f.read()
        rel = os.path.relpath(p, SRC)
        dec = kt_unwrap(data)
        if dec is not None:
            h = sum(dec.count(n) for n in NEEDLES)
            if h:
                print(f'{rel}: {h} hits (whole-file wrapped)')
            if dec[:4] == b'LINK':
                scan_blob(dec, rel)
        else:
            scan_blob(data, rel)
print('done')
