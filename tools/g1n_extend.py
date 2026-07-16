"""Extend G1N fonts with a full Hangul glyph set (proper new glyphs, no donors),
and rebuild res_lang.bin allowing entry growth.

Usage: python g1n_extend.py <charset.txt> <out res_lang.bin>
charset.txt: UTF-8 file whose unique characters (excluding whitespace) are added.
"""
import struct, sys, os, io
import lz4.block
from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding='utf-8')

SP = os.path.dirname(os.path.abspath(__file__))
SRC = r'D:\nsw\rom\노부나가의 야망 신생_일본판\추출원본'
FONT_REG = os.path.join(SRC, 'SeoulHangangM.ttf')
FONT_BOLD = os.path.join(SRC, 'SeoulHangangB.ttf')

# ---------- KT wrapper ----------
def kt_unwrap(blob):
    dec_size = struct.unpack_from('<Q', blob, 8)[0]
    comp_size = struct.unpack_from('<Q', blob, 16)[0]
    return blob[:24], lz4.block.decompress(blob[24:24 + comp_size], uncompressed_size=dec_size)

def kt_wrap(header24, data):
    comp = lz4.block.compress(data, mode='high_compression', compression=12, store_size=False)
    hdr = bytearray(header24)
    struct.pack_into('<Q', hdr, 8, len(data))
    struct.pack_into('<Q', hdr, 16, len(comp))
    return bytes(hdr) + comp

# ---------- rendering (same tuning as v3, correct h_hi nibble order) ----------
_font_bytes = {}
_ink_cache = {}
_scale_cache = {}

def load_font(path, size):
    if path not in _font_bytes:
        with open(path, 'rb') as f:
            _font_bytes[path] = f.read()
    return ImageFont.truetype(io.BytesIO(_font_bytes[path]), size)

