# -*- coding: utf-8 -*-
import koloc, numpy as np
from PIL import Image
res=open(koloc.RESJP,'rb').read()
e,coff,child,g=koloc.entry_gt1g(res,16)
texs=koloc.g1t_textures(g)
t0=[x for x in texs if x['tid']==0][0]
orig=np.asarray(Image.fromarray(t0['rgba'],'RGBA').convert('RGB')).astype(np.int16)
loc=np.asarray(Image.open(r"loc_out/e16/t0.png").convert('RGB')).astype(np.int16)
d=np.abs(orig-loc).sum(2)
# where changed significantly
mask=(d>40).astype(np.uint8)*255
Image.fromarray(mask).save("qa_changemask.png")
# print bounding boxes of changed regions clustering by column bands
ys,xs=np.where(d>40)
print("changed px",len(xs),"xrange",xs.min(),xs.max(),"yrange",ys.min(),ys.max())
# For gun node region: measure darkness. Center node approx
# Let's find disc darkness: count dark pixels (lum<110) in gun row band y 470-545
def darkcount(img,box):
    x0,y0,x1,y1=box
    sub=img[y0:y1,x0:x1]
    lum=sub.mean(2)
    return (lum<110).sum(), sub.shape
band=(770,470,1290,548)
print("orig dark in gun band",darkcount(orig,band))
print("loc  dark in gun band",darkcount(loc,band))
# seiryoku oval band
band2=(955,335,1110,410)
print("orig dark seiryoku",darkcount(orig,band2))
print("loc  dark seiryoku",darkcount(loc,band2))
# shiro (red circle) band
band3=(790,340,1250,430)
print("orig dark shiro row",darkcount(orig,band3))
print("loc  dark shiro row",darkcount(loc,band3))
# overlay change mask on loc for viewing
ov=np.asarray(Image.open(r"loc_out/e16/t0.png").convert('RGB')).copy()
ov[d>40]=[255,0,255]
Image.fromarray(ov).crop((760,300,1300,620)).resize((540*2,320*2)).save("qa_change_overlay.png")
