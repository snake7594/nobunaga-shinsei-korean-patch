# -*- coding: utf-8 -*-
"""v3.7 image localization — produce Korean RGBA replacements + preview PNGs:
 A) exppk e4 t1 (1024x512): 全承認×6 -> 전체 승인, 姫×6 -> 공주  (button pills)
 B) banner atlas 2048x2048 (exppk e3 t0 == res_lang_pk e04 t0): 11 gold battle banners
    + 3 result labels -> Korean
 C) titles: exp e0 c108 (512x128) 목표 무장 선택; exppk e0 c44-47 (512x64) 4 titles
Outputs saved as npy+png in v37_out/ for the rebuild step."""
import sys, os, struct, json
sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import koloc
import numpy as np, cv2
from PIL import Image
import lz4.block

OUT = os.path.join(SP, 'v37_out')
os.makedirs(OUT, exist_ok=True)

def kt_try(blob):
    dsz = struct.unpack_from('<Q', blob, 8)[0]
    csz = struct.unpack_from('<Q', blob, 16)[0]
    if csz == 0:
        return blob[24:24+dsz]
    return lz4.block.decompress(blob[24:24+csz], uncompressed_size=dsz)

def link_pairs(d):
    n = struct.unpack_from('<I', d, 4)[0]
    tab = struct.unpack_from('<I', d, 8)[0]
    if not (16 <= tab < len(d) and tab % 4 == 0):
        tab = 0x10
    return [struct.unpack_from('<II', d, tab + i*8) for i in range(n)]

def get_child_g1t(path, entry, child):
    d = open(path, 'rb').read()
    off, sz = link_pairs(d)[entry]
    blob = d[off:off+sz]
    pay = blob if blob[:4] == b'LINK' else kt_try(blob)
    o2, s2 = link_pairs(pay)[child]
    c = pay[o2:o2+s2]
    g = c if c[:4] in (b'GT1G', b'G1TG') else kt_try(c)
    return g

EXPPK = r'D:\nsw\rom\1.1.5\Program 1\romfs\RES_JP_PK\res_lang_exp_pk.bin'
EXP = r'D:\nsw\rom\1.1.5\Program 0\romfs\RES_JP\res_lang_exp.bin'

# ---------- A) buttons ----------
g = get_child_g1t(EXPPK, 4, 0)
texs = koloc.g1t_textures(g)
btn = texs[1]['rgba'].copy()          # 1024x512

# hand-measured pill boxes (x, y, w, h)
ZEN_BOXES = [(820, 8, 112, 48), (818, 70, 114, 49), (483, 119, 114, 49),
             (612, 119, 114, 49), (748, 130, 114, 51), (872, 132, 114, 51)]
HIME_BOXES = [(8, 183, 114, 50), (140, 184, 115, 50), (275, 181, 111, 50),
              (483, 181, 113, 50), (612, 181, 114, 50), (744, 206, 114, 50)]
BTN_JOBS = [(x, y, w, h, '전체 승인') for (x, y, w, h) in ZEN_BOXES] + \
           [(x, y, w, h, '공주') for (x, y, w, h) in HIME_BOXES]

