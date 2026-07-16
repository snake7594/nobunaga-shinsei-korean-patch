# -*- coding: utf-8 -*-
import koloc, numpy as np
from PIL import Image

res=open(koloc.RESJP,'rb').read()
e,coff,child,g=koloc.entry_gt1g(res,16)
texs=koloc.g1t_textures(g)
print("num tex", len(texs))
for t in texs:
    print("tid",t['tid'],"fmt",hex(t['fmt']),"w",t['w'],"h",t['h'],"rgba",None if t['rgba'] is None else t['rgba'].shape)

t0=[x for x in texs if x['tid']==0][0]
orig=Image.fromarray(t0['rgba'],'RGBA').convert('RGB')
loc=Image.open(r"loc_out/e16/t0.png").convert('RGB')
print("orig",orig.size,"loc",loc.size)

# full side by side (scaled down to fit)
def sbs(a,b,scale=0.5):
    w=int(a.width*scale); h=int(a.height*scale)
    a2=a.resize((w,h)); b2=b.resize((w,h))
    out=Image.new('RGB',(w*2+10,h),(40,40,40))
    out.paste(a2,(0,0)); out.paste(b2,(w+10,0))
    return out
sbs(orig,loc,0.5).save("qa_full.png")
