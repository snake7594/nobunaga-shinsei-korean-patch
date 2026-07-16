# -*- coding: utf-8 -*-
import numpy as np
from PIL import Image
ids=[9,48,49,50,51,52,53,54,55,56]
for tid in ids:
    a=np.array(Image.open(f"loc_src/e13/t{tid}.png").convert('RGBA'))
    al=a[:,:,3]
    ys,xs=np.where(al>16)
    if len(xs)==0:
        print(tid,'EMPTY'); continue
    print(f"t{tid}: content x[{xs.min()}..{xs.max()}] y[{ys.min()}..{ys.max()}] shape {a.shape[:2]}")
