"""Korean output test patch builder for Nobunaga's Ambition: Shinsei (Switch).

- Injects Hangul glyphs into G1N fonts (hijacks rare-kanji glyph slots; no size change)
- Replaces title-menu strings in strdata with equal-length Korean text
- Rebuilds MSG/JP/strdata.bin and RES_JP/res_lang.bin
"""
import struct, sys, os
import lz4.block
from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding='utf-8')

SRC = r'D:\nsw\rom\노부나가의 야망 신생_일본판\추출원본'
OUT = r'D:\nsw\rom\노부나가의 야망 신생_일본판\한글패치_테스트'
SP = sys.argv[1] if len(sys.argv) > 1 else '.'

# title menu: section1 [1] 初めから -> 처음부터, [2] 続きから -> 이어하기 (same UTF-16 length!)
REPLACEMENTS = [('初めから', '처음부터'), ('続きから', '이어하기')]
HANGUL = sorted(set(''.join(k for _, k in REPLACEMENTS)))
DONOR_POOL = ['鬻', '靨', '齟', '齬', '鸞', '麝', '龕', '彝', '齷', '齪', '鼾', '黌',
              '躑', '躅', '顳', '顴', '鬣', '鰥', '黐', '齲']

FONT_REG = r'C:\Windows\Fonts\malgun.ttf'
FONT_BOLD = r'C:\Windows\Fonts\malgunbd.ttf'

# ---------- KT wrapper ----------
def kt_unwrap(blob):
    assert blob[0] == 1 and blob[1] == 1
    dec_size = struct.unpack_from('<Q', blob, 8)[0]
    comp_size = struct.unpack_from('<Q', blob, 16)[0]
    return blob[:24], lz4.block.decompress(blob[24:24 + comp_size], uncompressed_size=dec_size)

def kt_wrap(header24, data):
    comp = lz4.block.compress(data, mode='high_compression', compression=12, store_size=False)
    hdr = bytearray(header24)
    struct.pack_into('<Q', hdr, 8, len(data))
    struct.pack_into('<Q', hdr, 16, len(comp))
    return bytes(hdr) + comp

