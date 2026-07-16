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
red=(R>50)&(R>G+15)&(B<G+30)&(al>60)&(lum<180)
print('gunhyotei wide', bb(gold,1160,5,1760,205))
print('haiboku wide', bb(red,1778,15,1945,112))
print('shori wide', bb(gold,1770,103,1950,202))
# sample colors: gold of gunhyotei, gold of shori, red of haiboku, senkou banner text
def sample(mask,x0,y0,x1,y1):
    m=np.zeros((H,W),bool); m[y0:y1,x0:x1]=True; m&=mask
    px=a[m][:,:3]
    if len(px)==0: return None
    return px.mean(0).astype(int), np.median(px,0).astype(int)
print('gun gold color', sample(gold,1183,12,1734,200))
print('shori gold color', sample(gold,1775,105,1954,199))
print('haiboku red color', sample(red,1805,20,1929,109))
# tai circle: analyze region 1580-1770 y30-230
tai=a[30:230,1560:1775]
tl=0.299*tai[:,:,0]+0.587*tai[:,:,1]+0.114*tai[:,:,2]
print('tai region lum min/max/mean', tl.min(), tl.max(), tl.mean())
