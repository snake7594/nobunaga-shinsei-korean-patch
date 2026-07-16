# -*- coding: utf-8 -*-
import numpy as np
from PIL import Image
im=Image.open('loc_src/e12_t0.png').convert('RGBA')
a=np.array(im)
print('shape',a.shape)
# crop regions and save upscaled
regions={
 'gunhyotei':(1350,0,1720,256),
 'tai':(1700,0,1950,256),
 'haiboku_shori':(1880,0,2048,256),
 'senkou1':(1730,150,1930,220),
 'senkou23':(430,150,720,220),
 'button_text':(800,120,1030,180),
}
for name,(x0,y0,x1,y1) in regions.items():
    c=im.crop((x0,y0,x1,y1))
    sc=3 if (x1-x0)<400 else 2
    c=c.resize((c.width*sc,c.height*sc),Image.NEAREST)
    c.save(f'z_{name}.png')
    print(name,(x0,y0,x1,y1))