def hangul_ink(ch, font_path, big_size=88):
    key = (ch, font_path)
    if key in _ink_cache:
        return _ink_cache[key]
    img = Image.new('L', (big_size * 3, big_size * 3), 0)
    dr = ImageDraw.Draw(img)
    dr.text((big_size * 3 // 2, big_size * 3 // 2), ch, fill=255,
            font=load_font(font_path, big_size), anchor='mm')
    bbox = img.getbbox()
    ink = img.crop(bbox) if bbox else None
    _ink_cache[key] = ink
    return ink

def scale_factor(font_path, target_ink_h):
    key = (font_path, target_ink_h)
    if key not in _scale_cache:
        ref = hangul_ink('음', font_path)
        _scale_cache[key] = target_ink_h / ref.size[1]
    return _scale_cache[key]

def render_cell(ch, font_path, w, h, target_ink_h, center_y_frac, gamma=1.15):
    ink = hangul_ink(ch, font_path)
    if ink is None:
        return bytes(w * h // 2)  # blank
    f = scale_factor(font_path, target_ink_h)
    nw, nh = max(1, round(ink.size[0] * f)), max(1, round(ink.size[1] * f))
    if nw > w - 2:
        r = (w - 2) / nw
        nw, nh = w - 2, max(1, round(nh * r))
    if nh > h - 2:
        r = (h - 2) / nh
        nh, nw = h - 2, max(1, round(nw * r))
    ink = ink.resize((nw, nh), Image.LANCZOS)
    cell = Image.new('L', (w, h), 0)
    cy = round(h * center_y_frac)
    cell.paste(ink, ((w - nw) // 2, min(max(cy - nh // 2, 0), h - nh)))
    p = cell.load()
    out = bytearray(w * h // 2)
    for y in range(h):
        for x in range(w):
            v = round(((p[x, y] / 255) ** gamma) * 15)
            idx = y * w + x
            out[idx // 2] |= (v << 4) if idx % 2 == 0 else v  # even pixel = HIGH nibble
    return bytes(out)

# ---------- G1N extension ----------
def extend_g1n(g1n, charset, tag):
    hdr_total = struct.unpack_from('<I', g1n, 0x08)[0]
    assert hdr_total == len(g1n)
    first_sec = struct.unpack_from('<I', g1n, 0x0C)[0]
    pool_off = struct.unpack_from('<I', g1n, 0x14)[0]
    nsec = struct.unpack_from('<I', g1n, 0x1C)[0]
    sec_offs = [struct.unpack_from('<I', g1n, 0x20 + 4 * i)[0] for i in range(nsec)]
    bounds = sec_offs + [pool_off]
    pool = bytearray(g1n[pool_off:])

    styles = {0: (FONT_REG, 39 / 48, 24.5 / 48), 1: (FONT_BOLD, 41 / 48, 24.5 / 48)}
    new_sections = []
    for si in range(nsec):
        s, e = sec_offs[si], bounds[si + 1]
        charmap = bytearray(g1n[s:s + 0x20000])
        records = bytearray(g1n[s + 0x20000:e])
        n_rec = len(records) // 12
        assert n_rec * 12 == len(records)
        if si in styles:
            font_path, ink_frac, cy_frac = styles[si]
            # reference metrics from a full-width glyph (一)
            ref_gid = struct.unpack_from('<H', charmap, ord('一') * 2)[0]
            ref_metrics = bytes(records[ref_gid * 12: ref_gid * 12 + 8])
            w, h = ref_metrics[0], ref_metrics[1]
            added = 0
            for ch in charset:
                cp = ord(ch)
                if cp > 0xFFFF:
                    continue
                if struct.unpack_from('<H', charmap, cp * 2)[0] != 0:
                    continue  # already present
                cell = render_cell(ch, font_path, w, h, round(h * ink_frac), cy_frac)
                gid = n_rec + added
                bmp_rel = len(pool)
                pool += cell
                records += ref_metrics + struct.pack('<I', bmp_rel)
                struct.pack_into('<H', charmap, cp * 2, gid)
                added += 1
            print(f'  {tag} sec{si}: +{added} glyphs (cell {w}x{h}, records {n_rec}->{n_rec + added})')
        new_sections.append(bytes(charmap) + bytes(records))

    # reassemble: header+palettes | sections (contiguous) | pool
    out = bytearray(g1n[:first_sec])
    new_offs = []
    for sec in new_sections:
        new_offs.append(len(out))
        out += sec
    new_pool_off = len(out)
    out += pool
    struct.pack_into('<I', out, 0x08, len(out))
    struct.pack_into('<I', out, 0x14, new_pool_off)
    for i, o in enumerate(new_offs):
        struct.pack_into('<I', out, 0x20 + 4 * i, o)
    return bytes(out)

# ---------- res_lang rebuild ----------
def rebuild_res_lang(charset, out_path):
    with open(os.path.join(SRC, r'romfs\RES_JP\res_lang.bin'), 'rb') as f:
        res = f.read()
    count, ver = struct.unpack_from('<II', res, 4)
    toc = [struct.unpack_from('<II', res, 16 + i * 8) for i in range(count)]
    # inter-entry gaps (preserve original padding bytes)
    entries = []
    for i, (off, size) in enumerate(toc):
        end = off + size
        nxt = toc[i + 1][0] if i + 1 < count else len(res)
        gap = res[end:nxt]
        blob = res[off:end]
        entries.append([blob, gap])
    # patch fonts (entries 6, 7)
    for idx in (6, 7):
        hdr, dec = kt_unwrap(entries[idx][0])
        print(f'entry {idx}: extending G1N ({len(dec):,} bytes)...')
        dec2 = extend_g1n(dec, charset, f'font{idx}')
        print(f'  G1N {len(dec):,} -> {len(dec2):,} bytes')
        entries[idx][0] = kt_wrap(hdr, dec2)
    # reassemble with original gap bytes, first entry offset preserved
    out = bytearray(res[:toc[0][0]])
    for i, (blob, gap) in enumerate(entries):
        struct.pack_into('<II', out, 16 + i * 8, len(out), len(blob))
        out += blob
        out += gap
    with open(out_path, 'wb') as f:
        f.write(out)
    print(f'res_lang.bin: {len(res):,} -> {len(out):,} bytes')

if __name__ == '__main__':
    charset_file, out_path = sys.argv[1], sys.argv[2]
    with open(charset_file, encoding='utf-8') as f:
        chars = sorted(set(c for c in f.read() if not c.isspace() and ord(c) > 0x7F))
    print(f'charset: {len(chars)} chars')
    rebuild_res_lang(chars, out_path)
