# -*- coding: utf-8 -*-
import numpy as np, json
from PIL import Image
boxes={}
for tid in [48,49,50,51,52,53,54,55,56]:
    a=np.array(Image.open(f"loc_src/e13/t{tid}.png").convert('RGBA'))
    al=a[:,:,3]
    ink=al>60
    ys,xs=np.where(ink)
    boxes[tid]=[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())]
    print(tid,boxes[tid],"w",int(xs.max()-xs.min()),"h",int(ys.max()-ys.min()))
json.dump(boxes,open("boxes13.json","w"))
