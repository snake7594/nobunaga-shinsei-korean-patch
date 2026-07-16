"""Verify v1.2 res_lang: all entries parse, fonts intact, replaced textures decode."""
import struct, os, sys, io
import numpy as np
import lz4.block
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))
PATH = r'D:\nsw\rom\노부나가의 야망 신생_일본판\한글패치_테스트\romfs\RES_JP\res_lang.bin'

def kt_unwrap(blob):
    dec = struct.unpack_from('<Q', blob, 8)[0]
    comp = struct.unpack_from('<Q', blob, 16)[0]
    return lz4.block.decompress(blob[24:24 + comp], uncompressed_size=dec)

def parse_link(d):
    count = struct.unpack_from('<I', d, 4)[0]
    return [struct.unpack_from('<II', d, 16 + i * 8) for i in range(count)]

def bc3_to_img(linear, w, h):
    dds = bytearray(128)
    struct.pack_into('<4s', dds, 0, b'DDS ')
    struct.pack_into('<I', dds, 4, 124)
    struct.pack_into('<I', dds, 8, 0x00081007)
    struct.pack_into('<I', dds, 12, h)
    struct.pack_into('<I', dds, 16, w)
    struct.pack_into('<I', dds, 20, len(linear))
    struct.pack_into('<I', dds, 76, 32)
    struct.pack_into('<I', dds, 80, 0x4)
    struct.pack_into('<4s', dds, 84, b'DXT5')
    struct.pack_into('<I', dds, 108, 0x1000)
    return Image.open(io.BytesIO(bytes(dds) + linear)).convert('RGBA')

with open(PATH, 'rb') as f:
    res = f.read()
toc = parse_link(res)
print(f'outer entries: {len(toc)}, file {len(res):,}B')

ok = 0
for i, (off, size) in enumerate(toc):
    blob = res[off:off + size]
    try:
        if blob[:4] == b'LINK':
            for o2, s2 in parse_link(blob):
                sub = blob[o2:o2 + s2]
                if len(sub) >= 24 and sub[0] == 1 and sub[1] == 1:
                    kt_unwrap(sub)
            ok += 1
        elif blob[0] == 1 and blob[1] == 1:
            kt_unwrap(blob)
            ok += 1
    except Exception as e:
        print(f'entry {i} FAIL: {e}')
print(f'entries OK: {ok}/{len(toc)}')

# font check
for idx in (6, 7):
    off, size = toc[idx]
    g = kt_unwrap(res[off:off + size])
    assert g[:4] == b'_N1G' and struct.unpack_from('<I', g, 8)[0] == len(g)
    s0 = struct.unpack_from('<I', g, 0x20)[0]
    gid = struct.unpack_from('<H', g, s0 + ord('한') * 2)[0]
    print(f'font entry {idx}: OK, 한={gid}')

# decode replaced textures for visual check
def sub_g1t(entry_idx, sub_idx):
    off, size = toc[entry_idx]
    blob = res[off:off + size]
    subs = parse_link(blob)
    o2, s2 = subs[sub_idx]
    return kt_unwrap(blob[o2:o2 + s2])

previews = []
for (ei, si, label) in [(3, 6, 'jihaeng'), (3, 14, 'pyeongjeong'), (3, 45, 'scenario'), (1, 2, 'warning')]:
    g = sub_g1t(ei, si)
    tbl = struct.unpack_from('<I', g, 0x0C)[0]
    p = tbl + struct.unpack_from('<I', g, tbl)[0]
    fmt, dxdy = g[p + 1], g[p + 2]
    w = 1 << (dxdy & 0xF)
    h = 1 << (dxdy >> 4)
    ex = struct.unpack_from('<I', g, p + 8)[0]
    data = g[p + 8 + ex:]
    if fmt == 0x5B:
        img = bc3_to_img(bytes(data[:(w // 4) * (h // 4) * 16]), w, h)
    else:
        arr = np.frombuffer(data[:w * h * 4], dtype=np.uint8).reshape(h, w, 4)
        img = Image.fromarray(arr[:, :, [2, 1, 0, 3]].copy(), 'RGBA')
    bg = Image.new('RGBA', img.size, (30, 30, 50, 255))
    comp = Image.alpha_composite(bg, img).convert('RGB')
    previews.append((label, comp))
    print(f'[{ei}][{si}] {fmt:#x} {w}x{h} decoded')

sheet_h = sum(min(p.height, 200) + 10 for _, p in previews)
sheet = Image.new('RGB', (1050, sheet_h + 10), (20, 20, 30))
y = 5
for label, p in previews:
    p.thumbnail((1024, 200))
    sheet.paste(p, (10, y))
    y += p.height + 10
sheet.save(os.path.join(SP, 'v12_check.jpg'), quality=88)
print('v12_check.jpg saved')
