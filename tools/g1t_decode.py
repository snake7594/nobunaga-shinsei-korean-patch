"""Decode Switch G1T textures (BC1 0x59 / BGRA8 0x01, Tegra block-linear) to PNG.
Block height is auto-detected by smoothness scoring."""
import struct, os, sys, io
import numpy as np
import lz4.block
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
SRC = r'D:\nsw\rom\노부나가의 야망 신생_일본판\추출원본'

def kt_unwrap(blob):
    if blob[0] == 1 and blob[1] == 1:
        dec = struct.unpack_from('<Q', blob, 8)[0]
        comp = struct.unpack_from('<Q', blob, 16)[0]
        return lz4.block.decompress(blob[24:24 + comp], uncompressed_size=dec)
    return blob

def deswizzle(data, width_bytes, height_rows, bh):
    GOB_W, GOB_H = 64, 8
    wg = (width_bytes + GOB_W - 1) // GOB_W
    x = np.arange(width_bytes, dtype=np.int64)[None, :]
    y = np.arange(height_rows, dtype=np.int64)[:, None]
    base = ((y // (GOB_H * bh)) * wg * bh + (x // GOB_W) * bh
            + (y % (GOB_H * bh)) // GOB_H) * 512
    xx = x % GOB_W
    yy = y % GOB_H
    intra = ((xx // 32) * 256 + (yy // 2) * 64 + ((xx % 32) // 16) * 32
             + (yy % 2) * 16 + (xx % 16))
    addr = (base + intra).ravel()
    src = np.frombuffer(data, dtype=np.uint8)
    out = np.zeros(width_bytes * height_rows, dtype=np.uint8)
    ok = addr < len(src)
    out[ok] = src[addr[ok]]
    return out.reshape(height_rows, width_bytes)

def auto_deswizzle(data, width_bytes, height_rows):
    best = None
    for bh in (16, 8, 4, 2, 1):
        lin = deswizzle(data, width_bytes, height_rows, bh)
        a = lin.astype(np.int16)
        score = np.abs(a[1:] - a[:-1]).sum()
        if best is None or score < best[0]:
            best = (score, bh, lin)
    return best[2], best[1]

def bc1_to_png(linear, w, h):
    dds = bytearray(128)
    struct.pack_into('<4s', dds, 0, b'DDS ')
    struct.pack_into('<I', dds, 4, 124)
    struct.pack_into('<I', dds, 8, 0x00081007)
    struct.pack_into('<I', dds, 12, h)
    struct.pack_into('<I', dds, 16, w)
    struct.pack_into('<I', dds, 20, len(linear))
    struct.pack_into('<I', dds, 76, 32)
    struct.pack_into('<I', dds, 80, 0x4)
    struct.pack_into('<4s', dds, 84, b'DXT1')
    struct.pack_into('<I', dds, 108, 0x1000)
    return Image.open(io.BytesIO(bytes(dds) + linear)).convert('RGBA')

def decode_g1t(g):
    tbl = struct.unpack_from('<I', g, 0x0C)[0]
    ntex = struct.unpack_from('<I', g, 0x10)[0]
    offs = struct.unpack_from(f'<{ntex}I', g, tbl)
    imgs = []
    for o in offs:
        p = tbl + o
        fmt, dxdy = g[p + 1], g[p + 2]
        w = 1 << (dxdy >> 4)
        h = 1 << (dxdy & 0xF)
        ex_size = struct.unpack_from('<I', g, p + 8)[0]
        data = g[p + 8 + ex_size:]
        if fmt == 0x59:      # BC1 swizzled
            lin, bh = auto_deswizzle(data, (w // 4) * 8, h // 4)
            imgs.append((bc1_to_png(lin.tobytes(), w, h), f'BC1 {w}x{h} bh={bh}'))
        elif fmt == 0x01:    # BGRA8 swizzled
            lin, bh = auto_deswizzle(data, w * 4, h)
            arr = lin.reshape(h, w, 4)[:, :, [2, 1, 0, 3]]
            imgs.append((Image.fromarray(arr.copy(), 'RGBA'), f'BGRA8 {w}x{h} bh={bh}'))
        else:
            imgs.append((None, f'fmt=0x{fmt:02X} {w}x{h} UNSUPPORTED'))
    return imgs

def get_sub(d, i, j):
    off, size = struct.unpack_from('<II', d, 16 + i * 8)
    blob = d[off:off + size]
    o2, s2 = struct.unpack_from('<II', blob, 16 + j * 8)
    return kt_unwrap(blob[o2:o2 + s2])

if __name__ == '__main__':
    with open(os.path.join(SRC, r'romfs\RES_JP\res_lang.bin'), 'rb') as f:
        d = f.read()
    outdir = sys.argv[1]
    os.makedirs(outdir, exist_ok=True)
    for spec in sys.argv[2].split(','):
        i, j = map(int, spec.split(':'))
        g = get_sub(d, i, j)
        for t, (img, info) in enumerate(decode_g1t(g)):
            if img:
                p = os.path.join(outdir, f'tex_{i}_{j}_{t}.png')
                img.save(p)
                print(f'saved tex_{i}_{j}_{t}.png  {info}')
            else:
                print(f'tex_{i}_{j}_{t}: {info}')
