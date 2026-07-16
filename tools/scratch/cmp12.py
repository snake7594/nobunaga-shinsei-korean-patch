# -*- coding: utf-8 -*-
from PIL import Image
a=Image.open('loc_src/e12_t0.png').convert('RGBA')
b=Image.open('loc_out/e12/t0.png').convert('RGBA')
W,H=a.size
c=Image.new('RGBA',(W,H*2+10),(30,30,30,255))
c.paste(a,(0,0)); c.paste(b,(0,H+10))
c.save('z_cmp12_full.png')
# zoom crops before/after for right cluster and banners
def pair(x0,y0,x1,y1,name,sc=2):
    ca=a.crop((x0,y0,x1,y1)); cb=b.crop((x0,y0,x1,y1))
    w,h=ca.size
    out=Image.new('RGBA',(w*sc,h*2*sc+6),(30,30,30,255))
    out.paste(ca.resize((w*sc,h*sc),Image.NEAREST),(0,0))
    out.paste(cb.resize((w*sc,h*sc),Image.NEAREST),(0,h*sc+6))
    out.save(f'z_cmp12_{name}.png')
pair(1160,0,2048,220,'right',2)
pair(420,120,1060,225,'bottomleft',2)
