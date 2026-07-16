"""Build v1.2 res_lang.bin: Hangul font extension (entries 6,7)
+ Korean menu labels (entry 3 sub-entries) + Korean warning (entry 1 sub 2)."""
import struct, os, sys
import numpy as np
import lz4.block
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
from bc_encode import encode_bc3
import g1n_extend  # reuse font extension + kt wrap/unwrap

SRC = r'D:\nsw\rom\노부나가의 야망 신생_일본판\추출원본'
KO_DIR = r'D:\nsw\rom\노부나가의 야망 신생_일본판\이미지한글화\png_ko'
OUT = r'D:\nsw\rom\노부나가의 야망 신생_일본판\한글패치_테스트\romfs\RES_JP\res_lang.bin'

kt_unwrap = g1n_extend.kt_unwrap
kt_wrap = g1n_extend.kt_wrap

def parse_link(d):
    count = struct.unpack_from('<I', d, 4)[0]
    return [struct.unpack_from('<II', d, 16 + i * 8) for i in range(count)]

def patch_g1t_texture(g1t, png_path):
    """Replace texture 0 payload in a G1T blob with re-encoded image (same fmt/dims)."""
    g = bytearray(g1t)
    tbl = struct.unpack_from('<I', g, 0x0C)[0]
    o = struct.unpack_from('<I', g, tbl)[0]
    p = tbl + o
    fmt, dxdy = g[p + 1], g[p + 2]
    w = 1 << (dxdy & 0xF)
    h = 1 << (dxdy >> 4)
    ex = struct.unpack_from('<I', g, p + 8)[0]
    data_off = p + 8 + ex
    img = Image.open(png_path).convert('RGBA')
    assert img.size == (w, h), f'{png_path}: {img.size} != {(w, h)}'
    if fmt == 0x5B:
        payload = encode_bc3(np.asarray(img))
    elif fmt == 0x01:
        arr = np.asarray(img)[:, :, [2, 1, 0, 3]]  # RGBA -> BGRA
        payload = arr.tobytes()
    else:
        raise ValueError(f'unsupported fmt 0x{fmt:02X}')
    assert data_off + len(payload) <= len(g), 'payload overrun'
    g[data_off:data_off + len(payload)] = payload
    return bytes(g)

def rebuild_inner_link(blob, replacements):
    """blob = inner LINKDATA; replacements = {sub_index: new_unwrapped_bytes}.
    CRITICAL: sub-entry data offsets must stay 16-byte aligned (relative to the
    inner blob) — the game's loader fails on unaligned entries and falls back to
    the 4x4 placeholder texture (black screen symptom)."""
    toc = parse_link(blob)
    raws = {}
    for j, (off, size) in enumerate(toc):
        raw = blob[off:off + size]
        if j in replacements:
            hdr, _ = kt_unwrap(raw)
            raw = kt_wrap(hdr, replacements[j])
        raws[j] = raw
    data_subs = [j for j, (off, size) in enumerate(toc) if size > 0]
    first_off = min(toc[j][0] for j in data_subs)
    out = bytearray(blob[:first_off])          # header + TOC area + leading pad
    new_toc = list(toc)
    cursor = first_off
    for j in data_subs:
        cursor = (cursor + 15) & ~15           # align 16
        while len(out) < cursor:
            out += b'\x00'
        new_toc[j] = (cursor, len(raws[j]))
        out += raws[j]
        cursor += len(raws[j])
    # preserve original trailing bytes after the last data sub
    last_end = max(toc[j][0] + toc[j][1] for j in data_subs)
    out += blob[last_end:]
    for j, (off, size) in enumerate(new_toc):
        struct.pack_into('<II', out, 16 + j * 8, off, size)
    return bytes(out)

def main():
    with open(os.path.join(SRC, r'romfs\RES_JP\res_lang.bin'), 'rb') as f:
        res = f.read()
    toc = parse_link(res)
    charset = sorted(set(c for c in open(os.path.join(SP, 'charset_final.txt'), encoding='utf-8').read()
                         if not c.isspace() and ord(c) > 0x7F))
    print(f'charset {len(charset)} chars')

    entries = []
    for i, (off, size) in enumerate(toc):
        end = off + size
        nxt = toc[i + 1][0] if i + 1 < len(toc) else len(res)
        entries.append([res[off:end], res[end:nxt]])

    # --- fonts (6,7) ---
    for idx in (6, 7):
        hdr, dec = kt_unwrap(entries[idx][0])
        print(f'entry {idx}: extending font...')
        dec2 = g1n_extend.extend_g1n(dec, charset, f'font{idx}')
        entries[idx][0] = kt_wrap(hdr, dec2)

    # --- warning (entry 1, sub 2) ---
    inner = entries[1][0]
    subs = parse_link(inner)
    hdr2, g1t = kt_unwrap(inner[subs[2][0]:subs[2][0] + subs[2][1]])
    g1t2 = patch_g1t_texture(g1t, os.path.join(KO_DIR, '01_002_0.png'))
    entries[1][0] = rebuild_inner_link(inner, {2: g1t2})
    print('entry 1: warning replaced')

    # --- menu labels (entry 3) ---
    inner = entries[3][0]
    subs = parse_link(inner)
    repl = {}
    for j in range(len(subs)):
        png = os.path.join(KO_DIR, f'03_{j:03d}_0.png')
        if os.path.exists(png):
            hdr3, g1t = kt_unwrap(inner[subs[j][0]:subs[j][0] + subs[j][1]])
            repl[j] = patch_g1t_texture(g1t, png)
    entries[3][0] = rebuild_inner_link(inner, repl)
    print(f'entry 3: {len(repl)} labels replaced')

    # --- outer rebuild ---
    out = bytearray(res[:toc[0][0]])
    for i, (blob, gap) in enumerate(entries):
        struct.pack_into('<II', out, 16 + i * 8, len(out), len(blob))
        out += blob
        out += gap
    with open(OUT, 'wb') as f:
        f.write(out)
    print(f'written {OUT} ({len(out):,} bytes)')

if __name__ == '__main__':
    main()
