# -*- coding: utf-8 -*-
"""Localize entry21's 33 trait/treasure name badges (gold glow text, transparent bg,
1024x256, 3 render-state variants per name: sharp/sharp/motion-blur)."""
import sys, os, struct
import numpy as np, cv2
sys.path.insert(0,'.'); import koloc
from erase_place_transparent import erase_place_transparent
from PIL import Image
sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))

PK = os.environ.get('PK_RES_SRC') or r'D:\nsw\rom\1.1.5\Program 1\romfs\RES_JP_PK\res_lang_pk.bin'

NAMES = ['다케다의 적비','정원의 지휘','계수의 재능','백절불굴','니혼고','구로다 무사',
         '무쌍창','용사의 뜻','결사의 각오','수변류','천시']
KO = []
for n in NAMES:
    KO += [n, n, n]   # each name has 3 render-state variants (sharp/sharp/motion-blur)
assert len(KO) == 33

d = open(PK, 'rb').read()
outer = koloc.outer_entries(d)
off, size = outer[21]
blob = d[off:off+size]
ch = koloc.link_children(blob)
assert len(ch) == 33

def localize_badge(rgba, ko):
    al = rgba[:, :, 3]
    ink = (al > 15).astype(np.uint8)
    ink = cv2.dilate(ink, np.ones((9,9), np.uint8))
    if ink.sum() < 15:
        return rgba, False
    ys, xs = np.where(ink > 0)
    x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
    style = dict(text_rgb=(255,221,120), stroke_rgb=(46,28,4), glow_a=180, glow_stroke=1.6, glow_blur=1.2)
    out = rgba.copy()
    erase_place_transparent(out, ink, (x0,y0,x1,y1), ko, dilate=9, **style)
    return out, True

new_children = []
n_ok = 0
for cidx, (co, cs) in enumerate(ch):
    cb = blob[co:co+cs]
    g = koloc.kt_decompress(cb)
    assert g[:4] == b'GT1G'
    texs = koloc.g1t_textures(g)
    t = texs[0]
    new_rgba, ok = localize_badge(t['rgba'].copy(), KO[cidx])
    n_ok += ok
    if not ok:
        new_children.append(cb)
        print(f'  #{cidx} "{KO[cidx]}" — SKIP (no ink found)')
        continue
    if t['fmt'] == 0x5B:
        orig_bc3 = bytes(g[t['data_off']:t['data_off']+t['data_len']])
        payload, _ = koloc.mixed_bc3(orig_bc3, t['rgba'], new_rgba)
    else:
        raise ValueError(f'unexpected fmt {t["fmt"]:02x}')
    g2 = bytearray(g)
    g2[t['data_off']:t['data_off']+t['data_len']] = payload
    new_child = koloc.kt_wrap(cb, bytes(g2))
    new_children.append(new_child)
    print(f'  #{cidx} "{KO[cidx]}" ok')

print(f'\n{n_ok}/33 localized')

toc_off = struct.unpack_from('<I', blob, 8)[0]
header = blob[:toc_off]
cursor = toc_off + len(new_children) * 8
toc_bytes = bytearray(); children_bytes = bytearray()
for child in new_children:
    pad = (-cursor) % 16
    children_bytes += b'\x00' * pad; cursor += pad
    toc_bytes += struct.pack('<II', cursor, len(child))
    children_bytes += child
    cursor += len(child)
out_link = bytearray(header) + toc_bytes + children_bytes
struct.pack_into('<I', out_link, 4, len(new_children))
print(f'entry21 LINK: {len(blob):,} -> {len(out_link):,} bytes  (toc_off={toc_off} unchanged)')

check = koloc.link_children(bytes(out_link))
assert check is not None and len(check) == 33
for i,(co,cs) in enumerate(check):
    cb = bytes(out_link)[co:co+cs]
    assert cb[:2] == b'\x01\x01'
    gg = koloc.kt_decompress(cb)
    assert gg[:4] == b'GT1G'
print('VERIFY: all 33 children re-parse correctly')

open(os.path.join(SP, 'e21_new_link.bin'), 'wb').write(bytes(out_link))
print('wrote e21_new_link.bin')
