# -*- coding: utf-8 -*-
import koloc, numpy as np, json
from PIL import Image
res=open(koloc.RESJP,'rb').read()
e,coff,child,g=koloc.entry_gt1g(res,13)
texs={t['tid']:t for t in koloc.g1t_textures(g)}
boxes=json.load(open('boxes13.json'))
def bbox_alpha(rgba,thr=40):
    a=rgba[:,:,3]>thr
    ys,xs=np.where(a)
    if len(xs)==0: return None
    return int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())
tids=[48,49,50,51,52,53,54,55,56]
for tid in tids:
    orig=texs[tid]['rgba']; loc=np.array(Image.open(f'loc_out/e13/t{tid}.png').convert('RGBA'))
    ob=bbox_alpha(orig); lb=bbox_alpha(loc); jb=boxes[str(tid)]
    ow=ob[2]-ob[0]; oh=ob[3]-ob[1]; lw=lb[2]-lb[0]; lh=lb[3]-lb[1]
    print(f"t{tid}: JPbox={jb} origInk(w={ow},h={oh}) locInk x=[{lb[0]},{lb[2]}] y=[{lb[1]},{lb[3]}] (w={lw},h={lh})")
# tex9 check
if 9 in texs:
    t9=texs[9]['rgba']
    a=t9[:,:,3]; rgb=t9[:,:,:3]
    lum=rgb.max(axis=2)
    light=np.sum((lum>60)&(a>100))
    print(f"tex9 shape={t9.shape} maxlum(a>100)={lum[a>100].max() if (a>100).any() else 'na'} lightpx={light} alpha_range=[{a.min()},{a.max()}]")
