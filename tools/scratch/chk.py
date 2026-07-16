import sys; sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
from PIL import Image
a=np.array(Image.open('loc_src/e12_t0.png').convert('RGBA'))
al=a[:,:,3]
# button text row y138-165, find leftmost opaque col in x780-830
sub=al[136:168,778:840]
cols=np.where(sub.max(0)>60)[0]
print('button leftmost opaque x=',778+cols.min() if len(cols) else None, 'to', 778+cols.max())
# senkou1 leftmost text x1828-1845
s=al[170:199,1826:1850]
c=np.where(s.max(0)>60)[0]
print('senkou1 leftmost opaque',1826+c.min() if len(c) else None)
