# -*- coding: utf-8 -*-
"""Localize res_lang entry-8 command-button atlas (e8_000): replace baked JP kanji labels
with Korean, preserving cloud/pictogram/arrows. Renders onto a copy + comparison sheets."""
import sys, json, numpy as np, cv2, io, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.stdout.reconfigure(encoding='utf-8')

SP=r'C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad'
ATLAS=r'D:\nsw\rom\노부나가의 야망 신생_일본판\이미지한글화\hidden_png\e8_000.png'
FB=open(r'D:\nsw\rom\노부나가의 야망 신생_일본판\추출원본\SeoulHangangB.ttf','rb').read()
centers=json.load(open(os.path.join(SP,'centers.json')))

# ---- transcription: index -> JP command ----
IDX2JP=[
'評定','評定','評定','評定','評定','評定','任命','任命','任命','任命','任命','任命','軍事','軍事',
'軍事','軍事','軍事','軍事','内政','内政','内政','内政','内政','帰城','内政','外交','外交','外交',
'外交','外交','外交','部隊情報','部隊情報','部隊情報','部隊情報','部隊情報','出陣','出陣','出陣','出陣','出陣','出陣',
'帰城','帰城','帰城','帰城','帰城','編制','入城','強攻','包囲','包囲','包囲','包囲','包囲','包囲',
'編制','編制','入城','入城','入城','入城','入城','目標','目標','目標','目標','目標','目標','強攻',
'強攻','強攻','強攻','強攻','編集','編制','解散','解散','解散','閉じる','閉じる','閉じる','閉じる','閉じる',
'閉じる','編制','編制','合戦','合戦','合戦','合戦','合戦','合戦','出陣取消','出陣取消','出陣取消','出陣取消','出陣取消',
'出陣取消','解散','解散','解散','国衆情報','編集','援軍取消','援軍取消','援軍取消','援軍取消','援軍取消','国衆情報','国衆情報','国衆情報',
'国衆情報','編集','編集','編集','編集','解除','解除','解除','解除','解除','解除','援軍要請','援軍要請','援軍要請',
'援軍要請','援軍要請','援軍要請','援軍取消','出陣','国衆情報','城情報','移動','移動','移動','移動','移動','移動','出陣',
'出陣','国衆懐柔','国衆懐柔','国衆懐柔','国衆懐柔','国衆懐柔','国衆懐柔','国衆取込','国衆取込','国衆取込','国衆取込','国衆取込','国衆取込','城情報',
'城情報','城情報','城情報','城情報','一括知行','出陣','城下施設','城下施設','城下施設','本拠','本拠','本拠','本拠','本拠',
'本拠','出陣','出陣','武将情報','武将情報','武将情報','武将情報','武将情報','武将情報','呼寄','呼寄','呼寄','呼寄','呼寄',
'呼寄','城下施設','城下施設','城下施設','軍事','一括知行','任命','任命',
# 190+
'任命','任命','任命','軍事','軍事','軍事','軍事','一括知行','一括知行','一括知行','一括知行','勢力情報','勢力情報','勢力情報',
'勢力情報','勢力情報','勢力情報','情報','情報','情報','情報','情報','情報','任命','合戦情報','軍事','調略','郡情報',
'郡情報','郡情報','郡情報','郡情報','郡情報','合戦情報','合戦情報','内政','内政','内政','内政','内政','内政','領内諸策',
'領内諸策','領内諸策','領内諸策','領内諸策','領内諸策','調略','調略','調略','調略','調略','転封','合戦情報','郡開発','郡開発',
'郡開発','知行','知行','知行','知行','知行','知行','合戦情報','合戦情報','知行','知行','知行','知行','知行',
'知行','代官','代官','代官','代官','代官','代官','郡開発','郡開発','郡開発','調略','転封','攻略目標','攻略目標',
'攻略目標','攻略目標','攻略目標','調略','調略','調略','調略','転封','転封','転封','転封','代官','代官','代官',
'代官','代官','代官','出陣','出陣','出陣','出陣','出陣','出陣','攻略目標','交渉','調略','領内諸策','親善',
'親善','親善','親善','親善','交渉','交渉','城下施設','城下施設','城下施設','城下施設','城下施設','城下施設','城下施設','郡開発',
'郡開発','郡開発','郡開発','郡開発','郡開発','領内諸策','領内諸策','領内諸策','領内諸策','領内諸策','郡開発','交渉','攻略目標','攻略目標',
'攻略目標','出陣','出陣','出陣','出陣','出陣','出陣','交渉','交渉','朝廷','朝廷','朝廷','朝廷','朝廷',
'朝廷','役職','役職','役職','役職','役職','役職','攻略目標','攻略目標','攻略目標','郡開発','','','',
'','郡開発','郡開発','郡開発','郡開発','','','主命','','主命','主命','主命','主命','主命',
'移転','移転','移転','移転','移転','移転','部隊情報','',
]
assert len(IDX2JP)==len(centers), f'{len(IDX2JP)} != {len(centers)}'

