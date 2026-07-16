# -*- coding: utf-8 -*-
"""Localize entry-13 battle-name banners (gold brush calligraphy) to Korean."""
import io, json, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import koloc

FB=koloc.FB
boxes=json.load(open("boxes13.json"))
KO={
 "48":"오케하자마 전투","49":"나가시노 전투","50":"미카타가하라 전투",
 "51":"히에이잔 방화","52":"가네가사키 철퇴전","53":"기초 혼례",
 "54":"젠토쿠지 회맹","55":"이쓰쿠시마 전투","56":"가와나카지마 전투",
}

def render_gold_fit(ko, box_w, box_h, S=4, fill=0.98):
    f=ImageFont.truetype(io.BytesIO(FB),44*S); pad=16*S
    W=len(ko)*44*S+2*pad; H=44*S+2*pad
    sw=max(1,int(0.9*S))
    fillmsk=Image.new('L',(W,H),0)
    ImageDraw.Draw(fillmsk).text((pad,pad),ko,font=f,fill=255)
    outmsk=Image.new('L',(W,H),0)
    ImageDraw.Draw(outmsk).text((pad,pad),ko,font=f,fill=255,stroke_width=sw,stroke_fill=255)
    ib=outmsk.getbbox()
    iw=ib[2]-ib[0]; ih=ib[3]-ib[1]
    fscale=min(box_w*S/iw, box_h*S/ih)*fill/S
    fa=np.array(fillmsk).astype(np.float32)/255
    oa=np.array(outmsk).astype(np.float32)/255
    ys=np.arange(H).astype(np.float32)
    t=np.clip((ys-ib[1])/max(1,ih),0,1)
    stops=[(0.0,(252,248,240)),(0.28,(232,214,170)),(0.58,(198,166,108)),(1.0,(150,116,64))]
    grad=np.zeros((H,3),np.float32)
    for c in range(3):
        grad[:,c]=np.interp(t,[s[0] for s in stops],[s[1][c] for s in stops])
    gradimg=np.repeat(grad[:,None,:],W,axis=1)
    stroke_col=np.array([70,52,28],np.float32)
    outonly=np.clip(oa-fa,0,1)
    rgb=gradimg*fa[:,:,None]+stroke_col[None,None,:]*outonly[:,:,None]
    alpha=np.clip(oa,0,1)*255
    img=Image.fromarray(np.dstack([rgb,alpha]).astype(np.uint8),'RGBA')
    mrg=int(7*S); cl,ct,cr,cb=max(0,ib[0]-mrg),max(0,ib[1]-mrg),min(W,ib[2]+mrg),min(H,ib[3]+mrg)
    crop=img.crop((cl,ct,cr,cb))
    nw=max(1,round(crop.width*fscale)); nh=max(1,round(crop.height*fscale))
    layer=crop.resize((nw,nh),Image.LANCZOS)
    icx=((ib[0]+ib[2])/2-cl)*fscale; icy=((ib[1]+ib[3])/2-ct)*fscale
    return layer,(icx,icy)

for tid,ko in KO.items():
    x0,y0,x1,y1=boxes[tid]
    src=np.array(Image.open(f"loc_src/e13/t{tid}.png").convert('RGBA'))
    H,W=src.shape[:2]
    out=Image.new('RGBA',(W,H),(0,0,0,0))
    bw=x1-x0+1; bh=y1-y0+1
    layer,ink=render_gold_fit(ko,bw,bh)
    # soft dark shadow underlay for legibility on light UI backgrounds
    sh=Image.new('RGBA',layer.size,(0,0,0,0))
    a=np.array(layer)[:,:,3]
    shrgb=np.zeros((*a.shape,4),np.uint8); shrgb[:,:,3]=(a*0.5).astype(np.uint8)
    sh=Image.fromarray(shrgb,'RGBA').filter(ImageFilter.GaussianBlur(2))
    jcx=(x0+x1)/2; jcy=(y0+y1)/2
    px=int(round(jcx-ink[0])); py=int(round(jcy-ink[1]))
    out.alpha_composite(sh,(px+1,py+2))
    out.alpha_composite(layer,(px,py))
    arr=np.array(out)
    assert arr.shape[:2]==(H,W)
    Image.fromarray(arr,'RGBA').save(f"loc_out/e13/t{tid}.png")
    print("saved",tid,ko,"box",bw,"x",bh)
