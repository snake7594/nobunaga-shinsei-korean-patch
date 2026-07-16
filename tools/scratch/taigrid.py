# -*- coding: utf-8 -*-
import numpy as np
from PIL import Image, ImageDraw
im=Image.open('loc_src/e12_t0.png').convert('RGBA')
a=np.array(im)
# tai circle zoom with grid
crop=im.crop((1555,20,1780,235)).resize((225*3,215*3),Image.NEAREST)
d=ImageDraw.Draw(crop)
for x in range(1560,1780,20):
    px=(x-1555)*3; d.line([(px,0),(px,645)],fill=(255,0,255,255)); d.text((px+1,1),str(x),fill=(255,0,255,255))
for y in range(20,235,20):
    py=(y-20)*3; d.line([(0,py),(crop.width,py)],fill=(0,255,255,255)); d.text((1,py+1),str(y),fill=(0,255,255,255))
crop.save('z_tai_grid.png')
# gold mask viz for gunhyotei to check stray
rgb=a[:,:,:3].astype(np.int32);R,G,B=rgb[:,:,0],rgb[:,:,1],rgb[:,:,2];al=a[:,:,3]
gold=((R>140)&(G>100)&(B<G-8)&(al>60)).astype(np.uint8)*255
Image.fromarray(gold[0:210,1160:1770]).resize((610*2,210*2),Image.NEAREST).save('z_goldmask_gun.png')
