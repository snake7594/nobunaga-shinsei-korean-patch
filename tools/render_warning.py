# -*- coding: utf-8 -*-
"""Render the Korean warning screen (2048x1024 BGRA8, content 1280x720)."""
import os, sys, io
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding='utf-8')
SRC = r'D:\nsw\rom\노부나가의 야망 신생_일본판\추출원본'
OUTD = r'D:\nsw\rom\노부나가의 야망 신생_일본판\이미지한글화\png_ko'
os.makedirs(OUTD, exist_ok=True)

def load_font(path, size):
    with open(path, 'rb') as f:
        return ImageFont.truetype(io.BytesIO(f.read()), size)

FONT_M = os.path.join(SRC, 'SeoulHangangM.ttf')
FONT_B = os.path.join(SRC, 'SeoulHangangB.ttf')

W, H = 2048, 1024
img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
dr = ImageDraw.Draw(img)
dr.rectangle([0, 0, 1279, 719], fill=(0, 0, 0, 255))

RED = (238, 50, 25, 255)
WHITE = (232, 232, 232, 255)

title = '주의'
tf = load_font(FONT_B, 46)
tw = dr.textlength(title, font=tf)
tx = (1280 - tw) // 2
dr.text((tx, 104), title, font=tf, fill=RED)
dr.line([tx - 4, 160, tx + tw + 4, 160], fill=RED, width=3)

body = [
    '게임 소프트를 권리자의 허락 없이 개조하는 행위와, 마찬가지로',
    '권리자의 허락 없이 인터넷 등을 통해 배포·전송하는 행위는',
    '법률로 금지되어 있습니다.',
    '',
    '또한 불법 전송임을 알면서 다운로드하는 행위 역시',
    '사적 이용 목적의 복제에 해당하지 않는 위법 행위입니다.',
    '',
    '여러분의 이해와 협조를 부탁드립니다.',
]
bf = load_font(FONT_M, 30)
y = 210
for line in body:
    if line:
        dr.text((225, y), line, font=bf, fill=WHITE)
    y += 44

img.save(os.path.join(OUTD, '01_002_0.png'))
print('warning rendered')
# preview
bg = Image.new('RGBA', img.size, (30, 30, 50, 255))
comp = Image.alpha_composite(bg, img).convert('RGB')
comp.thumbnail((900, 900))
comp.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'warning_ko_view.jpg'), quality=88)
