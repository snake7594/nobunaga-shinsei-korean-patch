# -*- coding: utf-8 -*-
import numpy as np
from PIL import Image
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

# gold: bright yellow strokes
gold=(R>150)&(G>110)&(B<G-15)&(al>60)
# dark red/brown brush (敗北)
redbrush=(R>60)&(R<200)&(R>G+20)&(G>B-5)&(B<120)&(al>60)&(lum<170)
# generic dark text
dark=(lum<120)&(al>60)

print('== 軍評定 gold region 1150-1730 ==')
print(bbox(gold & region(1150,0,1730,210)))
print('== 敗北 region 1900-2048 top ==')
print(bbox(redbrush & region(1890,0,2048,120)))
print('== 勝利 gold region 1900-2048 mid ==')
print(bbox(gold & region(1890,100,2048,220)))
print('== 戦功1位 dark on gold banner ~1750-1930 y150-210 ==')
print(bbox(dark & region(1740,150,1940,215)))
print('== 戦功2位 dark banner left ~430-620 ==')
print(bbox(dark & region(440,155,640,215)))
print('== 戦功3位 dark banner ~600-770 ==')
print(bbox(dark & region(600,155,780,215)))
print('== button text いずれか gray ~820-1030 y120-175 ==')
print(bbox(dark & region(810,120,1035,178)))
