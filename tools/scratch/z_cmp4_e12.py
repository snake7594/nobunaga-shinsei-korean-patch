# -*- coding: utf-8 -*-
import os, numpy as np
from PIL import Image
os.chdir(r'C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad')
import koloc
res=open(koloc.RESJP,'rb').read()
e,coff,child,g=koloc.entry_gt1g(res,12)
t0=[x for x in koloc.g1t_textures(g) if x['tid']==0][0]
orig=t0['rgba']; locn=np.array(Image.open('loc_out/e12/t0.png').convert('RGBA'))
def solid(a,val=128):
    al=a[:,:,3:4].astype(float)/255
    return (a[:,:,:3].astype(float)*al+val*(1-al)).astype(np.uint8)
oi=solid(orig); li=solid(locn)
x0,x1,y0,y1=1540,1760,0,240
a=oi[y0:y1,x0:x1]; b=li[y0:y1,x0:x1]; w=x1-x0; h=y1-y0; div=4; s=4
c=np.full((h*2+div,w,3),255,np.uint8); c[:h]=a; c[h:h+div]=[255,0,0]; c[h+div:]=b
Image.fromarray(c).resize((w*s,(h*2+div)*s),Image.NEAREST).save('z_e12_disc_solid.png')
# alpha-only view to isolate emboss remnant
def alonly(a):
    v=a[:,:,3]; return np.dstack([v,v,v])
oa=alonly(orig); la=alonly(locn)
a=oa[y0:y1,x0:x1]; b=la[y0:y1,x0:x1]
c=np.full((h*2+div,w,3),255,np.uint8); c[:h]=a; c[h:h+div]=[255,0,0]; c[h+div:]=b
Image.fromarray(c).resize((w*s,(h*2+div)*s),Image.NEAREST).save('z_e12_disc_alpha.png')
print("done")
