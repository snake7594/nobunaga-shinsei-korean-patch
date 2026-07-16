# -*- coding: utf-8 -*-
"""Build before/after comparison PNGs for the release notes."""
import os, sys, io
from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding='utf-8')
BASE = r'D:\nsw\rom\노부나가의 야망 신생_일본판\이미지한글화'
JP, KO = os.path.join(BASE, 'png_jp'), os.path.join(BASE, 'png_ko')
OUT = os.path.join(BASE, 'compare')
os.makedirs(OUT, exist_ok=True)

def ui_font(size):
    with open(r'C:\Windows\Fonts\malgun.ttf', 'rb') as f:
        return ImageFont.truetype(io.BytesIO(f.read()), size)

BG = (24, 24, 38)
PANEL = (38, 38, 58)

# ---- label comparison ----
PICKS = [4, 6, 7, 14, 24, 35, 45, 48, 74, 98, 101, 108]
ROW_H = 74
HDR = 46
W = 2 * 522 + 30
sheet = Image.new('RGB', (W, HDR + len(PICKS) * ROW_H + 14), BG)
dr = ImageDraw.Draw(sheet)
f = ui_font(22)
dr.text((10 + 260, 12), '원본 (일본어)', font=f, fill=(230, 200, 140), anchor='ma')
dr.text((20 + 522 + 260, 12), '한글화 (v1.2)', font=f, fill=(150, 220, 150), anchor='ma')
for k, idx in enumerate(PICKS):
    y = HDR + k * ROW_H
    for col, d in ((0, JP), (1, KO)):
        img = Image.open(os.path.join(d, f'03_{idx:03d}_0.png')).convert('RGBA')
        bg = Image.new('RGBA', img.size, PANEL + (255,))
        comp = Image.alpha_composite(bg, img).convert('RGB')
        if comp.height > 64:
            comp.thumbnail((512, 64))
        x = 10 + col * 532
        dr.rectangle([x, y, x + 521, y + 67], fill=PANEL)
        sheet.paste(comp, (x + 5, y + 2))
sheet.save(os.path.join(OUT, 'compare_labels.png'))
print('compare_labels.png', sheet.size)

# ---- warning comparison ----
w_jp = Image.open(os.path.join(JP, '01_002_0.png')).convert('RGBA').crop((0, 0, 1280, 720))
w_ko = Image.open(os.path.join(KO, '01_002_0.png')).convert('RGBA').crop((0, 0, 1280, 720))
TH = 380
sheet2 = Image.new('RGB', (2 * 680 + 30, TH + HDR + 14), BG)
dr2 = ImageDraw.Draw(sheet2)
dr2.text((10 + 338, 12), '원본 (일본어)', font=f, fill=(230, 200, 140), anchor='ma')
dr2.text((20 + 680 + 338, 12), '한글화 (v1.2)', font=f, fill=(150, 220, 150), anchor='ma')
for col, img in ((0, w_jp), (1, w_ko)):
    bg = Image.new('RGBA', img.size, (0, 0, 0, 255))
    comp = Image.alpha_composite(bg, img).convert('RGB')
    comp.thumbnail((676, TH))
    sheet2.paste(comp, (10 + col * 690, HDR))
sheet2.save(os.path.join(OUT, 'compare_warning.png'))
print('compare_warning.png', sheet2.size)
