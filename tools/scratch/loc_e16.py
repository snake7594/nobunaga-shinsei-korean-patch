# -*- coding: utf-8 -*-
"""Localize res_lang entry-16 atlas (tid 0, 2048x1024 BC3) baked JP -> KO."""
import sys, os, numpy as np, cv2
from PIL import Image
sys.stdout.reconfigure(encoding='utf-8')
import koloc

SRC='loc_src/e16/t0.png'
os.makedirs('loc_out/e16',exist_ok=True)
base=np.array(Image.open(SRC).convert('RGBA'))
H,W=base.shape[:2]

def mask_dark(bbox,T=100):
    x0,y0,x1,y1=bbox; m=np.zeros((H,W),np.uint8)
    c=base[y0:y1+1,x0:x1+1]; rgb=c[:,:,:3].astype(int); al=c[:,:,3]
    lum=0.299*rgb[:,:,0]+0.587*rgb[:,:,1]+0.114*rgb[:,:,2]
    mm=(lum<T)&(al>50)
    m[y0:y1+1,x0:x1+1]=mm.astype(np.uint8); return m

def mask_red(bbox):
    x0,y0,x1,y1=bbox; m=np.zeros((H,W),np.uint8)
    c=base[y0:y1+1,x0:x1+1]; rgb=c[:,:,:3].astype(int); al=c[:,:,3]
    r,g,b=rgb[:,:,0],rgb[:,:,1],rgb[:,:,2]
    mm=(r>100)&(r-g>40)&(r-b>40)&(al>50)
    m[y0:y1+1,x0:x1+1]=mm.astype(np.uint8); return m

# style presets
BLACK_PHOTO=dict(text_rgb=(12,12,14),stroke_rgb=(240,238,230),glow_a=205,glow_blur=1.1)
RED_BRUSH  =dict(text_rgb=(178,44,37),stroke_rgb=(70,18,14),glow_a=0)
BLACK_CIRC =dict(text_rgb=(18,18,20),stroke_rgb=(236,231,216),glow_a=170,glow_blur=1.0)
RED_CIRC   =dict(text_rgb=(184,45,38),stroke_rgb=(52,12,10),glow_a=0)
BLACK_SMALL=dict(text_rgb=(20,20,22),stroke_rgb=(236,231,216),glow_a=120,glow_blur=0.8)

JOBS=[
 # (ko, bbox, mode, style)
 ('지행',(123,35,251,97),'dark',BLACK_PHOTO),
 ('내정',(528,37,646,94),'dark',BLACK_PHOTO),
 ('전투',(355,172,421,235),'dark',BLACK_PHOTO),
 ('천하통일',(308,340,467,379),'red',RED_BRUSH),
 ('세력',(965,330,1074,399),'dark',BLACK_CIRC),
 ('성',(908,428,938,459),'red',RED_CIRC),
 ('성',(1011,424,1048,463),'red',RED_CIRC),
 ('성',(1121,428,1151,459),'red',RED_CIRC),
]
GUN=[(828,498,859,533),(881,498,920,535),(944,498,983,535),(1009,498,1048,535),
     (1072,498,1111,535),(1136,498,1174,535),(1193,498,1228,533)]
for b in GUN: JOBS.append(('군',b,'dark',BLACK_CIRC))
BUS=[(836,560,856,584),(888,557,912,585),(948,556,973,587),(1014,556,1043,589),
     (1083,556,1111,587),(1147,556,1171,585),(1202,560,1219,584)]
for b in BUS: JOBS.append(('무장',b,'dark',BLACK_SMALL))

for ko,bbox,mode,style in JOBS:
    m=mask_dark(bbox) if mode=='dark' else mask_red(bbox)
    koloc.erase_place(base,m,bbox,ko,**style)

Image.fromarray(base,'RGBA').save('loc_out/e16/t0.png')
print('saved, jobs',len(JOBS))
