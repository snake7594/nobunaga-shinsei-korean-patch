import numpy as np
from PIL import Image
a=np.array(Image.open('loc_src/e12_t0.png')); b=np.array(Image.open('loc_out/e12/t0.png'))
print('src',a.shape,'out',b.shape,'match',a.shape==b.shape)
print('changed pixels', int((a!=b).any(axis=2).sum()))