JP2KO={
'評定':'평정','内政':'내정','任命':'임명','軍事':'군사','外交':'외교','郡開発':'군개발',
'領内諸策':'영지제책','知行':'지행','代官':'대관','転封':'전봉','城下施設':'성하시설',
'本拠':'본거지','出陣':'출진','帰城':'귀성','入城':'입성','強攻':'강공','包囲':'포위',
'編制':'편제','編集':'편집','解散':'해산','閉じる':'닫기','合戦':'합전','出陣取消':'출진취소',
'援軍取消':'원군취소','援軍要請':'원군요청','国衆情報':'국인정보','国衆懐柔':'국인회유',
'国衆取込':'국인포섭','城情報':'성정보','移動':'이동','目標':'목표','部隊情報':'부대정보',
'一括知行':'일괄지행','武将情報':'무장정보','呼寄':'호출','勢力情報':'세력정보','情報':'정보',
'郡情報':'군정보','合戦情報':'합전정보','調略':'조략','攻略目標':'공략목표','交渉':'교섭',
'親善':'친선','朝廷':'조정','役職':'역직','主命':'주명','移転':'이전','解除':'해제',
}

im=Image.open(ATLAS).convert('RGBA')
BASE=np.array(im).copy()
BW,BH=80,92

def detect_label(cx,cy):
    """Return (text_bbox, dark_mask, (x0,y0)) in button-local coords, or (None,...)."""
    x0,y0=cx-BW//2,cy-BH//2
    c=np.array(Image.fromarray(BASE,'RGBA').crop((x0,y0,x0+BW,y0+BH)))
    rgb=c[:,:,:3].astype(np.int32); al=c[:,:,3]
    lum=0.299*rgb[:,:,0]+0.587*rgb[:,:,1]+0.114*rgb[:,:,2]
    band=np.zeros((BH,BW),bool); band[53:82,3:77]=True
    dark=((lum<108)&(al>55)&band).astype(np.uint8)
    if dark.sum()<8: return None,None,(x0,y0)
    ys,xs=np.where(dark>0)
    return (int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())),dark,(x0,y0)

def render_ko_fit(ko, box_w, box_h, S=4, text_rgb=(24,28,42), stroke_rgb=(243,243,246),
                  glow_a=235, glow_stroke=1.6, glow_blur=1.1, fill=0.98, font_bytes=None):
    """Render KO; scale so its DARK-INK bbox fits within (box_w,box_h) target px.
    Returns (layer RGBA in target px, (ink_cx, ink_cy) within layer)."""
    fb=font_bytes if font_bytes is not None else FB
    fsz=44; f=ImageFont.truetype(io.BytesIO(fb),fsz*S); pad=10*S
    W=len(ko)*fsz*S+2*pad; H=fsz*S+2*pad
    probe=Image.new('L',(W,H)); ImageDraw.Draw(probe).text((pad,pad),ko,font=f,fill=255,stroke_width=S)
    ib=probe.getbbox()
    if ib is None: return None,None
    iw=ib[2]-ib[0]; ih=ib[3]-ib[1]
    fscale=min(box_w*S/iw, box_h*S/ih)*fill/S
    comp=Image.new('RGBA',(W,H),(0,0,0,0))
    gl=Image.new('RGBA',(W,H),(0,0,0,0))
    ImageDraw.Draw(gl).text((pad,pad),ko,font=f,fill=(255,255,255,glow_a),
                            stroke_width=int(glow_stroke*S),stroke_fill=(255,255,255,glow_a))
    gl=gl.filter(ImageFilter.GaussianBlur(int(glow_blur*S)))
    comp=Image.alpha_composite(comp,gl)
    ImageDraw.Draw(comp).text((pad,pad),ko,font=f,fill=text_rgb+(255,),
                              stroke_width=S,stroke_fill=stroke_rgb+(255,))
    mrg=int(5*S); cl,ct,cr,cb=max(0,ib[0]-mrg),max(0,ib[1]-mrg),min(W,ib[2]+mrg),min(H,ib[3]+mrg)
    crop=comp.crop((cl,ct,cr,cb))
    nw=max(1,round(crop.width*fscale)); nh=max(1,round(crop.height*fscale))
    layer=crop.resize((nw,nh),Image.LANCZOS)
    icx=((ib[0]+ib[2])/2-cl)*fscale; icy=((ib[1]+ib[3])/2-ct)*fscale
    return layer,(icx,icy)

