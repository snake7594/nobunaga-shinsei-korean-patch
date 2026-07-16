# -*- coding: utf-8 -*-
import sys; sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
from PIL import Image
a=np.array(Image.open('loc_src/e12_t0.png').convert('RGBA')); H,W=a.shape[:2]
rgb=a[:,:,:3].astype(np.int32); al=a[:,:,3]
R,G,B=rgb[:,:,0],rgb[:,:,1],rgb[:,:,2]
lum=0.299*R+0.587*G+0.114*B
def bb(mask,x0,y0,x1,y1):
    m=np.zeros((H,W),bool); m[y0:y1,x0:x1]=True; m&=mask
    ys,xs=np.where(m)
    if len(xs)==0: return None
    return int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max()),int(m.sum())
gold=(R>140)&(G>100)&(B<G-8)&(al>60)
dark=(lum<110)&(al>60)
darkbig=(lum<140)&(al>60)
# red brush 敗北 - dark red/brown
red=(R>50)&(R>G+15)&(B<G+30)&(al>60)&(lum<180)
print('gunhyotei', bb(gold,1160,5,1735,205))
print('haiboku red', bb(red,1775,20,1945,110))
print('shori gold', bb(gold,1775,105,1955,200))
print('senkou1', bb(dark,1835,150,1920,195))
print('senkou2', bb(dark,463,196,565,222))
print('senkou3', bb(dark,623,196,722,222))
print('button', bb(darkbig,808,133,1055,173))
