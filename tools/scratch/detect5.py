# -*- coding: utf-8 -*-
import sys; sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
from PIL import Image
a=np.array(Image.open('loc_src/e12_t0.png').convert('RGBA')); H,W=a.shape[:2]
rgb=a[:,:,:3].astype(np.int32); al=a[:,:,3]
R,G,B=rgb[:,:,0],rgb[:,:,1],rgb[:,:,2]
lum=0.299*R+0.587*G+0.114*B
def bb(mask,x0,y0,x1,y1):
    m=np.zeros((H,W),bool);m[y0:y1,x0:x1]=True;m&=mask
    ys,xs=np.where(m)
    return (int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max()),int(m.sum())) if len(xs) else None
gold=(R>140)&(G>100)&(B<G-8)&(al>60)
red=(R>50)&(R>G+15)&(B<G+30)&(al>60)&(lum<180)
print('haiboku', bb(red,1785,15,1940,112))
print('shori', bb(gold,1786,105,1950,200))
# tai char: deviation from disc
disc=al>140
dl=lum.copy()
tai_char=disc&((lum>224)|(lum<178))
print('tai char bbox', bb(tai_char,1595,40,1752,205))