def render_button(cx,cy,ko):
    bb,dark,(x0,y0)=detect_label(cx,cy)
    if bb is None: return
    tx0,ty0,tx1,ty1=bb
    # erase: inpaint dark text (dilated) within padded button region
    reg=np.array(Image.fromarray(BASE,'RGBA').crop((x0,y0,x0+BW,y0+BH)))
    rgb=reg[:,:,:3].copy().astype(np.uint8); al=reg[:,:,3].copy().astype(np.uint8)
    mask=cv2.dilate(dark,np.ones((5,5),np.uint8),iterations=2)
    # detect wheel arrows: dark components whose centroid is at the far left/right edge
    ncomp,lab,stats,cent=cv2.connectedComponentsWithStats(dark,connectivity=8)
    arrow_cols=np.zeros((BH,BW),bool)
    for ci in range(1,ncomp):
        area=stats[ci,cv2.CC_STAT_AREA]; cxx=cent[ci,0]
        if area<220 and (cxx<18 or cxx>BW-18):   # small blob near an edge = arrow
            arrow_cols|=(lab==ci)
    arrow_cols=cv2.dilate(arrow_cols.astype(np.uint8),np.ones((3,3),np.uint8),1).astype(bool)
    mask[arrow_cols]=0   # don't inpaint arrows
    inp=cv2.inpaint(rgb,mask,4,cv2.INPAINT_TELEA)
    # --- KO render, fit to JP ink box (jw x jh), centered on JP ink center ---
    jw=tx1-tx0+1; jh=ty1-ty0+1; jcx=(tx0+tx1)/2; jcy=(ty0+ty1)/2
    base=Image.fromarray(np.dstack([inp,al]).astype(np.uint8),'RGBA')
    layer,ink=render_ko_fit(ko,jw,jh)
    if layer is not None:
        px=int(round(jcx-ink[0])); py=int(round(jcy-ink[1]))
        base.alpha_composite(layer,(px,py))
    out=np.array(base)
    # restore original arrow pixels (they were protected from inpaint, but KO glow may cover them)
    if arrow_cols.any():
        out[arrow_cols]=reg[arrow_cols]
    # write back only the valid overlap with the atlas
    H,W=BASE.shape[:2]
    ax0,ay0=max(0,x0),max(0,y0); ax1,ay1=min(W,x0+BW),min(H,y0+BH)
    ox0,oy0=ax0-x0,ay0-y0
    BASE[ay0:ay1, ax0:ax1]=out[oy0:oy0+(ay1-ay0), ox0:ox0+(ax1-ax0)]

if __name__=='__main__':
    import sys as _s
    lo,hi=(int(_s.argv[1]),int(_s.argv[2])) if len(_s.argv)>2 else (0,len(centers))
    for i in range(lo,hi):
        jp=IDX2JP[i]
        if not jp: continue
        ko=JP2KO.get(jp)
        if not ko: print('  no KO for',jp,'idx',i); continue
        render_button(centers[i][0],centers[i][1],ko)
    Image.fromarray(BASE,'RGBA').save(os.path.join(SP,'e8_ko.png'))
    print(f'rendered {lo}-{hi}, saved e8_ko.png')
