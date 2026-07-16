"""Korean test patch v2: full title-menu translation + quality-tuned Hangul glyphs."""
import struct, sys, os
import lz4.block
from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding='utf-8')

SRC = r'D:\nsw\rom\노부나가의 야망 신생_일본판\추출원본'
OUT = r'D:\nsw\rom\노부나가의 야망 신생_일본판\한글패치_테스트'

# exact full-string replacements, applied across all strdata sections
REPLACEMENTS = {
    '初めから': '처음부터',
    '続きから': '이어하기',
    'チュートリアル': '튜토리얼',
    '登録武将編集': '등록무장편집',
    '追加コンテンツ': '추가 콘텐츠',
    '鑑賞': '감상',
    '設定': '설정',
    'ライセンス': '라이선스',
}
HANGUL = sorted(set(c for v in REPLACEMENTS.values() for c in v if c != ' '))
# NOTE: excluded kanji that occur in game text (checked against MSG dumps):
#   齟齬(1) 鸞(1) 麝(2) 躑躅(6 — 躑躅ヶ崎館 place name)
DONOR_POOL = ['鬻', '靨', '龕', '彝', '齷', '齪', '鼾', '黌',
              '顳', '顴', '鬣', '鰥', '黐', '齲', '魃', '魄', '魍', '魎',
              '魑', '鵺', '鸚', '鵡', '黶', '黷', '齔', '齣', '齠', '齧', '齦', '齶',
              '龠', '鬯', '鬲', '韲', '霾', '驪', '髑', '髴', '鱶', '鰈', '鼬', '黴']

# Seoul Hangang fonts live inside the extraction root folder
FONT_REG = os.path.join(SRC, 'SeoulHangangM.ttf')
FONT_BOLD = os.path.join(SRC, 'SeoulHangangB.ttf')

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

# ---------- glyph rendering v2 ----------
_scale_cache = {}

_font_bytes = {}

def load_font(font_path, size):
    if font_path not in _font_bytes:
        with open(font_path, 'rb') as f:
            _font_bytes[font_path] = f.read()
    import io
    return ImageFont.truetype(io.BytesIO(_font_bytes[font_path]), size)

