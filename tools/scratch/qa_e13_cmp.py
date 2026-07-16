# -*- coding: utf-8 -*-
import koloc, numpy as np
from PIL import Image
res=open(koloc.RESJP,'rb').read()
e,coff,child,g=koloc.entry_gt1g(res,13)
texs={t['tid']:t for t in koloc.g1t_textures(g)}
tids=[48,49,50,51,52,53,54,55,56]
# checkerboard bg to reveal alpha
def onbg(rgba):
    h,w=rgba.shape[:2]
    bg=np.zeros((h,w,3),np.uint8)
    c=40; 
    for y in range(0,h,16):
        for x in range(0,w,16):
            if ((x//16)+(y//16))%2==0: bg[y:y+16,x:x+16]=[60,60,60]
            else: bg[y:y+16,x:x+16]=[110,110,110]
    a=rgba[:,:,3:4].astype(float)/255
    out=(rgba[:,:,:3].astype(float)*a+bg*(1-a)).astype(np.uint8)
    return out
for tid in tids:
    orig=texs[tid]['rgba']
    loc=np.array(Image.open(f'loc_out/e13/t{tid}.png').convert('RGBA'))
    print(tid,'orig',orig.shape,'loc',loc.shape)
    oi=onbg(orig); li=onbg(loc)
    # stack vertically: orig on top, loc bottom, with gap
    gap=np.full((8,orig.shape[1],3),255,np.uint8)
    comb=np.vstack([oi,gap,li])
    Image.fromarray(comb).save(f'qa_e13_t{tid}.png')
print('done')
