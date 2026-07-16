# -*- coding: utf-8 -*-
from PIL import Image
import os
for tid in [48,49,50,51,52,53,54,55,56]:
    p=f"loc_out/e13/t{tid}.png"
    im=Image.open(p)
    print(tid,im.size,im.mode, os.path.getsize(p))