def hangul_ink(ch, font_path, big_size=88):
    img = Image.new('L', (big_size * 3, big_size * 3), 0)
    dr = ImageDraw.Draw(img)
    fnt = load_font(font_path, big_size)
    dr.text((big_size * 3 // 2, big_size * 3 // 2), ch, fill=255, font=fnt, anchor='mm')
    bbox = img.getbbox()
    return img.crop(bbox)

def scale_factor(font_path, target_ink_h):
    key = (font_path, target_ink_h)
    if key not in _scale_cache:
        ref = hangul_ink('음', font_path)  # tall reference syllable
        _scale_cache[key] = target_ink_h / ref.size[1]
    return _scale_cache[key]

def render_cell(ch, font_path, w, h, target_ink_h, center_y_frac, gamma=1.15):
    ink = hangul_ink(ch, font_path)
    f = scale_factor(font_path, target_ink_h)
    nw, nh = max(1, round(ink.size[0] * f)), max(1, round(ink.size[1] * f))
    if nw > w - 2:  # keep 1px side margin
        r = (w - 2) / nw
        nw, nh = w - 2, max(1, round(nh * r))
    ink = ink.resize((nw, nh), Image.LANCZOS)
    cell = Image.new('L', (w, h), 0)
    cy = round(h * center_y_frac)
    px_x = (w - nw) // 2
    px_y = min(max(cy - nh // 2, 0), h - nh)
    cell.paste(ink, (px_x, px_y))
    p = cell.load()
    out = bytearray(w * h // 2)
    # NOTE: true layout is row-major 4bpp with the EVEN pixel in the HIGH nibble
    # (verified by smoothness scoring on original kanji — h_hi beats h_lo on all)
    for y in range(h):
        for x in range(w):
            v = round(((p[x, y] / 255) ** gamma) * 15)
            idx = y * w + x
            out[idx // 2] |= (v << 4) if idx % 2 == 0 else v
    return bytes(out)

# ---------- G1N patch ----------
def patch_g1n(g1n, tag):
    d = bytearray(g1n)
    pool = struct.unpack_from('<I', d, 0x14)[0]
    nsec = struct.unpack_from('<I', d, 0x1C)[0]
    secs = [struct.unpack_from('<I', d, 0x20 + 4 * i)[0] for i in range(nsec)]
    # section 0 = regular, 1 = bold. kanji ink: reg h~39/48 centered y~24.5; bold h~42/48
    styles = [(FONT_REG, 39 / 48, 24.5 / 48), (FONT_BOLD, 41 / 48, 24.5 / 48)]
    for si in (0, 1):
        font_path, ink_frac, cy_frac = styles[si]
        s = secs[si]
        cm_off, rec_off = s, s + 0x20000
        charmap = list(struct.unpack_from('<65536H', d, cm_off))
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
        assert len(donors) == len(HANGUL), f'{tag} sec{si}: only {len(donors)}/{len(HANGUL)} donors'
        for hangul_ch, (donor_ch, gid) in zip(HANGUL, donors):
            rec = rec_off + gid * 12
            w, h = d[rec], d[rec + 1]
            assert w == h and w in (24, 32, 48, 64), f'{tag} sec{si} {donor_ch}: cell {w}x{h}'
            bmp_rel = struct.unpack_from('<I', d, rec + 8)[0]
            cell = render_cell(hangul_ch, font_path, w, h, round(h * ink_frac), cy_frac)
            base = pool + bmp_rel
            d[base: base + len(cell)] = cell
            struct.pack_into('<H', d, cm_off + ord(hangul_ch) * 2, gid)
        print(f'  {tag} sec{si}: {len(HANGUL)} glyphs injected '
              f'({", ".join(h + "→" + dc for h, (dc, _) in list(zip(HANGUL, donors))[:5])} ...)')
    return bytes(d)

# ---------- strdata full rebuild ----------
def rebuild_strdata(dec):
    count = struct.unpack_from('<I', dec, 0)[0]
    sections = []
    n_replaced = 0
    for i in range(count):
        off, size = struct.unpack_from('<II', dec, 4 + i * 8)
        n = struct.unpack_from('<I', dec, off + 8)[0] & 0xFFFF
        tab = off + 0x14
        entries = struct.unpack_from(f'<{n}I', dec, tab)
        strings = []
        for e in entries:
            pos = tab + e
            end = pos
            while struct.unpack_from('<H', dec, end)[0] != 0:
                end += 2
            s = dec[pos:end].decode('utf-16-le')
            if s in REPLACEMENTS:
                s = REPLACEMENTS[s]
                n_replaced += 1
            strings.append(s)
        sections.append(strings)
    print(f'  {n_replaced} strings replaced')
    # rebuild
    blobs = []
    for strings in sections:
        n = len(strings)
        table = bytearray()
        pool = bytearray()
        base = 4 * n
        for s in strings:
            table += struct.pack('<I', base + len(pool))
            pool += s.encode('utf-16-le') + b'\x00\x00'
        body = bytes(table) + bytes(pool)
        size = 0x14 + len(body)
        hdr = struct.pack('<IIIII', 0x134C58, 0x10000 | (size & 0xFFFF),
                          0x40000 | n, 0x14, 0xFFFFFF00)
        blobs.append(hdr + body)
    out = bytearray()
    out += struct.pack('<I', len(blobs))
    toc_pos = len(out)
    out += b'\x00' * (8 * len(blobs))
    for i, b in enumerate(blobs):
        while len(out) % 4:
            out += b'\x00'
        struct.pack_into('<II', out, toc_pos + i * 8, len(out), len(b))
        out += b
    return bytes(out)

# ---------- main ----------
os.makedirs(os.path.join(OUT, r'romfs\MSG\JP'), exist_ok=True)
os.makedirs(os.path.join(OUT, r'romfs\RES_JP'), exist_ok=True)

with open(os.path.join(SRC, r'romfs\MSG\JP\strdata.bin'), 'rb') as f:
    raw = f.read()
hdr, dec = kt_unwrap(raw)
print('rebuilding strdata...')
dec2 = rebuild_strdata(dec)
print(f'  dec size {len(dec):,} -> {len(dec2):,}')
with open(os.path.join(OUT, r'romfs\MSG\JP\strdata.bin'), 'wb') as f:
    f.write(kt_wrap(hdr, dec2))

with open(os.path.join(SRC, r'romfs\RES_JP\res_lang.bin'), 'rb') as f:
    res = bytearray(f.read())
lcount = struct.unpack_from('<I', res, 4)[0]
for idx in (6, 7):
    off, size = struct.unpack_from('<II', res, 16 + idx * 8)
    hdr, dec = kt_unwrap(bytes(res[off:off + size]))
    print(f'patching font entry {idx} ({len(dec):,} bytes)...')
    blob = kt_wrap(hdr, patch_g1n(dec, f'font{idx}'))
    assert len(blob) <= size, f'entry {idx}: {len(blob)} > {size}'
    res[off:off + len(blob)] = blob
    for k in range(off + len(blob), off + size):
        res[k] = 0
    struct.pack_into('<I', res, 16 + idx * 8 + 4, len(blob))
    print(f'  entry {idx}: {size:,} -> {len(blob):,}')
with open(os.path.join(OUT, r'romfs\RES_JP\res_lang.bin'), 'wb') as f:
    f.write(res)
print('done')
