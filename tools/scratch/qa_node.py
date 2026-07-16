# -*- coding: utf-8 -*-
import koloc, numpy as np
from PIL import Image
res=open(koloc.RESJP,'rb').read()
e,coff,child,g=koloc.entry_gt1g(res,16)
texs=koloc.g1t_textures(g)
t0=[x for x in texs if x['tid']==0][0]
orig=Image.fromarray(t0['rgba'],'RGBA').convert('RGB')
loc=Image.open(r"loc_out/e16/t0.png").convert('RGB')
# center gun node tight
box=(975,465,1085,555)
a=orig.crop(box).resize((110*5,90*5),Image.NEAREST)
b=loc.crop(box).resize((110*5,90*5),Image.NEAREST)
out=Image.new('RGB',(a.width*2+8,a.height),(40,40,40))
out.paste(a,(0,0)); out.paste(b,(a.width+8,0))
out.save("c_node_center.png")
# left three gun nodes
box2=(775,470,1010,550)
a=orig.crop(box2).resize((235*4,80*4),Image.NEAREST)
b=loc.crop(box2).resize((235*4,80*4),Image.NEAREST)
out=Image.new('RGB',(a.width,a.height*2+8),(40,40,40))
out.paste(a,(0,0)); out.paste(b,(0,a.height+8))
out.save("c_node_left3.png")
print("done")
