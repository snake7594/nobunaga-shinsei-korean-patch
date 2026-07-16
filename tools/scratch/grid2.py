# -*- coding: utf-8 -*-
import sys; sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageDraw
im=Image.open('loc_src/e12_t0.png').convert('RGBA')
crop=im.crop((400,120,1050,220)).resize((650*2,100*2),Image.NEAREST)
d=ImageDraw.Draw(crop)
for x in range(400,1050,25):
    px=(x-400)*2; d.line([(px,0),(px,200)],fill=(255,0,255,255))
    if x%50==0: d.text((px+1,1),str(x),fill=(255,0,255,255))
for y in range(120,220,20):
    py=(y-120)*2; d.line([(0,py),(crop.width,py)],fill=(0,255,255,255)); d.text((1,py+1),str(y),fill=(0,255,255,255))
crop.save('z_grid_leftbanners.png')
