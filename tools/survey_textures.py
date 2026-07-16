"""Survey res_lang.bin: enumerate nested LINKDATA entries, find G1T textures,
and diff JP vs SC to locate localized (text) images."""
import struct, sys, os, hashlib
import lz4.block
sys.stdout.reconfigure(encoding='utf-8')

SRC = r'D:\nsw\rom\노부나가의 야망 신생_일본판\추출원본'

def kt_unwrap(blob):
    if len(blob) >= 24 and blob[0] == 1 and blob[1] == 1:
        dec_size = struct.unpack_from('<Q', blob, 8)[0]
        comp_size = struct.unpack_from('<Q', blob, 16)[0]
        try:
            return lz4.block.decompress(blob[24:24 + comp_size], uncompressed_size=dec_size)
        except Exception:
            return blob
    return blob

def parse_link(d):
    if d[:4] != b'LINK':
        return None
    count = struct.unpack_from('<I', d, 4)[0]
    out = []
    for i in range(count):
        off, size = struct.unpack_from('<II', d, 16 + i * 8)
        out.append((off, size))
    return out

def ident(b):
    if b[:4] in (b'GT1G', b'G1TG'):
        return 'G1T'
    if b[:4] == b'LINK':
        return 'LINK'
    if b[:8] == b'_N1G0000':
        return 'G1N'
    return b[:4].hex()

def survey(path, tag):
    with open(path, 'rb') as f:
        d = f.read()
    toc = parse_link(d)
    result = {}  # (i, j) -> (kind, dec_size, sha1, tex_info)
    for i, (off, size) in enumerate(toc):
        blob = d[off:off + size]
        if blob[:4] == b'LINK':
            sub = parse_link(blob)
            for j, (o2, s2) in enumerate(sub):
                raw = blob[o2:o2 + s2]
                dec = kt_unwrap(raw)
                kind = ident(dec)
                h = hashlib.sha1(dec).hexdigest()[:12]
                info = ''
                if kind == 'G1T':
                    ntex = struct.unpack_from('<I', dec, 0x10)[0] if len(dec) > 0x14 else -1
                    info = f'ntex={ntex}'
                result[(i, j)] = (kind, len(dec), h, info)
        else:
            dec = kt_unwrap(blob)
            kind = ident(dec)
            result[(i, -1)] = (kind, len(dec), hashlib.sha1(dec).hexdigest()[:12], '')
    return result

jp = survey(os.path.join(SRC, r'romfs\RES_JP\res_lang.bin'), 'JP')
sc = survey(os.path.join(SRC, r'romfs\RES_SC\res_lang.bin'), 'SC')

from collections import Counter
kinds = Counter(v[0] for v in jp.values())
print(f'JP sub-entries: {len(jp)}, kinds: {dict(kinds)}')

same = diff = jponly = 0
diff_list = []
for k, v in jp.items():
    if k not in sc:
        jponly += 1
        continue
    if v[2] == sc[k][2]:
        same += 1
    else:
        diff += 1
        diff_list.append((k, v))
print(f'identical to SC: {same}, DIFFERENT: {diff}, jp-only: {jponly}')
print('\n=== entries differing from SC (localized content) ===')
g1t_diff = [x for x in diff_list if x[1][0] == 'G1T']
other_diff = [x for x in diff_list if x[1][0] != 'G1T']
print(f'G1T textures differing: {len(g1t_diff)}')
for (i, j), (kind, sz, h, info) in g1t_diff[:60]:
    print(f'  [{i:2}][{j:3}] {sz:10,}B {info}')
print(f'non-G1T differing: {len(other_diff)}')
for (i, j), (kind, sz, h, info) in other_diff[:20]:
    print(f'  [{i:2}][{j:3}] {kind} {sz:,}B')
