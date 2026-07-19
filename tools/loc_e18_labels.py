# -*- coding: utf-8 -*-
"""Localize entry18's 43 small text-only label textures (512x64, transparent bg, dark
navy text w/ cream glow). Each texture = ONE label, active ink area near top-left."""
import sys, os, struct
import numpy as np, cv2
sys.path.insert(0,'.'); import koloc
from erase_place_transparent import erase_place_transparent
from PIL import Image
sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))

PK = os.environ.get('PK_RES_SRC') or r'D:\nsw\rom\1.1.5\Program 1\romfs\RES_JP_PK\res_lang_pk.bin'

KO = ['은상','소목표 건의','이탈 만류','등용','포박 등용','항복','배반','빼내기','정전','공물','직접 담판',
'성 역할','보급 거점','방위 거점','담당 구획 변경','지원 거점 선택','가재 특성 선택','봉행 특성 선택',
'초기화','반영·보류 전환','관직 선택','역직 선택','상위 취락 선택','정책 정보','명소 정보',
'봉행 특성 정보','가재 특성 정보','설비 정보','이명 정보','이명 선택','군단장 변경','평정중',
'시나리오 편집','전봉','신규 세력 작성','다이묘 변경','게임 중 편집','세력 편집','외교 편집',
'성 편집','부대 편집','무장 편집','BGM 편집']
assert len(KO) == 43

d = open(PK, 'rb').read()
outer = koloc.outer_entries(d)
off, size = outer[18]
blob = d[off:off+size]
ch = koloc.link_children(blob)
assert len(ch) == 43

def localize_label(rgba, ko):
    al = rgba[:, :, 3]
    ink = (al > 30).astype(np.uint8)
    ink = cv2.dilate(ink, np.ones((7,7), np.uint8))   # cover cream glow halo too
    if ink.sum() < 15:
        return rgba, False
    ys, xs = np.where(ink > 0)
    x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
    style = dict(text_rgb=(40,34,24), stroke_rgb=(246,243,233), glow_a=205, glow_stroke=1.4, glow_blur=1.0)
    out = rgba.copy()
    erase_place_transparent(out, ink, (x0,y0,x1,y1), ko, dilate=7, **style)
    return out, True

new_children = []
n_ok = 0
for cidx, (co, cs) in enumerate(ch):
    cb = blob[co:co+cs]
    g = koloc.kt_decompress(cb)
    assert g[:4] == b'GT1G'
    texs = koloc.g1t_textures(g)
    t = texs[0]
    new_rgba, ok = localize_label(t['rgba'].copy(), KO[cidx])
    n_ok += ok
    if not ok:
        new_children.append(cb)  # unchanged
        print(f'  #{cidx} "{KO[cidx]}" — SKIP (no ink found)')
        continue
    # re-encode BC3 in place (same technique as koloc.rebuild_entry)
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

print(f'\n{n_ok}/43 localized')

# rebuild entry18's inner LINK archive: header (magic+count+toc_off, unchanged) + TOC
# (fixed toc_off, recomputed offsets/sizes) + children (each 16-byte aligned, per
# FORMATS.md's documented inner-LINKDATA alignment requirement).
toc_off = struct.unpack_from('<I', blob, 8)[0]
header = blob[:toc_off]
cursor = toc_off + len(new_children) * 8   # TOC is packed right after header, no gap
toc_bytes = bytearray()
children_bytes = bytearray()
for child in new_children:
    pad = (-cursor) % 16
    children_bytes += b'\x00' * pad
    cursor += pad
    toc_bytes += struct.pack('<II', cursor, len(child))
    children_bytes += child
    cursor += len(child)
out_link = bytearray(header) + toc_bytes + children_bytes
struct.pack_into('<I', out_link, 4, len(new_children))
print(f'entry18 LINK: {len(blob):,} -> {len(out_link):,} bytes  (toc_off={toc_off} unchanged)')

# sanity: re-parse with link_children and confirm each child KT-decodes correctly
check = koloc.link_children(bytes(out_link))
assert check is not None and len(check) == 43, 'link_children reparse failed'
for i,(co,cs) in enumerate(check):
    cb = bytes(out_link)[co:co+cs]
    assert cb[:2] == b'\x01\x01', f'child {i} bad KT header'
    gg = koloc.kt_decompress(cb)
    assert gg[:4] == b'GT1G', f'child {i} bad G1T header'
print('VERIFY: all 43 children re-parse correctly')

open(os.path.join(SP, 'e18_new_link.bin'), 'wb').write(bytes(out_link))
print('wrote e18_new_link.bin')
