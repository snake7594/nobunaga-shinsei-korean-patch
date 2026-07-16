import sys; sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
from PIL import Image
a=np.array(Image.open('loc_src/e12_t0.png').convert('RGBA'))
rgb=a[:,:,:3].astype(np.int32); L=0.299*rgb[:,:,0]+0.587*rgb[:,:,1]+0.114*rgb[:,:,2]
# stripe decoration x1810-1832
st=L[172:196,1810:1832]; print('stripe lum min/mean/p5', st.min(), round(st.mean(),1), np.percentile(st,5))
# 戦 fragment x1832-1845
fr=L[172:196,1832:1846]; print('fragment lum min/mean', fr.min(), round(fr.mean(),1))
