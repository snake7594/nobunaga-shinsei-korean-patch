# -*- coding: utf-8 -*-
import sys; sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
from PIL import Image
a=np.array(Image.open('loc_src/e12_t0.png').convert('RGBA'))
al=a[:,:,3]
def stat(x0,y0,x1,y1,name):
    r=al[y0:y1,x0:x1]
    print(f'{name}: alpha min={r.min()} max={r.max()} mean={r.mean():.1f} frac_transparent(<20)={(r<20).mean():.2f} frac_opaque(>200)={(r>200).mean():.2f}')
stat(1183,31,1544,169,'gunhyotei')
stat(1805,15,1929,111,'haiboku')
stat(1801,105,1949,199,'shori')
# corners just outside text to see bg
stat(1183,0,1544,10,'gun_top_strip')
stat(1560,15,1600,111,'left_of_haiboku')
