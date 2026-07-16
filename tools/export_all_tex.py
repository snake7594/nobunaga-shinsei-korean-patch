"""Export all JP/SC-differing G1T textures from res_lang.bin to PNG + contact sheets."""
import struct, os, sys, io, hashlib
import numpy as np
import lz4.block
from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding='utf-8')
SRC = r'D:\nsw\rom\노부나가의 야망 신생_일본판\추출원본'
OUT = r'D:\nsw\rom\노부나가의 야망 신생_일본판\이미지한글화'
PNG_DIR = os.path.join(OUT, 'png_jp')
SHEET_DIR = os.path.join(OUT, 'contact_sheets')
os.makedirs(PNG_DIR, exist_ok=True)
os.makedirs(SHEET_DIR, exist_ok=True)

def kt_unwrap(blob):
    if len(blob) >= 24 and blob[0] == 1 and blob[1] == 1:
        dec = struct.unpack_from('<Q', blob, 8)[0]
        comp = struct.unpack_from('<Q', blob, 16)[0]
        return lz4.block.decompress(blob[24:24 + comp], uncompressed_size=dec)
    return blob

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
    """Returns list of (Image|None, info)."""
    tbl = struct.unpack_from('<I', g, 0x0C)[0]
    ntex = struct.unpack_from('<I', g, 0x10)[0]
    offs = struct.unpack_from(f'<{ntex}I', g, tbl)
    out = []
    for k, o in enumerate(offs):
        p = tbl + o
        fmt, dxdy = g[p + 1], g[p + 2]
        w = 1 << (dxdy & 0xF)      # low nibble = width
        h = 1 << (dxdy >> 4)       # high nibble = height
        ex = struct.unpack_from('<I', g, p + 8)[0]
        end = tbl + offs[k + 1] if k + 1 < ntex else len(g)
        data = g[p + 8 + ex:end]
        try:
            if fmt == 0x59:
                need = (w // 4) * (h // 4) * 8
                out.append((bc_to_img(bytes(data[:need]), w, h, b'DXT1'), f'BC1 {w}x{h}'))
            elif fmt == 0x5B:
                need = (w // 4) * (h // 4) * 16
                out.append((bc_to_img(bytes(data[:need]), w, h, b'DXT5'), f'BC3 {w}x{h}'))
            elif fmt == 0x01:
                need = w * h * 4
                arr = np.frombuffer(data[:need], dtype=np.uint8).reshape(h, w, 4)
                out.append((Image.fromarray(arr[:, :, [2, 1, 0, 3]].copy(), 'RGBA'), f'BGRA8 {w}x{h}'))
            else:
                out.append((None, f'fmt0x{fmt:02X} {w}x{h}'))
        except Exception as e:
            out.append((None, f'ERR {e}'))
    return out

def parse_link(d):
    count = struct.unpack_from('<I', d, 4)[0]
    return [struct.unpack_from('<II', d, 16 + i * 8) for i in range(count)]

def load_subs(path):
    with open(path, 'rb') as f:
        d = f.read()
    subs = {}
    for i, (off, size) in enumerate(parse_link(d)):
        blob = d[off:off + size]
        if blob[:4] == b'LINK':
            for j, (o2, s2) in enumerate(parse_link(blob)):
                dec = kt_unwrap(blob[o2:o2 + s2])
                subs[(i, j)] = dec
    return subs

jp = load_subs(os.path.join(SRC, r'romfs\RES_JP\res_lang.bin'))
sc = load_subs(os.path.join(SRC, r'romfs\RES_SC\res_lang.bin'))

targets = []
for k, v in sorted(jp.items()):
    if v[:4] == b'GT1G' and (k not in sc or hashlib.sha1(v).digest() != hashlib.sha1(sc[k]).digest()):
        targets.append(k)
print(f'{len(targets)} differing G1T textures to export')

BG = (28, 28, 44, 255)
thumbs = []
fails = []
for (i, j) in targets:
    imgs = decode_g1t(jp[(i, j)])
    for t, (img, info) in enumerate(imgs):
        name = f'{i:02d}_{j:03d}_{t}'
        if img is None:
            fails.append((name, info))
            continue
        img.save(os.path.join(PNG_DIR, name + '.png'))
        bg = Image.new('RGBA', img.size, BG)
        comp = Image.alpha_composite(bg, img).convert('RGB')
        comp.thumbnail((256, 256))
        thumbs.append((name, info, comp))

print(f'exported {len(thumbs)} PNGs, failures: {len(fails)}')
for f_ in fails[:10]:
    print('  FAIL', f_)

# contact sheets: 6 cols x 6 rows
COLS, ROWS = 6, 6
CW, CH, CAP = 262, 262, 18
per = COLS * ROWS
for s in range(0, len(thumbs), per):
    sheet = Image.new('RGB', (COLS * CW + 8, ROWS * (CH + CAP) + 8), (18, 18, 28))
    dr = ImageDraw.Draw(sheet)
    for idx, (name, info, im) in enumerate(thumbs[s:s + per]):
        cx = 8 + (idx % COLS) * CW
        cy = 8 + (idx // COLS) * (CH + CAP)
        sheet.paste(im, (cx + (250 - im.width) // 2, cy + (250 - im.height) // 2))
        dr.text((cx + 2, cy + CH - 12), f'{name}  {info}', fill=(180, 220, 180))
    n = s // per
    sheet.save(os.path.join(SHEET_DIR, f'sheet_{n:02d}.jpg'), quality=82)
print(f'{(len(thumbs) + per - 1) // per} contact sheets written to {SHEET_DIR}')
