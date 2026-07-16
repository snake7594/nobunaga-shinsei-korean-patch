# -*- coding: utf-8 -*-
import sys; sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
from PIL import Image
a=np.array(Image.open('loc_src/e12_t0.png').convert('RGBA')); H,W=a.shape[:2]
rgb=a[:,:,:3].astype(np.int32); al=a[:,:,3]
R,G,B=rgb[:,:,0],rgb[:,:,1],rgb[:,:,2]
lum=0.299*R+0.587*G+0.114*B
gold=(R>140)&(G>100)&(B<G-8)&(al>60)
def bb(mask,x0,y0,x1,y1):
    m=np.zeros((H,W),bool);m[y0:y1,x0:x1]=True;m&=mask
    ys,xs=np.where(m)
    return (int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max()),int(m.sum())) if len(xs) else None
print('gunhyotei capped1552', bb(gold,1160,5,1552,205))
# button text region: alpha & color stats
bt=a[133:168,808:1055]
print('button alpha min/max/mean', bt[:,:,3].min(), bt[:,:,3].max(), bt[:,:,3].mean())
btl=0.299*bt[:,:,0]+0.587*bt[:,:,1]+0.114*bt[:,:,2]
tm=bt[:,:,3]>80
print('button text px color mean', bt[tm][:,:3].mean(0).astype(int) if tm.any() else None)
print('button text lum range', btl[tm].min(), btl[tm].max())
# senkou1 gold banner text color
s1=a[150:195,1835:1920]; s1l=0.299*s1[:,:,0]+0.587*s1[:,:,1]+0.114*s1[:,:,2]
dm=(s1l<110)&(s1[:,:,3]>60); print('senkou1 dark color', s1[dm][:,:3].mean(0).astype(int) if dm.any() else None, 'banner bg', s1[~dm&(s1[:,:,3]>60)][:,:3].mean(0).astype(int))
# tai disc bg color (exclude char): use median of disc region
td=a[45:200,1590:1755]; tdl=0.299*td[:,:,0]+0.587*td[:,:,1]+0.114*td[:,:,2]
disc=(td[:,:,3]>150)
print('tai disc lum median', np.median(tdl[disc]), 'color', np.median(td[disc][:,:3],0).astype(int))
print('tai disc lum p10 p90', np.percentile(tdl[disc],10), np.percentile(tdl[disc],90))
