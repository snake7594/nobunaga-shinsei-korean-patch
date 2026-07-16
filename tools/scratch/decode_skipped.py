"""Decode ALL previously-skipped textures (0x08, 0x5C, 0x5F) in res_else/res_eff/res_lang."""
import struct, os, sys, io
import numpy as np
import lz4.block
from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding='utf-8')
SRC = r'D:\nsw\rom\노부나가의 야망 신생_일본판\추출원본\romfs'
OUT = r'D:\nsw\rom\노부나가의 야망 신생_일본판\이미지한글화'
PNG_DIR = os.path.join(OUT, 'png_skipped')
os.makedirs(PNG_DIR, exist_ok=True)

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

def dds_img(linear, w, h, kind):
    if kind == 'BC7':
        dds = bytearray(148)
        struct.pack_into('<4s', dds, 84, b'DX10')
        struct.pack_into('<IIIII', dds, 128, 98, 3, 0, 1, 0)
    elif kind == 'BC4':
        dds = bytearray(148)
        struct.pack_into('<4s', dds, 84, b'DX10')
        struct.pack_into('<IIIII', dds, 128, 80, 3, 0, 1, 0)  # BC4_UNORM
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

def decode_tex(g, want_fmts):
    tbl = struct.unpack_from('<I', g, 0x0C)[0]
    ntex = struct.unpack_from('<I', g, 0x10)[0]
    offs = struct.unpack_from(f'<{ntex}I', g, tbl)
    out = []
    for k, o in enumerate(offs):
        p = tbl + o
        fmt, dxdy = g[p + 1], g[p + 2]
        w, h = 1 << (dxdy & 0xF), 1 << (dxdy >> 4)
        if fmt not in want_fmts or w < 32 or h < 16:
            continue
        ex = struct.unpack_from('<I', g, p + 8)[0]
        end = tbl + offs[k + 1] if k + 1 < ntex else len(g)
        data = g[p + 8 + ex:end]
        try:
            if fmt == 0x5F:
                im = dds_img(bytes(data[:(w//4)*(h//4)*16]), w, h, 'BC7')
            elif fmt == 0x5C:
                im = dds_img(bytes(data[:(w//4)*(h//4)*8]), w, h, 'BC4')
            elif fmt == 0x08:
                im = dds_img(bytes(data[:(w//4)*(h//4)*16]), w, h, 'BC3')
            else:
                continue
            out.append((k, fmt, w, h, im))
        except Exception as e:
            print(f'  decode err fmt=0x{fmt:02X} {w}x{h}: {e}')
    return out

thumbs = []
def walk(blob, path, depth=0):
    if blob[:4] == b'GT1G':
        for k, fmt, w, h, im in decode_tex(blob, (0x08, 0x5C, 0x5F)):
            name = f'{path}_t{k}_f{fmt:02X}'.replace('\\', '_').replace('[', '_').replace(']', '')
            im.save(os.path.join(PNG_DIR, name + '.png'))
            thumbs.append((name, f'0x{fmt:02X} {w}x{h}', im))
        return
    if depth < 6 and blob[:4] == b'LINK':
        for i, (off, size) in enumerate(parse_link(blob)):
            if size == 0 or off + size > len(blob):
                continue
            sub = blob[off:off + size]
            dec = unwrap(sub)
            walk(dec if dec else sub, f'{path}[{i}]', depth + 1)

for rel in (r'RES\res_else.bin', r'RES\res_eff.bin', r'RES_JP\res_lang.bin'):
    data = open(os.path.join(SRC, rel), 'rb').read()
    dec = unwrap(data)
    walk(dec if dec else data, os.path.basename(rel).replace('.bin', ''))

print(f'{len(thumbs)} skipped-format textures decoded')
COLS, CW, CH, CAP = 6, 262, 262, 18
per = 36
for s in range(0, len(thumbs), per):
    chunk = thumbs[s:s + per]
    rows = (len(chunk) + COLS - 1) // COLS
    sheet = Image.new('RGB', (COLS * CW + 8, rows * (CH + CAP) + 8), (18, 18, 28))
    dr = ImageDraw.Draw(sheet)
    for idx, (name, info, im) in enumerate(chunk):
        cx = 8 + (idx % COLS) * CW
        cy = 8 + (idx // COLS) * (CH + CAP)
        bg = Image.new('RGBA', im.size, (40, 40, 60, 255))
        comp = Image.alpha_composite(bg, im).convert('RGB')
        comp.thumbnail((250, 250))
        sheet.paste(comp, (cx, cy))
        dr.text((cx, cy + CH - 12), f'{name[:38]} {info}', fill=(180, 220, 180))
    sheet.save(os.path.join(OUT, 'contact_sheets', f'skipped_{s//per:02d}.jpg'), quality=82)
print('sheets written')
