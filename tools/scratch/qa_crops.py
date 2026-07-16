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
    out.save(name)
    print(name,box)

# top-left menu tree (知行 内政 戦)
crop((0,0,700,300),"c_topleft.png",1.4)
# tenka touitsu red
crop((250,300,560,430),"c_tenka.png",2.5)
# seiryoku / shiro / gun cluster
crop((740,300,1300,620),"c_seiryoku.png",1.4)
# right pyramid panel
crop((1300,300,1780,620),"c_pyramid_r.png",1.3)
# full right nav
crop((1560,0,2048,320),"c_nav.png",1.4)
