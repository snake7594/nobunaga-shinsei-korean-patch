"""Decode the 16 G1T entries in res_stage.bin (map-screen resources)."""
import struct, os, sys, io, mmap
import numpy as np
import lz4.block
from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding='utf-8')
OUT = r'D:\nsw\rom\노부나가의 야망 신생_일본판\이미지한글화'
PNG_DIR = os.path.join(OUT, 'png_stage')
os.makedirs(PNG_DIR, exist_ok=True)

def unwrap(b):
    if len(b) >= 24 and b[0] == 1 and b[1] == 1:
        return lz4.block.decompress(b[24:24 + struct.unpack_from('<Q', b, 16)[0]],
                                    uncompressed_size=struct.unpack_from('<Q', b, 8)[0])
    return b

def dds_img(linear, w, h, kind):
    if kind == 'BC7':
        dds = bytearray(148)
        struct.pack_into('<4s', dds, 84, b'DX10')
        struct.pack_into('<IIIII', dds, 128, 98, 3, 0, 1, 0)
    else:
        dds = bytearray(128)
        struct.pack_into('<4s', dds, 84, {'BC1': b'DXT1', 'BC3': b'DXT5'}[kind])
    struct.pack_into('<4s', dds, 0, b'DDS ')
    struct.pack_into('<I', dds, 4, 124)
    struct.pack_into('<I', dds, 8, 0x00081007)
    struct.pack_into('<I', dds, 12, h)
    struct.pack_into('<I', dds, 16, w)
    struct.pack_into('<I', dds, 20, len(linear))
    struct.pack_into('<I', dds, 76, 32)
    struct.pack_into('<I', dds, 80, 0x4)
    struct.pack_into('<I', dds, 108, 0x1000)
    return Image.open(io.BytesIO(bytes(dds) + linear)).convert('RGBA')

f = open(r'D:\nsw\rom\노부나가의 야망 신생_일본판\추출원본\romfs\RES\res_stage.bin', 'rb')
mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
toc = [struct.unpack_from('<II', mm, 16 + i * 8) for i in range(struct.unpack_from('<I', mm, 4)[0])]

thumbs = []
for i in (19, 23, 72, 95, 195, 196, 200, 204, 209, 231, 274, 275, 276, 280, 289, 300):
    off, size = toc[i]
    g = unwrap(bytes(mm[off:off + size]))
    if g[:4] != b'GT1G':
        continue
    tbl = struct.unpack_from('<I', g, 0x0C)[0]
    ntex = struct.unpack_from('<I', g, 0x10)[0]
    offs = struct.unpack_from(f'<{ntex}I', g, tbl)
    for k, o in enumerate(offs):
        p = tbl + o
        fmt, dxdy = g[p + 1], g[p + 2]
        w, h = 1 << (dxdy & 0xF), 1 << (dxdy >> 4)
        if w < 32 or h < 32:
            continue
        ex = struct.unpack_from('<I', g, p + 8)[0]
        end = tbl + offs[k + 1] if k + 1 < ntex else len(g)
        data = g[p + 8 + ex:end]
        try:
            if fmt == 0x59:
                img = dds_img(bytes(data[:(w//4)*(h//4)*8]), w, h, 'BC1')
            elif fmt == 0x5B:
                img = dds_img(bytes(data[:(w//4)*(h//4)*16]), w, h, 'BC3')
            elif fmt == 0x5F:
                img = dds_img(bytes(data[:(w//4)*(h//4)*16]), w, h, 'BC7')
            elif fmt == 0x01:
                arr = np.frombuffer(bytes(data[:w*h*4]), dtype=np.uint8).reshape(h, w, 4)
                img = Image.fromarray(arr[:, :, [2, 1, 0, 3]].copy(), 'RGBA')
            else:
                continue
        except Exception:
            continue
        name = f'S{i:03d}_{k:03d}'
        img.save(os.path.join(PNG_DIR, name + '.png'))
        thumbs.append((name, f'0x{fmt:02X} {w}x{h}', img))

print(f'{len(thumbs)} textures')
COLS, CW, CH, CAP = 6, 262, 262, 18
rows = (len(thumbs) + COLS - 1) // COLS
per = 36
sheets = 0
for s in range(0, len(thumbs), per):
    n = min(per, len(thumbs) - s)
    r = (n + COLS - 1) // COLS
    sheet = Image.new('RGB', (COLS * CW + 8, r * (CH + CAP) + 8), (18, 18, 28))
    dr = ImageDraw.Draw(sheet)
    for idx, (name, info, im) in enumerate(thumbs[s:s + per]):
        cx = 8 + (idx % COLS) * CW
        cy = 8 + (idx // COLS) * (CH + CAP)
        bg = Image.new('RGBA', im.size, (40, 40, 60, 255))
        comp = Image.alpha_composite(bg, im).convert('RGB')
        comp.thumbnail((250, 250))
        sheet.paste(comp, (cx, cy))
        dr.text((cx, cy + CH - 12), f'{name} {info}', fill=(180, 220, 180))
    sheet.save(os.path.join(OUT, 'contact_sheets', f'stage_{sheets:02d}.jpg'), quality=82)
    sheets += 1
print(f'{sheets} sheets')
