# -*- coding: utf-8 -*-
import koloc, numpy as np
from PIL import Image
res=open(koloc.RESJP,'rb').read()
e,coff,child,g=koloc.entry_gt1g(res,16)
t0=[x for x in koloc.g1t_textures(g) if x['tid']==0][0]
orig=np.asarray(Image.fromarray(t0['rgba'],'RGBA').convert('RGB')).astype(np.float32)
loc=np.asarray(Image.open(r"loc_out/e16/t0.png").convert('RGB')).astype(np.float32)
def darkfrac(img,box,thr=115):
    x0,y0,x1,y1=box; s=img[y0:y1,x0:x1].mean(2); return (s<thr).mean()
# gun-row node discs: 7 approx centers x; measure a bottom-rim strip (below glyph) per node
# node centers roughly:
cxs=[820,910,1000,1030,1120,1210,1290]  # rough
print("=== GUN row disc bottom-rim strip (y 533-548), dark fraction orig vs loc ===")
for cx in [820,905,1000,1095,1185]:
    box=(cx-30,533,cx+30,549)
    print(f"x~{cx}: orig {darkfrac(orig,box):.2f}  loc {darkfrac(loc,box):.2f}")
print("=== SHIRO(red) row disc bottom-rim (y 415-430) ===")
for cx in [900,1010,1120]:
    box=(cx-35,414,cx+35,430)
    print(f"x~{cx}: orig {darkfrac(orig,box):.2f}  loc {darkfrac(loc,box):.2f}")
