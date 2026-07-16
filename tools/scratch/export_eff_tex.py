"""Decode BC7 effect textures from res_eff.bin entries 5-8."""
import struct, os, sys, io
import numpy as np
import lz4.block
from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding='utf-8')
OUT = r'D:\nsw\rom\노부나가의 야망 신생_일본판\이미지한글화'
PNG_DIR = os.path.join(OUT, 'png_eff')
os.makedirs(PNG_DIR, exist_ok=True)

def parse_link(d):
    c = struct.unpack_from('<I', d, 4)[0]
    return [struct.unpack_from('<II', d, 16 + i * 8) for i in range(c)]

def unwrap(b):
    if len(b) >= 24 and b[0] == 1 and b[1] == 1:
        return lz4.block.decompress(b[24:24 + struct.unpack_from('<Q', b, 16)[0]],
                                    uncompressed_size=struct.unpack_from('<Q', b, 8)[0])
    return b

def bc7_img(linear, w, h):
    dds = bytearray(148)
    struct.pack_into('<4s', dds, 0, b'DDS ')
    struct.pack_into('<I', dds, 4, 124)
    struct.pack_into('<I', dds, 8, 0x00081007)
    struct.pack_into('<I', dds, 12, h)
    struct.pack_into('<I', dds, 16, w)
    struct.pack_into('<I', dds, 20, len(linear))
    struct.pack_into('<I', dds, 76, 32)
    struct.pack_into('<I', dds, 80, 0x4)
    struct.pack_into('<4s', dds, 84, b'DX10')
    struct.pack_into('<I', dds, 108, 0x1000)
    struct.pack_into('<IIIII', dds, 128, 98, 3, 0, 1, 0)
    return Image.open(io.BytesIO(bytes(dds) + linear)).convert('RGBA')

d = open(r'D:\nsw\rom\노부나가의 야망 신생_일본판\추출원본\romfs\RES\res_eff.bin', 'rb').read()
toc = parse_link(d)
thumbs = []
for i in (5, 6, 7, 8):
    off, size = toc[i]
    g = unwrap(d[off:off + size])
    tbl = struct.unpack_from('<I', g, 0x0C)[0]
    ntex = struct.unpack_from('<I', g, 0x10)[0]
    offs = struct.unpack_from(f'<{ntex}I', g, tbl)
    n = 0
    for k, o in enumerate(offs):
        p = tbl + o
        fmt, dxdy = g[p + 1], g[p + 2]
        w, h = 1 << (dxdy & 0xF), 1 << (dxdy >> 4)
        if fmt != 0x5F or w < 32 or h < 32:
            continue
        ex = struct.unpack_from('<I', g, p + 8)[0]
        end = tbl + offs[k + 1] if k + 1 < ntex else len(g)
        data = g[p + 8 + ex:end]
        try:
            img = bc7_img(bytes(data[:(w // 4) * (h // 4) * 16]), w, h)
        except Exception:
            continue
        name = f'F{i}_{k:03d}'
        img.save(os.path.join(PNG_DIR, name + '.png'))
        thumbs.append((name, f'{w}x{h}', img))
        n += 1
    print(f'entry {i}: {n} BC7 textures decoded')

COLS, ROWS, CW, CH, CAP = 8, 8, 200, 200, 16
per = COLS * ROWS
sheets = 0
for s in range(0, len(thumbs), per):
    sheet = Image.new('RGB', (COLS * CW + 8, ROWS * (CH + CAP) + 8), (18, 18, 28))
    dr = ImageDraw.Draw(sheet)
    for idx, (name, info, im) in enumerate(thumbs[s:s + per]):
        cx = 8 + (idx % COLS) * CW
        cy = 8 + (idx // COLS) * (CH + CAP)
        bg = Image.new('RGBA', im.size, (40, 40, 60, 255))
        comp = Image.alpha_composite(bg, im).convert('RGB')
        comp.thumbnail((190, 190))
        sheet.paste(comp, (cx, cy))
        dr.text((cx, cy + CH - 10), f'{name} {info}', fill=(180, 220, 180))
    sheet.save(os.path.join(OUT, 'contact_sheets', f'eff_{sheets:02d}.jpg'), quality=80)
    sheets += 1
print(f'{len(thumbs)} textures, {sheets} sheets')
