# -*- coding: utf-8 -*-
import os, numpy as np
from PIL import Image
os.chdir(r'C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad')
import koloc

res=open(koloc.RESJP,'rb').read()
e,coff,child,g=koloc.entry_gt1g(res,12)
texs=koloc.g1t_textures(g)
print("ntex",len(texs))
for t in texs:
    print("tid",t['tid'],"fmt",hex(t['fmt']),"w",t['w'],"h",t['h'],"rgba",None if t['rgba'] is None else t['rgba'].shape)

t0=[x for x in texs if x['tid']==0][0]
orig=t0['rgba']  # HxW x4
loc=Image.open('loc_out/e12/t0.png').convert('RGBA')
locn=np.array(loc)
print("orig",orig.shape,"loc",locn.shape)

# checkerboard bg for transparency
def onbg(a):
    h,w=a.shape[:2]
    bg=np.zeros((h,w,3),np.uint8)
    c=32
    for y in range(0,h,c):
        for x in range(0,w,c):
            bg[y:y+c,x:x+c]=200 if ((x//c+y//c)%2==0) else 120
    al=a[:,:,3:4].astype(float)/255
    return (a[:,:,:3].astype(float)*al+bg*(1-al)).astype(np.uint8)

oi=onbg(orig); li=onbg(locn)
# texture is 256 wide x 2048 tall per notes (w=256,h=2048). Side-by-side would be very tall & narrow.
# Stack horizontally: orig | gap | loc
H=orig.shape[0]; W=orig.shape[1]
gap=8
canvas=np.full((H,W*2+gap,3),255,np.uint8)
canvas[:, :W]=oi
canvas[:, W+gap:]=li
Image.fromarray(canvas).save('z_e12_cmp.png')
print("saved cmp", canvas.shape)

# Also diff mask
diff=(orig.astype(int)-locn.astype(int))
changed=(np.abs(diff).sum(2)>0)
print("changed px",int(changed.sum()),"of",H*W)
ys,xs=np.where(changed)
if len(ys):
    print("changed bbox y",ys.min(),ys.max(),"x",xs.min(),xs.max())
