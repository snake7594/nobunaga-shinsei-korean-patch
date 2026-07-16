# -*- coding: utf-8 -*-
import os, numpy as np
from PIL import Image
os.chdir(r'C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad')
import koloc
res=open(koloc.RESJP,'rb').read()
e,coff,child,g=koloc.entry_gt1g(res,12)
t0=[x for x in koloc.g1t_textures(g) if x['tid']==0][0]
orig=t0['rgba']
locn=np.array(Image.open('loc_out/e12/t0.png').convert('RGBA'))

def onbg(a):
    h,w=a.shape[:2]; bg=np.zeros((h,w,3),np.uint8); c=16
    yy,xx=np.mgrid[0:h,0:w]
    chk=(((xx//c)+(yy//c))%2==0)
    bg[chk]=210; bg[~chk]=110
    al=a[:,:,3:4].astype(float)/255
    return (a[:,:,:3].astype(float)*al+bg*(1-al)).astype(np.uint8)

oi=onbg(orig); li=onbg(locn)
H,W=orig.shape[:2]
# vertical stack: orig top, red divider, loc bottom
div=6
canvas=np.full((H*2+div,W,3),255,np.uint8)
canvas[:H]=oi; canvas[H:H+div]=[255,0,0]; canvas[H+div:]=li
Image.fromarray(canvas).save('z_e12_vstack.png')

# crop the active region x 440..1950 for zoom, split into 2 halves for readability
def crop_pair(x0,x1,name,scale=1):
    a=oi[:,x0:x1]; b=li[:,x0:x1]
    w=x1-x0
    c=np.full((H*2+div,w,3),255,np.uint8)
    c[:H]=a; c[H:H+div]=[255,0,0]; c[H+div:]=b
    im=Image.fromarray(c)
    if scale!=1:
        im=im.resize((w*scale,(H*2+div)*scale),Image.NEAREST)
    im.save(name)
    print("saved",name,im.size)

crop_pair(440,1200,'z_e12_left.png',2)
crop_pair(1200,1950,'z_e12_right.png',2)
print("done")
