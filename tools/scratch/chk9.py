# -*- coding: utf-8 -*-
import numpy as np
from PIL import Image
a=np.array(Image.open("loc_src/e13/t9.png").convert('RGBA'))
rgb=a[:,:,:3].astype(int); al=a[:,:,3]
lum=0.299*rgb[:,:,0]+0.587*rgb[:,:,1]+0.114*rgb[:,:,2]
# light pixels (potential white text) with alpha
light=(lum>150)&(al>60)
print('light count',light.sum())
if light.sum():
    ys,xs=np.where(light); print('light bbox x',xs.min(),xs.max(),'y',ys.min(),ys.max())
# unique-ish colors
print('max lum where alpha>100:', lum[al>100].max() if (al>100).any() else 'na')
