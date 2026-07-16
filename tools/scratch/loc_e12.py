# -*- coding: utf-8 -*-
"""Localize res_lang entry-12 texture 0 (군평정 / battle-result atlas) JP->KO."""
import sys, os, numpy as np, cv2, io
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import koloc

SP=os.path.dirname(os.path.abspath(__file__))
SRC=os.path.join(SP,'loc_src','e12_t0.png')
OUTDIR=os.path.join(SP,'loc_out','e12'); os.makedirs(OUTDIR,exist_ok=True)

BASE=np.array(Image.open(SRC).convert('RGBA')).copy()
H,W=BASE.shape[:2]

def LUM():
    r=BASE[:,:,0].astype(np.int32);g=BASE[:,:,1].astype(np.int32);b=BASE[:,:,2].astype(np.int32)
    return 0.299*r+0.587*g+0.114*b

def place_ko(bbox, ko, **st):
    """Composite KO fit-to-box centered on bbox ink center onto current BASE."""
    x0,y0,x1,y1=bbox
    img=Image.fromarray(BASE,'RGBA')
    layer,ink=koloc.render_ko_fit(ko,x1-x0+1,y1-y0+1,**st)
    if layer is not None:
        jcx=(x0+x1)/2; jcy=(y0+y1)/2
        img.alpha_composite(layer,(int(round(jcx-ink[0])),int(round(jcy-ink[1]))))
    BASE[:,:,:]=np.array(img)

def clear_rect(x0,y0,x1,y1):
    """Transparent-bg erase: zero rgba over rectangle."""
    BASE[y0:y1+1,x0:x1+1,:]=0

def inpaint_mask(mask, dil=1, ir=3):
    m=cv2.dilate(mask.astype(np.uint8),np.ones((3,3),np.uint8),iterations=dil)
    rgb=BASE[:,:,:3].copy()
    inp=cv2.inpaint(rgb,m,ir,cv2.INPAINT_TELEA)
    BASE[:,:,:3]=inp

def sub(x0,y0,x1,y1):
    r=np.zeros((H,W),bool); r[y0:y1+1,x0:x1+1]=True; return r

# ================= transparent-background brush labels =================
# 1) 軍評定 -> 군평정  (gold brush)
clear_rect(1168,8,1556,186)
place_ko((1183,31,1544,169),'군평정',
    text_rgb=(214,188,116), stroke_rgb=(108,70,18), glow_rgb=(58,38,8), glow_a=120,
    glow_stroke=1.5, glow_blur=2.2, fill=0.97, stroke_ratio=0.9)

# 3) 敗北 -> 패배  (dark red brush)
clear_rect(1792,2,1940,82)
place_ko((1798,8,1932,68),'패배',
    text_rgb=(150,48,20), stroke_rgb=(72,20,8), glow_rgb=(48,14,5), glow_a=110,
    glow_stroke=1.4, glow_blur=2.0, fill=0.97, stroke_ratio=0.9)

# 4) 勝利 -> 승리  (gold brush)
clear_rect(1792,88,1940,166)
place_ko((1798,96,1935,162),'승리',
    text_rgb=(228,202,90), stroke_rgb=(112,74,18), glow_rgb=(58,38,8), glow_a=120,
    glow_stroke=1.5, glow_blur=2.0, fill=0.97, stroke_ratio=0.9)

# ================= 対 -> 대  (embossed on opaque crest disc) =================
dx0,dy0,dx1,dy1=1573,28,1772,216
L=LUM(); AL=BASE[:,:,3]
disc=AL>140
# deviation from a locally-smoothed disc luminance => every char stroke (light or dark)
Lf=L.astype(np.float32)
bg=cv2.GaussianBlur(Lf,(0,0),26)
charmask=sub(1588,38,1757,208)&disc&(np.abs(Lf-bg)>7)
# rebuild the smooth disc: replace char strokes AND non-disc corners with disc-median color, then blur
reg=BASE[dy0:dy1+1,dx0:dx1+1,:3].astype(np.uint8)
disc_l=disc[dy0:dy1+1,dx0:dx1+1]
char_l=cv2.dilate(charmask[dy0:dy1+1,dx0:dx1+1].astype(np.uint8),np.ones((3,3),np.uint8),iterations=6).astype(bool)
keep=disc_l&(~char_l)
medcol=np.median(reg[keep].reshape(-1,3),axis=0).astype(np.uint8)
reg2=reg.copy(); reg2[~keep]=medcol
blur=cv2.GaussianBlur(reg2,(0,0),9)
full=BASE[:,:,:3].copy(); full[dy0:dy1+1,dx0:dx1+1]=blur
cm=cv2.dilate(charmask.astype(np.uint8),np.ones((3,3),np.uint8),iterations=6).astype(bool)&disc
BASE[:,:,:3][cm]=full[cm]
place_ko((1600,52,1748,196),'대',
    text_rgb=(238,237,233), stroke_rgb=(150,148,142), glow_rgb=(255,255,255), glow_a=70,
    glow_stroke=1.2, glow_blur=1.6, fill=0.92, stroke_ratio=1.0)

# ================= dark text on opaque banners (inpaint keeps banner) =================
L=LUM(); AL=BASE[:,:,3]
# 5) 戦功1位 -> 전공1위 (gold banner)
inpaint_mask(sub(1831,170,1922,199)&(AL>60)&(L<112), dil=1, ir=3)
place_ko((1838,174,1915,196),'전공1위',
    text_rgb=(48,40,18), stroke_rgb=(228,208,110), glow_a=0, fill=0.99, stroke_ratio=0.45)

# 6) 戦功2位 -> 전공2위 (silver banner)
L=LUM(); AL=BASE[:,:,3]
inpaint_mask(sub(461,196,565,221)&(AL>60)&(L<112), dil=1, ir=3)
place_ko((463,200,563,218),'전공2위',
    text_rgb=(42,42,48), stroke_rgb=(214,214,220), glow_a=0, fill=0.99, stroke_ratio=0.45)

# 7) 戦功3位 -> 전공3위 (orange banner)
L=LUM(); AL=BASE[:,:,3]
inpaint_mask(sub(621,196,722,221)&(AL>60)&(L<112), dil=1, ir=3)
place_ko((623,200,705,218),'전공3위',
    text_rgb=(56,30,10), stroke_rgb=(232,152,60), glow_a=0, fill=0.99, stroke_ratio=0.45)

# ================= 8) いずれかのボタンを押してください -> 아무 버튼이나 누르세요 =================
clear_rect(764,130,1058,173)
place_ko((790,138,1050,164),'아무 버튼이나 누르세요',
    text_rgb=(126,118,113), stroke_rgb=(236,236,236), glow_rgb=(255,255,255), glow_a=120,
    glow_stroke=1.1, glow_blur=1.0, fill=0.95, stroke_ratio=0.7)

Image.fromarray(BASE,'RGBA').save(os.path.join(OUTDIR,'t0.png'))
print('saved', os.path.join(OUTDIR,'t0.png'))
