# -*- coding: utf-8 -*-
import numpy as np
from PIL import Image
for tid in [48,52,54]:
    a=np.array(Image.open(f"loc_src/e13/t{tid}.png").convert('RGBA'))
    rgb=a[:,:,:3].astype(int); al=a[:,:,3]
    lum=0.299*rgb[:,:,0]+0.587*rgb[:,:,1]+0.114*rgb[:,:,2]
    ink=al>40
    # brightest gold (fill)
    bright=ink&(lum>150)
    mid=ink&(lum>90)&(lum<=150)
    dark=ink&(lum<=90)
    def med(m):
        if m.sum()==0: return None
        return tuple(int(np.median(rgb[:,:,c][m])) for c in range(3)), int(m.sum())
    print(f"t{tid}: bright(fill)",med(bright),"mid",med(mid),"dark(edge)",med(dark))
    # alpha distribution
    print("   alpha: ink px",ink.sum(),"semi(40-180)",((al>=40)&(al<180)).sum(),"opaque(>=180)",(al>=180).sum())
