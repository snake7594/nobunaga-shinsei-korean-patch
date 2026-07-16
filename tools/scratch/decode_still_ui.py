"""Decode UI-candidate textures in res_still entries 1,2,3 (non-128 sizes)."""
import struct, os, sys, io, mmap
import numpy as np
import lz4.block
from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding='utf-8')
OUT = r'D:\nsw\rom\노부나가의 야망 신생_일본판\이미지한글화'

def unwrap(b):
    if len(b) >= 24 and b[0] == 1 and b[1] == 1:
        return lz4.block.decompress(b[24:24 + struct.unpack_from('<Q', b, 16)[0]],
                                    uncompressed_size=struct.unpack_from('<Q', b, 8)[0])
    return b

def parse_link(d):
    return [struct.unpack_from('<II', d, 16 + i * 8) for i in range(struct.unpack_from('<I', d, 4)[0])]

def img_from(fmt, w, h, data):
    if fmt in (0x59, 0x5B, 0x5F):
        fourcc = {0x59: b'DXT1', 0x5B: b'DXT5'}.get(fmt)
        dds = bytearray(148 if fmt == 0x5F else 128)
        struct.pack_into('<4s', dds, 0, b'DDS ')
        struct.pack_into('<I', dds, 4, 124)
        struct.pack_into('<I', dds, 8, 0x00081007)
        struct.pack_into('<I', dds, 12, h)
        struct.pack_into('<I', dds, 16, w)
        need = (w // 4) * (h // 4) * (8 if fmt == 0x59 else 16)
        struct.pack_into('<I', dds, 20, need)
        struct.pack_into('<I', dds, 76, 32)
        struct.pack_into('<I', dds, 80, 0x4)
        if fmt == 0x5F:
            struct.pack_into('<4s', dds, 84, b'DX10')
            struct.pack_into('<IIIII', dds, 128, 98, 3, 0, 1, 0)
        else:
            struct.pack_into('<4s', dds, 84, fourcc)
        struct.pack_into('<I', dds, 108, 0x1000)
        return Image.open(io.BytesIO(bytes(dds) + bytes(data[:need]))).convert('RGBA')
    elif fmt == 0x01:
        arr = np.frombuffer(bytes(data[:w * h * 4]), dtype=np.uint8).reshape(h, w, 4)
        return Image.fromarray(arr[:, :, [2, 1, 0, 3]].copy(), 'RGBA')
    return None

f = open(r'D:\nsw\rom\노부나가의 야망 신생_일본판\추출원본\romfs\RES\res_still.bin', 'rb')
mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
toc = parse_link(mm)

for ei in (1, 2, 3):
    off, size = toc[ei]
    blob = bytes(mm[off:off + size])
    subs = parse_link(blob)
    thumbs = []
    for j, (o2, s2) in enumerate(subs):
        if s2 == 0:
            continue
        g = unwrap(blob[o2:o2 + s2])
        if g[:4] != b'GT1G':
            continue
        tbl = struct.unpack_from('<I', g, 0x0C)[0]
        ntex = struct.unpack_from('<I', g, 0x10)[0]
        offs = struct.unpack_from(f'<{ntex}I', g, tbl)
        for t, o in enumerate(offs):
            p = tbl + o
            fmt, dxdy = g[p + 1], g[p + 2]
            w, h = 1 << (dxdy & 0xF), 1 << (dxdy >> 4)
            if w < 64 or h < 64:
                continue
            ex = struct.unpack_from('<I', g, p + 8)[0]
            end = tbl + offs[t + 1] if t + 1 < ntex else len(g)
            try:
                im = img_from(fmt, w, h, g[p + 8 + ex:end])
            except Exception:
                im = None
            if im:
                thumbs.append((f'{j}_{t}', f'0x{fmt:02X} {w}x{h}', im))
        if len(thumbs) >= 130:
            break
    # sheet
    COLS, CW, CH, CAP = 6, 262, 200, 18
    per = 36
    for s in range(0, len(thumbs), per):
        chunk = thumbs[s:s + per]
        rows = (len(chunk) + COLS - 1) // COLS
        sheet = Image.new('RGB', (COLS * CW + 8, rows * (CH + CAP) + 8), (20, 20, 30))
        dr = ImageDraw.Draw(sheet)
        for idx, (name, info, im) in enumerate(chunk):
            cx = 8 + (idx % COLS) * CW
            cy = 8 + (idx // COLS) * (CH + CAP)
            bg = Image.new('RGBA', im.size, (40, 40, 60, 255))
            comp = Image.alpha_composite(bg, im).convert('RGB')
            comp.thumbnail((250, 190))
            sheet.paste(comp, (cx, cy))
            dr.text((cx, cy + CH - 12), f'{name} {info}', fill=(180, 220, 180))
        sheet.save(os.path.join(OUT, 'contact_sheets', f'still_e{ei}_{s//per}.jpg'), quality=80)
    print(f'entry {ei}: {len(thumbs)} UI-size textures -> sheets')
mm.close(); f.close()
