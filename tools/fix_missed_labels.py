# -*- coding: utf-8 -*-
"""Localize buttons/badges that were missed in the original e5 (nav buttons) and
e8 (command wheel) atlas localization passes:
  e5 tex1: 開戦(x7 color variants) -> 개전, 承認(x3 more, not already covered) -> 승인
  e8 tex0: 中止 -> 중지, 失敗 -> 실패, 達成 -> 달성 (small status badges)
Reuses koloc.erase_place with the same auto fill/text-color detection as e5_loc.py.
These were missed because the auto-detected button box list (e5_btns.json) didn't
pick up the differently-shaped/rotated elements below -- box coordinates here were
found manually via connected-components on the alpha channel (see git history for
the exploratory scripts). Run tools/repack_missed_labels.py afterward to merge the
two output PNGs back into res_lang.bin."""
import sys, os, numpy as np, cv2
sys.path.insert(0,'.'); import koloc
from PIL import Image
sys.stdout.reconfigure(encoding='utf-8')
SP=os.path.dirname(os.path.abspath(__file__))
E5_SRC = os.environ.get('RES_LANG_SRC') or r'D:\nsw\rom\nobu16_powerupkit\patch_build\romfs\RES_JP\res_lang.bin'

def localize_box(BASE, x, y, w, h, ko, band_frac=(0.20, 0.86, 0.03, 0.97), fill_band=(0.10, 0.24),
                  inpaint_r=5, erase_margin=0.0):
    """band_frac (tight): used to measure the JP ink's own bounding box, so the KO
    replacement is sized/centered correctly (avoids picking up border decoration).
    erase_margin (0..0.5): how much further OUT the erase/inpaint mask is allowed to
    extend beyond band_frac, for text that's rotated/tilted and pokes past the tight
    band -- erased but NOT counted toward the ink-box size calculation."""
    reg = BASE[y:y+h, x:x+w]
    rgb = reg[:, :, :3].astype(np.int32); al = reg[:, :, 3]
    lum = 0.299*rgb[:,:,0] + 0.587*rgb[:,:,1] + 0.114*rgb[:,:,2]
    fy0, fy1 = int(h*fill_band[0]), int(h*fill_band[1])
    fillmask = (al[fy0:fy1] > 120)
    fill = np.median(rgb[fy0:fy1][fillmask], axis=0) if fillmask.sum() > 10 else np.array([200,200,200])
    fill_lum = 0.299*fill[0] + 0.587*fill[1] + 0.114*fill[2]
    band = np.zeros((h, w), bool)
    band[int(h*band_frac[0]):int(h*band_frac[1]), int(w*band_frac[2]):int(w*band_frac[3])] = True
    erase_band = np.zeros((h, w), bool)
    ey0=max(0,int(h*(band_frac[0]-erase_margin))); ey1=min(h,int(h*(band_frac[1]+erase_margin)))
    ex0=max(0,int(w*(band_frac[2]-erase_margin))); ex1=min(w,int(w*(band_frac[3]+erase_margin)))
    erase_band[ey0:ey1, ex0:ex1] = True
    diff = np.abs(lum - fill_lum)
    sizemask = ((diff > 40) & (al > 70) & band).astype(np.uint8)
    erasemask = ((diff > 40) & (al > 70) & erase_band).astype(np.uint8)
    erasemask = cv2.morphologyEx(erasemask, cv2.MORPH_CLOSE, np.ones((3,3), np.uint8))
    if sizemask.sum() < 15:
        print(f'  WARN: no text detected in box ({x},{y},{w},{h})'); return
    ys, xs = np.where(sizemask > 0)
    tlum = np.median(lum[sizemask > 0]); dark = tlum < fill_lum
    text_top, text_bot = int(ys.min()), int(ys.max())
    tcx = w // 2; box_w = int(w * 0.7)
    tb = (tcx - box_w // 2, text_top, tcx + box_w // 2, text_bot)
    if dark:
        style = dict(text_rgb=(40,34,24), stroke_rgb=(246,243,233), glow_a=205, glow_stroke=1.4, glow_blur=1.0)
    else:
        style = dict(text_rgb=(249,249,251), stroke_rgb=(33,44,68), glow_a=0, glow_stroke=1.0, glow_blur=0.8)
    local = reg.copy()
    koloc.erase_place(local, erasemask, tb, ko, inpaint_r=inpaint_r, **style)
    BASE[y:y+h, x:x+w] = local
    print(f'  ok: box ({x},{y},{w},{h}) -> "{ko}"  (dark_text={dark})')

# ---------------- e5 tex1: 開戦 -> 개전, 承認(missed ones) -> 승인 ----------------
res = open(E5_SRC, 'rb').read()
e, coff, child, g = koloc.entry_gt1g(res, 5)
texs = koloc.g1t_textures(g)
e5_arr = texs[1]['rgba'].copy()   # tex index 1 = 2048x2048 nav button sheet

e5_boxes = [
    (655,6,165,47,'개전'), (1339,5,164,47,'개전'), (1519,5,164,47,'개전'), (1699,5,164,47,'개전'),
    (1877,4,119,53,'승인'),
    (653,68,119,32,'승인'), (1339,65,164,35,'개전'), (1519,65,164,35,'개전'), (1699,65,164,35,'개전'),
    (1877,68,119,32,'승인'),
]
print('=== e5 (nav buttons) — 開戦/承認 missed labels ===')
for x,y,w,h,ko in e5_boxes:
    localize_box(e5_arr, x, y, w, h, ko)
Image.fromarray(e5_arr, 'RGBA').save(os.path.join(SP, 'e5_t1_extra_ko.png'))

# ---------------- e8 tex0: 中止/失敗/達成 badges ----------------
E8_SRC = E5_SRC
e2, coff2, child2, g2 = koloc.entry_gt1g(res, 8)
texs2 = koloc.g1t_textures(g2)
e8_arr = texs2[0]['rgba'].copy()  # tex index 0 = 2048x1024 wheel sheet

def localize_badge(BASE, x, y, w, h, ko, border_erode=5, inpaint_r=8):
    """For small rotated badges where luminance-diff text detection is unreliable:
    erase the WHOLE interior (alpha mask eroded inward, so the badge's own border/bevel
    survives) and redraw KO centered -- avoids ghost strokes from missed rotated glyphs."""
    reg = BASE[y:y+h, x:x+w]
    al = reg[:, :, 3]
    interior = (al > 100).astype(np.uint8)
    interior = cv2.erode(interior, np.ones((border_erode, border_erode), np.uint8))
    if interior.sum() < 15:
        print(f'  WARN: badge interior empty ({x},{y},{w},{h})'); return
    ys, xs = np.where(interior > 0)
    text_top, text_bot = int(ys.min()), int(ys.max())
    tcx = w // 2; box_w = int((xs.max()-xs.min()) * 0.72)
    tb = (tcx - box_w // 2, text_top, tcx + box_w // 2, text_bot)
    style = dict(text_rgb=(250,246,225), stroke_rgb=(22,18,10), glow_a=0, glow_stroke=1.2, glow_blur=0.8)
    local = reg.copy()
    koloc.erase_place(local, interior, tb, ko, inpaint_r=inpaint_r, **style)
    BASE[y:y+h, x:x+w] = local
    print(f'  ok(badge): box ({x},{y},{w},{h}) -> "{ko}"')

e8_boxes = [
    (786,967,57,42,'중지'), (850,967,57,42,'실패'), (914,967,57,42,'달성'),
]
print('=== e8 (command wheel) — status badge labels ===')
for x,y,w,h,ko in e8_boxes:
    localize_badge(e8_arr, x, y, w, h, ko)
Image.fromarray(e8_arr, 'RGBA').save(os.path.join(SP, 'e8_t0_extra_ko.png'))

print('\nsaved e5_t1_extra_ko.png, e8_t0_extra_ko.png')
