# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw
im=Image.open('loc_src/e12_t0.png').convert('RGBA')
crop=im.crop((420,190,780,230)).resize((360*3,40*3),Image.NEAREST)
d=ImageDraw.Draw(crop)
for x in range(420,780,20):
    px=(x-420)*3; d.line([(px,0),(px,120)],fill=(255,0,255,255))
    if x%40==0: d.text((px+1,1),str(x),fill=(255,0,255,255))
crop.save('z_grid_botbanner.png')
# button text region
c2=im.crop((805,130,1055,180)).resize((250*3,50*3),Image.NEAREST)
d2=ImageDraw.Draw(c2)
for x in range(805,1055,25):
    px=(x-805)*3; d2.line([(px,0),(px,150)],fill=(255,0,255,255)); d2.text((px+1,1),str(x),fill=(255,0,255,255))
c2.save('z_grid_btntext.png')
