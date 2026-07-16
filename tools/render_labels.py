# -*- coding: utf-8 -*-
"""Render Korean menu-title labels in the original style
(ivory gradient fill, dark outline, left-aligned) using Seoul Hangang B."""
import os, sys, io
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
from label_map import LABELS

SRC = r'D:\nsw\rom\노부나가의 야망 신생_일본판\추출원본'
OUTD = r'D:\nsw\rom\노부나가의 야망 신생_일본판\이미지한글화\png_ko'
os.makedirs(OUTD, exist_ok=True)

_font_bytes = {}
def load_font(path, size):
    if path not in _font_bytes:
        with open(path, 'rb') as f:
            _font_bytes[path] = f.read()
    return ImageFont.truetype(io.BytesIO(_font_bytes[path]), size)

FONT = os.path.join(SRC, 'SeoulHangangB.ttf')

def _render_glyph_rgba(text, fsize, outline_px):
    """Render text into a tight RGBA image: ivory vertical-gradient fill + dark outline."""
    pad = outline_px * 2 + 8
    fnt = load_font(FONT, fsize)
    # measure
    tmp = Image.new('L', (8, 8), 0)
    box = ImageDraw.Draw(tmp).textbbox((0, 0), text, font=fnt)
    tw, th = box[2] - box[0], box[3] - box[1]
    W, H = tw + pad * 2, th + pad * 2
    img = Image.new('L', (W, H), 0)
    ImageDraw.Draw(img).text((pad - box[0], pad - box[1]), text, font=fnt, fill=255)
    mask = np.asarray(img, dtype=np.float32) / 255
    outline_img = img.filter(ImageFilter.MaxFilter(2 * outline_px + 1))
    outline = np.asarray(outline_img, dtype=np.float32) / 255
    outline_soft = np.asarray(Image.fromarray((outline * 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(outline_px * 0.6)), dtype=np.float32) / 255
    outline_a = np.clip(outline * 0.92 + outline_soft * 0.5, 0, 1)
    yy = np.linspace(0, 1, H)[:, None]
    fills = ((205 - 75 * yy), (203 - 72 * yy), (190 - 68 * yy))
    oc = (30, 33, 40)
    out = np.zeros((H, W, 4), dtype=np.float32)
    for c, (ocv, fv) in enumerate(zip(oc, fills)):
        out[:, :, c] = ocv * (1 - mask) + np.broadcast_to(fv, (H, W)) * mask
    out[:, :, 3] = np.clip(outline_a + mask * (1 - outline_a), 0, 1) * 255
    im = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), 'RGBA')
    return im.crop(im.getbbox())  # tight ink crop

def render_label(text, w, h):
    """Render then fit the ink into the cell with safe margins so it never clips.
    Target: ink height <= h-2*MARGIN, width <= w-2*MARGIN, left-aligned, vertically centered."""
    SS = 2
    MARGIN = max(3, round(h * 0.09))       # ~6px on a 64px cell
    max_h = h - 2 * MARGIN
    max_w = w - 2 * MARGIN
    glyph = _render_glyph_rgba(text, round(h * 0.92 * SS), max(1, round(h * 0.05 * SS)))
    gw, gh = glyph.size
    # scale to fit both constraints (never upscale beyond native SS)
    s = min(max_h * SS / gh, max_w * SS / gw, 1.0)
    nw, nh = max(1, round(gw * s)), max(1, round(gh * s))
    glyph = glyph.resize((nw, nh), Image.LANCZOS)
    cell = Image.new('RGBA', (w * SS, h * SS), (0, 0, 0, 0))
    px = MARGIN * SS
    py = (h * SS - nh) // 2
    cell.alpha_composite(glyph, (px, py))
    return cell.resize((w, h), Image.LANCZOS)

def main():
    from PIL import Image as I
    sizes = {}
    srcdir = r'D:\nsw\rom\노부나가의 야망 신생_일본판\이미지한글화\png_jp'
    for idx, text in LABELS.items():
        orig = I.open(os.path.join(srcdir, f'03_{idx:03d}_0.png'))
        w, h = orig.size
        im = render_label(text, w, h)
        im.save(os.path.join(OUTD, f'03_{idx:03d}_0.png'))
    print(f'{len(LABELS)} labels rendered to {OUTD}')
    # preview sheet
    files = sorted(os.listdir(OUTD))
    ROW = 70
    sheet = I.new('RGB', (2 * 622, (len(files) + 1) // 2 * ROW + 10), (24, 24, 38))
    from PIL import ImageDraw as ID
    dr = ID.Draw(sheet)
    per = (len(files) + 1) // 2
    for k, f in enumerate(files):
        img = I.open(os.path.join(OUTD, f)).convert('RGBA')
        bg = I.new('RGBA', img.size, (24, 24, 38, 255))
        comp = I.alpha_composite(bg, img).convert('RGB')
        if comp.height > 64:
            comp.thumbnail((512, 64))
        col, row = k // per, k % per
        sheet.paste(comp, (10 + col * 622 + 100, 5 + row * ROW))
        dr.text((10 + col * 622, 25 + row * ROW), f.split('_')[1], fill=(150, 200, 150))
    sheet.save(os.path.join(SP, 'labels_ko_preview.png'))
    print('preview saved')

if __name__ == '__main__':
    main()
