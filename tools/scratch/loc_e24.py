# -*- coding: utf-8 -*-
"""Localize res_lang entry 24 (title/loading screens). Only functional text:
t0 has a white-on-blue '追加' (Add) button top-right -> '추가'.
The main logo 信長の野望・新生 and the ©2022 Koei Tecmo copyright/trademark line are left untouched.
t7 = character artwork (no text), t8 = blank white panel (no text): skipped."""
import os, numpy as np, cv2
from PIL import Image
import koloc

SP=os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(SP,'loc_out','e24'),exist_ok=True)

res=open(koloc.RESJP,'rb').read()
e,coff,child,g=koloc.entry_gt1g(res,24)
texs=koloc.g1t_textures(g)

# ---- t0: '追加' button ----
t0=[x for x in texs if x['tid']==0][0]
base=t0['rgba'].copy()
H,W=base.shape[:2]

# ink box of the white JP text on the blue button (measured)
bx0,by0,bx1,by1 = 2003,5,2036,19
# build white-text mask restricted to the button interior (a bit padded)
mask=np.zeros((H,W),np.uint8)
px0,py0,px1,py1 = 1994,1,2045,24
reg=base[py0:py1,px0:px1]
rgb=reg[:,:,:3].astype(int); al=reg[:,:,3]
lum=0.299*rgb[:,:,0]+0.587*rgb[:,:,1]+0.114*rgb[:,:,2]
white=(lum>170)&(al>110)
mask[py0:py1,px0:px1]=(white*255).astype(np.uint8)

# white text on blue button: white ink, dark-blue stroke, no glow
koloc.erase_place(
    base, mask, (bx0,by0,bx1,by1), '추가',
    text_rgb=(228,231,235), stroke_rgb=(40,60,95), glow_a=0, fill=0.98,
)

Image.fromarray(base,'RGBA').save(os.path.join(SP,'loc_out','e24','t0.png'))

# before/after crop of the button for verification (4x)
orig=t0['rgba']
def crop4(arr):
    c=Image.fromarray(arr[0:40,1985:2048],'RGBA')
    return c.resize((c.width*6,c.height*6),Image.NEAREST)
ba=Image.new('RGBA',(63*6, 40*6*2+20),(30,30,30,255))
ba.alpha_composite(crop4(orig),(0,0))
ba.alpha_composite(crop4(base),(0,40*6+20))
ba.save(os.path.join(SP,'e24_t0_ba.png'))
print('done t0. ink box',(bx0,by0,bx1,by1),'mask px',int((mask>0).sum()))
