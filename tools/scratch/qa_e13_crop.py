# -*- coding: utf-8 -*-
import koloc, numpy as np, json
from PIL import Image
res=open(koloc.RESJP,'rb').read()
e,coff,child,g=koloc.entry_gt1g(res,13)
texs={t['tid']:t for t in koloc.g1t_textures(g)}
boxes=json.load(open('boxes13.json'))
tids=[48,49,50,51,52,53,54,55,56]
def onbg(rgba):
    h,w=rgba.shape[:2]
    bg=np.zeros((h,w,3),np.uint8)
    for y in range(0,h,16):
        for x in range(0,w,16):
            bg[y:y+16,x:x+16]=[60,60,60] if ((x//16)+(y//16))%2==0 else [120,120,120]
    a=rgba[:,:,3:4].astype(float)/255
    return (rgba[:,:,:3].astype(float)*a+bg*(1-a)).astype(np.uint8)
# crop x from 360 to 920 to capture full ink area + margin, full height
x0,x1=360,940
rows=[]
labels={48:'okehazama',49:'nagashino',50:'mikatagahara',51:'hieizan',52:'kanegasaki',53:'kicho',54:'zentokuji',55:'itsukushima',56:'kawanakajima'}
for tid in tids:
    orig=texs[tid]['rgba']
    loc=np.array(Image.open(f'loc_out/e13/t{tid}.png').convert('RGBA'))
    oi=onbg(orig)[:,x0:x1]; li=onbg(loc)[:,x0:x1]
    # draw box from boxes json
    bx=boxes[str(tid)]
    gap=np.full((4,oi.shape[1],3),255,np.uint8)
    pair=np.vstack([oi,gap,li])
    sep=np.full((12,pair.shape[1],3),[200,40,40],np.uint8)
    rows.append(np.vstack([pair,sep]))
comb=np.vstack(rows)
im=Image.fromarray(comb)
# scale up 1.4x
im=im.resize((int(im.width*1.3),int(im.height*1.3)),Image.LANCZOS)
im.save('qa_e13_stack.png')
print(im.size)
