# -*- coding: utf-8 -*-
import numpy as np
from PIL import Image
a=np.array(Image.open("loc_src/e13/t48.png").convert('RGBA'))
rgb=a[:,:,:3].astype(int); al=a[:,:,3]
R,G,B=rgb[:,:,0],rgb[:,:,1],rgb[:,:,2]
ink=al>120
gold=ink&(R>G)&(G>=B)&(R-B>25)  # saturated gold
print("gold px",gold.sum())
if gold.sum():
    for c,n in zip(range(3),'RGB'):
        v=rgb[:,:,c][gold]
        print(n,"median",int(np.median(v)),"mean",int(v.mean()),"p25",int(np.percentile(v,25)),"p75",int(np.percentile(v,75)))
# brightest gold (highlight) vs darker gold (deep)
lum=0.299*R+0.587*G+0.114*B
for name,m in [("bright gold",gold&(lum>170)),("mid gold",gold&(lum>=110)&(lum<=170)),("deep gold",gold&(lum<110))]:
    if m.sum(): print(name,tuple(int(np.median(rgb[:,:,c][m])) for c in range(3)),m.sum())
