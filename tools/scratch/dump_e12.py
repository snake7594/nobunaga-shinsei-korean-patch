# -*- coding: utf-8 -*-
import koloc, numpy as np, os
from PIL import Image
res=open(koloc.RESJP,'rb').read()
e,coff,child,g=koloc.entry_gt1g(res,12)
texs=koloc.g1t_textures(g)
os.makedirs('loc_src',exist_ok=True)
for t in texs:
    print(f"tid={t['tid']} fmt=0x{t['fmt']:02X} w={t['w']} h={t['h']} rgba={'ok' if t['rgba'] is not None else 'None'}")
    if t['rgba'] is not None:
        Image.fromarray(t['rgba'],'RGBA').save(f"loc_src/e12_t{t['tid']}.png")
