# -*- coding: utf-8 -*-
import numpy as np
from PIL import Image
# banners: crop x 380..900
for tid in [48,49,50,51,52,53,54,55,56]:
    a=Image.open(f"loc_src/e13/t{tid}.png").convert('RGBA')
    c=a.crop((380,0,900,110))
    # composite on gray to see light/gold text
    bg=Image.new('RGBA',c.size,(90,90,90,255))
    bg.alpha_composite(c)
    bg.convert('RGB').save(f"v_t{tid}.png")
# t9 left
a=Image.open("loc_src/e13/t9.png").convert('RGBA')
c=a.crop((0,0,1360,256))
bg=Image.new('RGBA',c.size,(90,90,90,255)); bg.alpha_composite(c)
bg.convert('RGB').save("v_t9.png")
print("done")
