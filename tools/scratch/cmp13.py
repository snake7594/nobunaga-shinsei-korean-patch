# -*- coding: utf-8 -*-
import numpy as np
from PIL import Image
ids=[48,49,50,51,52,53,54,55,56]
rows=[]
for tid in ids:
    o=Image.open(f"loc_src/e13/t{tid}.png").convert('RGBA').crop((380,0,900,110))
    n=Image.open(f"loc_out/e13/t{tid}.png").convert('RGBA').crop((380,0,900,110))
    bg=Image.new('RGBA',(o.width*2+30,o.height),(70,70,78,255))
    bg.alpha_composite(o,(0,0)); bg.alpha_composite(n,(o.width+30,0))
    rows.append(bg.convert('RGB'))
W=max(r.width for r in rows); Htot=sum(r.height for r in rows)+ (len(rows)-1)*8
sheet=Image.new('RGB',(W,Htot),(40,40,40)); y=0
for r in rows:
    sheet.paste(r,(0,y)); y+=r.height+8
sheet.save("cmp13_all.png"); print("saved",sheet.size)
