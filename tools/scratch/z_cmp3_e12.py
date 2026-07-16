# -*- coding: utf-8 -*-
import os, numpy as np
from PIL import Image
os.chdir(r'C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad')
import koloc
res=open(koloc.RESJP,'rb').read()
e,coff,child,g=koloc.entry_gt1g(res,12)
t0=[x for x in koloc.g1t_textures(g) if x['tid']==0][0]
orig=t0['rgba']; locn=np.array(Image.open('loc_out/e12/t0.png').convert('RGBA'))
H,W=orig.shape[:2]
def onbg(a,c=12):
    h,w=a.shape[:2]; bg=np.zeros((h,w,3),np.uint8)
    yy,xx=np.mgrid[0:h,0:w]; chk=(((xx//c)+(yy//c))%2==0)
    bg[chk]=210; bg[~chk]=90
    al=a[:,:,3:4].astype(float)/255
    return (a[:,:,:3].astype(float)*al+bg*(1-al)).astype(np.uint8)
oi=onbg(orig); li=onbg(locn)
def pair(x0,x1,y0,y1,name,scale=3):
    a=oi[y0:y1,x0:x1]; b=li[y0:y1,x0:x1]; w=x1-x0; h=y1-y0; div=4
    c=np.full((h*2+div,w,3),255,np.uint8); c[:h]=a; c[h:h+div]=[255,0,0]; c[h+div:]=b
    im=Image.fromarray(c).resize((w*scale,(h*2+div)*scale),Image.NEAREST); im.save(name); print("saved",name,im.size)
# disc region: find via changed bbox. disc approx x 1560-1740
pair(1540,1760,0,240,'z_e12_disc.png',4)
# 전공1위 banner approx x 1780-1960 y 150-230
pair(1770,1970,140,235,'z_e12_banner1.png',6)
