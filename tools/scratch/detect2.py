# -*- coding: utf-8 -*-
import sys; sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
from PIL import Image, ImageDraw
im=Image.open('loc_src/e12_t0.png').convert('RGBA')
a=np.array(im); H,W=a.shape[:2]
rgb=a[:,:,:3].astype(np.int32); al=a[:,:,3]
R,G,B=rgb[:,:,0],rgb[:,:,1],rgb[:,:,2]
lum=0.299*R+0.587*G+0.114*B
def bbox(mask):
    ys,xs=np.where(mask)
    if len(xs)==0: return None
    return int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max()),int(mask.sum())
def region(x0,y0,x1,y1):
    m=np.zeros((H,W),bool); m[y0:y1,x0:x1]=True; return m
gold=(R>140)&(G>100)&(B<G-8)&(al>60)
dark=(lum<120)&(al>60)
print('gunhyotei full', bbox(gold & region(1150,0,1730,210)))
print('senkou1', bbox(dark & region(1740,150,1940,215)))
print('senkou2', bbox(dark & region(440,155,640,215)))
print('senkou3', bbox(dark & region(600,155,780,215)))
print('button', bbox(dark & region(810,120,1035,178)))
# grid overlay on right half
crop=im.crop((1150,0,2048,256)).resize(((2048-1150)*2,512),Image.NEAREST)
d=ImageDraw.Draw(crop)
for x in range(1150,2048,50):
    px=(x-1150)*2; d.line([(px,0),(px,512)],fill=(255,0,255,255)); d.text((px+2,2),str(x),fill=(255,0,255,255))
for y in range(0,256,50):
    py=y*2; d.line([(0,py),(crop.width,py)],fill=(0,255,255,255)); d.text((2,py+2),str(y),fill=(0,255,255,255))
crop.save('z_grid_right.png')
