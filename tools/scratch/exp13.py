# -*- coding: utf-8 -*-
import koloc, numpy as np
from PIL import Image
res=open(koloc.RESJP,'rb').read()
e,coff,child,g=koloc.entry_gt1g(res,13)
texs=koloc.g1t_textures(g)
print('ntex',len(texs))
ids=[9,48,49,50,51,52,53,54,55,56]
for t in texs:
    if t['tid'] in ids:
        print(t['tid'],'fmt',hex(t['fmt']),t['w'],'x',t['h'],'rgba',None if t['rgba'] is None else t['rgba'].shape)
        if t['rgba'] is not None:
            Image.fromarray(t['rgba'],'RGBA').save(f"loc_src/e13/t{t['tid']}.png")
