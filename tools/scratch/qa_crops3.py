# -*- coding: utf-8 -*-
import koloc, numpy as np
from PIL import Image
res=open(koloc.RESJP,'rb').read()
e,coff,child,g=koloc.entry_gt1g(res,16)
texs=koloc.g1t_textures(g)
t0=[x for x in texs if x['tid']==0][0]
orig=Image.fromarray(t0['rgba'],'RGBA').convert('RGB')
loc=Image.open(r"loc_out/e16/t0.png").convert('RGB')
def crop(box,name,scale=1.0):
    a=orig.crop(box); b=loc.crop(box)
    if scale!=1.0:
        a=a.resize((int(a.width*scale),int(a.height*scale)))
        b=b.resize((int(b.width*scale),int(b.height*scale)))
    out=Image.new('RGB',(a.width,a.height*2+8),(40,40,40))
    out.paste(a,(0,0)); out.paste(b,(0,a.height+8))
    out.save(name); print(name,box,"orig size",orig.size)
crop((760,430,1300,560),"c_gun_circles.png",1.7)
crop((950,330,1130,420),"c_seiryoku_zoom.png",3.0)
