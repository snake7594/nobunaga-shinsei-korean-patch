"""Decode UI textures from RES/res_grp.bin (graphics archive) to find radial menu."""
import struct, os, sys, io
import numpy as np
import lz4.block
from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding='utf-8')
SRC = r'D:\nsw\rom\노부나가의 야망 신생_일본판\추출원본'
OUT = r'D:\nsw\rom\노부나가의 야망 신생_일본판\이미지한글화'
PNG_DIR = os.path.join(OUT, 'png_grp')
os.makedirs(PNG_DIR, exist_ok=True)

def kt_unwrap(blob):
    if len(blob) >= 24 and blob[0] == 1 and blob[1] == 1:
        dec = struct.unpack_from('<Q', blob, 8)[0]
        comp = struct.unpack_from('<Q', blob, 16)[0]
        try:
            return lz4.block.decompress(blob[24:24 + comp], uncompressed_size=dec)
        except Exception:
            return None
    return None

def parse_link(d):
    count = struct.unpack_from('<I', d, 4)[0]
    return [struct.unpack_from('<II', d, 16 + i * 8) for i in range(count)]

def bc_to_img(linear, w, h, fourcc):
    dds = bytearray(128)
    struct.pack_into('<4s', dds, 0, b'DDS ')
    struct.pack_into('<I', dds, 4, 124)
    struct.pack_into('<I', dds, 8, 0x00081007)
    struct.pack_into('<I', dds, 12, h)
    struct.pack_into('<I', dds, 16, w)
    struct.pack_into('<I', dds, 20, len(linear))
    struct.pack_into('<I', dds, 76, 32)
    struct.pack_into('<I', dds, 80, 0x4)
    struct.pack_into('<4s', dds, 84, fourcc)
    struct.pack_into('<I', dds, 108, 0x1000)
    return Image.open(io.BytesIO(bytes(dds) + linear)).convert('RGBA')

def decode_g1t(g):
    tbl = struct.unpack_from('<I', g, 0x0C)[0]
    ntex = struct.unpack_from('<I', g, 0x10)[0]
    offs = struct.unpack_from(f'<{ntex}I', g, tbl)
    out = []
    for k, o in enumerate(offs):
        p = tbl + o
        fmt, dxdy = g[p + 1], g[p + 2]
        w = 1 << (dxdy & 0xF)
        h = 1 << (dxdy >> 4)
        ex = struct.unpack_from('<I', g, p + 8)[0]
        end = tbl + offs[k + 1] if k + 1 < ntex else len(g)
        data = g[p + 8 + ex:end]
        try:
            if fmt == 0x59:
                out.append((bc_to_img(bytes(data[:(w//4)*(h//4)*8]), w, h, b'DXT1'), f'BC1 {w}x{h}'))
            elif fmt == 0x5B:
                out.append((bc_to_img(bytes(data[:(w//4)*(h//4)*16]), w, h, b'DXT5'), f'BC3 {w}x{h}'))
            elif fmt == 0x01:
                arr = np.frombuffer(bytes(data[:w*h*4]), dtype=np.uint8).reshape(h, w, 4)
                out.append((Image.fromarray(arr[:, :, [2, 1, 0, 3]].copy(), 'RGBA'), f'BGRA8 {w}x{h}'))
            else:
                out.append((None, f'fmt0x{fmt:02X} {w}x{h}'))
        except Exception as e:
            out.append((None, f'ERR {e}'))
    return out

with open(os.path.join(SRC, r'romfs\RES\res_grp.bin'), 'rb') as f:
    d = f.read()
toc = parse_link(d)
thumbs = []
n_g1t = 0
unsup = {}
for i, (off, size) in enumerate(toc):
    blob = d[off:off + size]
    candidates = []
    if blob[:4] == b'LINK':
        for j, (o2, s2) in enumerate(parse_link(blob)):
            sub = blob[o2:o2 + s2]
            dec = kt_unwrap(sub) or sub
            candidates.append((f'{i:03d}_{j:03d}', dec))
    else:
        dec = kt_unwrap(blob) or blob
        candidates.append((f'{i:03d}', dec))
    for name, g in candidates:
        if g[:4] != b'GT1G':
            continue
        n_g1t += 1
        for t, (img, info) in enumerate(decode_g1t(g)):
            if img is None:
                unsup[info.split()[0]] = unsup.get(info.split()[0], 0) + 1
                continue
            if img.width < 16 or img.height < 16:
                continue
            fname = f'G{name}_{t:03d}'
            img.save(os.path.join(PNG_DIR, fname + '.png'))
            thumbs.append((fname, info, img))
print(f'{n_g1t} G1T found, {len(thumbs)} textures decoded, unsupported: {unsup}')

BG = (28, 28, 44, 255)
COLS, ROWS, CW, CH, CAP = 6, 6, 262, 262, 18
per = COLS * ROWS
sheets = 0
for s in range(0, len(thumbs), per):
    sheet = Image.new('RGB', (COLS * CW + 8, ROWS * (CH + CAP) + 8), (18, 18, 28))
    dr = ImageDraw.Draw(sheet)
    for idx, (name, info, im) in enumerate(thumbs[s:s + per]):
        cx = 8 + (idx % COLS) * CW
        cy = 8 + (idx // COLS) * (CH + CAP)
        bg = Image.new('RGBA', im.size, BG)
        comp = Image.alpha_composite(bg, im).convert('RGB')
        comp.thumbnail((250, 250))
        sheet.paste(comp, (cx + (250 - comp.width) // 2, cy + (250 - comp.height) // 2))
        dr.text((cx + 2, cy + CH - 12), f'{name} {info}', fill=(180, 220, 180))
    sheet.save(os.path.join(OUT, 'contact_sheets', f'grp_{sheets:02d}.jpg'), quality=82)
    sheets += 1
print(f'{sheets} sheets')