def relabel(rgba, x, y, w, h, ko):
    """Erase the JP text area (inner band of the pill) and render KO in matching scheme."""
    reg = rgba[y:y+h, x:x+w]
    rgb = reg[:, :, :3].astype(np.int32)
    al = reg[:, :, 3]
    lum = 0.299*rgb[:, :, 0] + 0.587*rgb[:, :, 1] + 0.114*rgb[:, :, 2]
    fy0, fy1 = int(h*0.14), int(h*0.24)
    fillmask = al[fy0:fy1] > 120
    fill_lum = np.median(lum[fy0:fy1][fillmask]) if fillmask.sum() > 10 else np.median(lum[al > 120])
    band = np.zeros((h, w), bool)
    band[int(h*0.22):int(h*0.86), int(w*0.10):int(w*0.93)] = True
    diff = np.abs(lum - fill_lum)
    txt = ((diff > 45) & (al > 60) & band).astype(np.uint8)
    txt = cv2.morphologyEx(txt, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    if txt.sum() < 12:
        return False
    ys, xs = np.where(txt > 0)
    tlum = np.median(lum[txt > 0])
    dark = tlum < fill_lum
    tcx = w // 2
    box_w = int(w * 0.72)
    tb = (tcx - box_w//2, int(ys.min()), tcx + box_w//2, int(ys.max()))
    if dark:
        style = dict(text_rgb=(40, 34, 24), stroke_rgb=(246, 243, 233), glow_a=200, glow_stroke=1.3, glow_blur=1.0)
    else:
        style = dict(text_rgb=(249, 249, 251), stroke_rgb=(33, 44, 68), glow_a=0, glow_stroke=1.0, glow_blur=0.8)
    local = reg.copy()
    koloc.erase_place(local, txt, tb, ko, inpaint_r=5, **style)
    rgba[y:y+h, x:x+w] = local
    return True

done = 0
for (x, y, w, h, ko) in BTN_JOBS:
    ok = relabel(btn, x, y, w, h, ko)
    done += ok
    if not ok:
        print('  NO INK at', (x, y, w, h), ko)
print(f'buttons relabeled: {done}/{len(BTN_JOBS)}')
np.save(os.path.join(OUT, 'btn_t1.npy'), btn)
Image.fromarray(btn, 'RGBA').save(os.path.join(OUT, 'preview_buttons.png'))

# ---------- B) banners ----------
g = get_child_g1t(EXPPK, 3, 0)
texs = koloc.g1t_textures(g)
ban = texs[0]['rgba'].copy()          # 2048x2048

BANNERS = [  # (x0,y0,x1,y1, ko, gold?) — generous full-cell boxes
    (130, 0, 790, 190, '미미가와 전투', True),
    (1000, 0, 1720, 190, '야마자키 전투', True),
    (10, 190, 850, 385, '미카타가하라 전투', True),
    (950, 190, 1750, 385, '세키가하라 전투', True),
    (20, 385, 790, 585, '오사카 여름의 진', True),
    (950, 385, 1710, 585, '오사카 겨울의 진', True),
    (5, 585, 890, 785, '제2차 우에다 합전', True),
    (1040, 585, 1700, 785, '가와고에 합전', True),
    (40, 785, 860, 1005, '오케하자마 전투', True),
    (980, 785, 1780, 1005, '나가시노 전투', True),
    (60, 1005, 800, 1220, '가와나카지마 전투', True),
    (40, 1285, 480, 1535, '본성 함락', False),
    (515, 1285, 950, 1535, '성주 항복', False),
    (985, 1285, 1470, 1535, '본성 제압', False),
]
for (x0, y0, x1, y1, ko, gold) in BANNERS:
    reg = ban[y0:y1, x0:x1]
    h, w = reg.shape[:2]
    rgb = reg[:, :, :3].astype(np.int32)
    al = reg[:, :, 3]
    lum = 0.299*rgb[:, :, 0] + 0.587*rgb[:, :, 1] + 0.114*rgb[:, :, 2]
    if gold:
        # the dark blob is the JP glyph shadow — clear the whole cell and recreate:
        # Korean gold text + its own brush-shadow (dilated/blurred glyph silhouette)
        reg2 = reg.copy()
        reg2[:, :, :] = 0                      # fully transparent cell
        style = dict(text_rgb=(216, 184, 114), stroke_rgb=(58, 48, 26), glow_a=0,
                     glow_stroke=1.0, glow_blur=0.8, fill=0.95)
        layer, inkc = koloc.render_ko_fit(ko, int(w*0.86), int(h*0.52), **style)
        la = np.array(layer)
        # shadow: dilate + blur the glyph alpha
        a = la[:, :, 3]
        pad = 28
        ap = np.zeros((a.shape[0]+2*pad, a.shape[1]+2*pad), np.uint8)
        ap[pad:-pad, pad:-pad] = a
        sh = cv2.dilate(ap, np.ones((17, 17), np.uint8))
        sh = cv2.GaussianBlur(sh, (0, 0), 7)
        shadow = np.zeros((ap.shape[0], ap.shape[1], 4), np.uint8)
        shadow[:, :, 0] = 44
        shadow[:, :, 1] = 44
        shadow[:, :, 2] = 46
        shadow[:, :, 3] = (sh.astype(np.float32) * 0.93).astype(np.uint8)
        img = Image.fromarray(reg2, 'RGBA')
        sx = int(round(w/2 - inkc[0] - pad))
        sy = int(round(h/2 - inkc[1] - pad))
        img.alpha_composite(Image.fromarray(shadow, 'RGBA'), (sx, sy))
        img.alpha_composite(layer, (int(round(w/2 - inkc[0])), int(round(h/2 - inkc[1]))))
        ban[y0:y1, x0:x1] = np.array(img)
    else:
        # white paper panel with big black calligraphy: paint ink out with paper color
        ink = ((lum < 233) & (al > 100)).astype(np.uint8)
        ink = cv2.dilate(ink, np.ones((9, 9), np.uint8))
        paper_sel = (al > 200) & (lum > 235)
        if paper_sel.sum() < 200 or ink.sum() < 100:
            print('banner: label parse fail for', ko)
            continue
        paper = np.median(rgb[paper_sel], axis=0).astype(np.uint8)
        reg2 = reg.copy()
        m = ink > 0
        # also kill the faint watermark ghost: central-zone pixels that deviate from paper
        zone = np.zeros((h, w), bool)
        zone[int(h*0.28):int(h*0.97), int(w*0.03):int(w*0.97)] = True
        dist = np.abs(rgb - paper[None, None, :]).max(axis=2)
        m = m | (zone & (al > 150) & (dist > 5))
        reg2[m, 0] = paper[0]
        reg2[m, 1] = paper[1]
        reg2[m, 2] = paper[2]
        style = dict(text_rgb=(45, 40, 32), stroke_rgb=(235, 232, 222), glow_a=0,
                     glow_stroke=1.0, glow_blur=0.8, fill=0.95)
        layer, inkc = koloc.render_ko_fit(ko, int(w*0.82), int(h*0.5), **style)
        img = Image.fromarray(reg2, 'RGBA')
        img.alpha_composite(layer, (int(round(w/2 - inkc[0])), int(round(h/2 - inkc[1]))))
        ban[y0:y1, x0:x1] = np.array(img)
    print('banner ok:', ko)
np.save(os.path.join(OUT, 'banner_t0.npy'), ban)
Image.fromarray(ban, 'RGBA').save(os.path.join(OUT, 'preview_banners.png'))

# ---------- C) titles ----------
from erase_place_transparent import erase_place_transparent

def localize_title(g1t_blob, ko, style):
    texs2 = koloc.g1t_textures(g1t_blob)
    t = texs2[0]
    rgba = t['rgba'].copy()
    al = rgba[:, :, 3]
    ink = (al > 30).astype(np.uint8)
    ink = cv2.dilate(ink, np.ones((7, 7), np.uint8))
    ys, xs = np.where(ink > 0)
    box = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
    erase_place_transparent(rgba, ink, box, ko, dilate=7, **style)
    return t, rgba

TITLE_STYLE = dict(text_rgb=(40, 34, 24), stroke_rgb=(246, 243, 233), glow_a=205, glow_stroke=1.4, glow_blur=1.0)
title_jobs = [
    ('exp_e0_c108', EXP, 0, 108, '목표 무장 선택'),
    ('exppk_e0_c44', EXPPK, 0, 44, '공주 정보'),
    ('exppk_e0_c45', EXPPK, 0, 45, '정책 선택'),
    ('exppk_e0_c46', EXPPK, 0, 46, '무장 소속 변경'),
    ('exppk_e0_c47', EXPPK, 0, 47, '항복 권고'),
]
for name, path, e, c, ko in title_jobs:
    gt = get_child_g1t(path, e, c)
    t, rgba = localize_title(gt, ko, TITLE_STYLE)
    np.save(os.path.join(OUT, f'{name}.npy'), rgba)
    Image.fromarray(rgba, 'RGBA').save(os.path.join(OUT, f'preview_{name}.png'))
    print('title ok:', name, ko, rgba.shape)
print('ALL RENDERS DONE')