# ---------- glyph rendering ----------
def render_cell(ch, font_path, w, h):
    """Render a Hangul syllable into a w x h 4bpp cell, ink centered like the kanji glyphs."""
    big = max(w, h) * 3
    img = Image.new('L', (big, big), 0)
    dr = ImageDraw.Draw(img)
    fnt = ImageFont.truetype(font_path, round(h * 44 / 48))
    dr.text((big // 2, big // 2), ch, fill=255, font=fnt, anchor='mm')
    bbox = img.getbbox()
    assert bbox, f'empty render for {ch}'
    ink = img.crop(bbox)
    iw, ih = ink.size
    assert iw <= w and ih <= h, f'{ch}: ink {iw}x{ih} exceeds cell {w}x{h}'
    cell = Image.new('L', (w, h), 0)
    # kanji ink is centered around (24, 26) in a 48x48 cell; scale proportionally
    cx, cy = w // 2, round(h * 26 / 48)
    cell.paste(ink, (cx - iw // 2, min(cy - ih // 2, h - ih)))
    px = cell.load()
    out = bytearray(w * h // 2)
    for y in range(h):
        for x in range(w):
            v = (px[x, y] * 15 + 127) // 255
            idx = y * w + x
            if idx % 2 == 0:
                out[idx // 2] |= v
            else:
                out[idx // 2] |= v << 4
    return bytes(out)

# ---------- G1N patch ----------
def patch_g1n(g1n, tag):
    d = bytearray(g1n)
    pool = struct.unpack_from('<I', d, 0x14)[0]
    nsec = struct.unpack_from('<I', d, 0x1C)[0]
    secs = [struct.unpack_from('<I', d, 0x20 + 4 * i)[0] for i in range(nsec)]
    styles = [FONT_REG, FONT_BOLD]  # section 0 = regular, 1 = bold
    for si in (0, 1):
        s = secs[si]
        cm_off = s
        rec_off = s + 0x20000
        charmap = list(struct.unpack_from('<65536H', d, cm_off))
        # glyph -> list of chars using it
        users = {}
        for c, g in enumerate(charmap):
            if g:
                users.setdefault(g, []).append(c)
        donors = []
        for cand in DONOR_POOL:
            g = charmap[ord(cand)]
            if g and len(users[g]) == 1:
                donors.append((cand, g))
            if len(donors) == len(HANGUL):
                break
        assert len(donors) == len(HANGUL), f'{tag} sec{si}: only {len(donors)} donors'
        for hangul_ch, (donor_ch, gid) in zip(HANGUL, donors):
            m = d[rec_off + gid * 12: rec_off + gid * 12 + 8]
            bmp_rel = struct.unpack_from('<I', d, rec_off + gid * 12 + 8)[0]
            w, h = m[0], m[1]
            assert w == h and w in (24, 32, 48, 64), f'{tag} sec{si} donor {donor_ch}: cell {w}x{h}'
            cell = render_cell(hangul_ch, styles[si], w, h)
            base = pool + bmp_rel
            d[base: base + len(cell)] = cell
            struct.pack_into('<H', d, cm_off + ord(hangul_ch) * 2, gid)
            print(f'  {tag} sec{si}: {hangul_ch} -> glyph {gid} (donor {donor_ch}, bmp+0x{bmp_rel:X})')
    return bytes(d)

# ---------- strdata patch ----------
def patch_strdata(dec):
    d = bytearray(dec)
    count = struct.unpack_from('<I', d, 0)[0]
    replaced = 0
    for i in range(count):
        off, size = struct.unpack_from('<II', d, 4 + i * 8)
        n = struct.unpack_from('<I', d, off + 8)[0] & 0xFFFF
        tab = off + 0x14
        entries = struct.unpack_from(f'<{n}I', d, tab)
        for j, e in enumerate(entries):
            pos = tab + e
            # read string
            end = pos
            while struct.unpack_from('<H', d, end)[0] != 0:
                end += 2
            cur = d[pos:end].decode('utf-16-le')
            for old, new in REPLACEMENTS:
                if cur == old:
                    nb = new.encode('utf-16-le')
                    assert len(nb) == end - pos, 'length mismatch'
                    d[pos:end] = nb
                    replaced += 1
                    print(f'  strdata sec{i}[{j}]: {old} -> {new}')
    assert replaced == len(REPLACEMENTS), f'replaced {replaced}'
    return bytes(d)

# ---------- main ----------
os.makedirs(os.path.join(OUT, r'romfs\MSG\JP'), exist_ok=True)
os.makedirs(os.path.join(OUT, r'romfs\RES_JP'), exist_ok=True)

# 1) strdata
with open(os.path.join(SRC, r'romfs\MSG\JP\strdata.bin'), 'rb') as f:
    raw = f.read()
hdr, dec = kt_unwrap(raw)
print('patching strdata...')
dec2 = patch_strdata(dec)
out_str = kt_wrap(hdr, dec2)
with open(os.path.join(OUT, r'romfs\MSG\JP\strdata.bin'), 'wb') as f:
    f.write(out_str)
print(f'strdata.bin: {len(raw):,} -> {len(out_str):,} bytes\n')

# 2) fonts inside res_lang.bin
with open(os.path.join(SRC, r'romfs\RES_JP\res_lang.bin'), 'rb') as f:
    res = bytearray(f.read())
lcount = struct.unpack_from('<I', res, 4)[0]
toc = [struct.unpack_from('<II', res, 16 + i * 8) for i in range(lcount)]
for idx in (6, 7):
    off, size = toc[idx]
    hdr, dec = kt_unwrap(bytes(res[off:off + size]))
    print(f'patching res_lang entry {idx} (font, {len(dec):,} bytes)...')
    dec2 = patch_g1n(dec, f'font{idx}')
    blob = kt_wrap(hdr, dec2)
    assert len(blob) <= size, f'entry {idx}: {len(blob)} > slot {size}'
    res[off:off + len(blob)] = blob
    # zero slack, update TOC size
    for k in range(off + len(blob), off + size):
        res[k] = 0
    struct.pack_into('<I', res, 16 + idx * 8 + 4, len(blob))
    print(f'  entry {idx}: {size:,} -> {len(blob):,} bytes (slack {size - len(blob):,})\n')
with open(os.path.join(OUT, r'romfs\RES_JP\res_lang.bin'), 'wb') as f:
    f.write(res)
print(f'res_lang.bin written ({len(res):,} bytes)')
