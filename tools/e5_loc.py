# -*- coding: utf-8 -*-
"""Localize e5 tex1 system/nav button atlas: replace JP labels with Korean, matching each
button's text color (dark on light / white on dark), preserving left icon prefixes."""
import sys, json, numpy as np, cv2, os
sys.path.insert(0,'.'); import koloc
from PIL import Image
sys.stdout.reconfigure(encoding='utf-8')
SP=os.path.dirname(os.path.abspath(__file__))

btns=json.load(open(os.path.join(SP,'e5_btns.json')))
IDX2JP=[
'中止','中止','中止','中止','閉じる','承認','承認','承認','中止','中止',
'閉じる','閉じる','閉じる','閉じる','否認','閉じる','否認','否認','否認','否認',
'全解放','全解放','全解放','決定','否認','全解放','全解放','全解放','決定','決定',
'決定','決定','戻る','戻る','戻る','戻る','決定','拒否','拒否','拒否',
'拒否','拒否','拒否','姫','姫','姫','采配する','いいえ','いいえ','姫',
'姫','姫','戻る','戻る','いいえ','いいえ','いいえ','いいえ','采配する','再交渉',
'再交渉','再交渉','再交渉','采配する','采配する','采配する','采配する','再交渉','再交渉','承諾',
'承諾','承諾','承諾','処断','処断','スキップ','スキップ','スキップ','承諾','承諾',
'処断','処断','処断','処断','スキップ','スキップ','スキップ','開始','開始','登用',
'登用','登用','登用','開始','開始','開始','開始','登用','登用','武将',
'武将','武将','武将','はい','はい','次へ','次へ','次へ','武将','武将',
'はい','はい','はい','はい',
]
assert len(IDX2JP)==len(btns), f'{len(IDX2JP)} != {len(btns)}'
JP2KO={'中止':'중지','閉じる':'닫기','承認':'승인','否認':'부인','全解放':'전부개방','決定':'결정',
'戻る':'뒤로','拒否':'거부','姫':'공주','采配する':'지휘','いいえ':'아니오','再交渉':'재교섭',
'承諾':'승낙','処断':'처단','スキップ':'건너뛰기','開始':'개시','登用':'등용','武将':'무장',
'はい':'예','次へ':'다음','開戦':'개전'}
ICON_LABELS={'中止','閉じる','承認','否認','決定','戻る','拒否','承諾','再交渉','次へ','開戦'}

im=Image.open(os.path.join(SP,'loc_src','e5_t1.png')).convert('RGBA')
BASE=np.array(im).copy()

def localize(k):
    jp=IDX2JP[k]; ko=JP2KO.get(jp)
    if not ko: return
    x,y,w,h=btns[k]
    reg=BASE[y:y+h, x:x+w]
    rgb=reg[:,:,:3].astype(np.int32); al=reg[:,:,3]
    lum=0.299*rgb[:,:,0]+0.587*rgb[:,:,1]+0.114*rgb[:,:,2]
    # fill color from a strip just below the top border (no text there)
    fy0,fy1=int(h*0.13),int(h*0.24)
    fillmask=(al[fy0:fy1]>120)
    fill=np.median(rgb[fy0:fy1][fillmask],axis=0) if fillmask.sum()>10 else np.array([200,200,200])
    fill_lum=0.299*fill[0]+0.587*fill[1]+0.114*fill[2]
    # text band = vertical center (whole label incl. icon)
    band=np.zeros((h,w),bool); band[int(h*0.24):int(h*0.84), int(w*0.03):int(w*0.97)]=True
    diff=np.abs(lum-fill_lum)
    txt=((diff>40)&(al>70)&band).astype(np.uint8)
    txt=cv2.morphologyEx(txt,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
    if txt.sum()<15: return
    ys,xs=np.where(txt>0)
    tlum=np.median(lum[txt>0]); dark=tlum<fill_lum
    text_top,text_bot=int(ys.min()),int(ys.max())
    # target: KO centered on button, height = original text height, width capped
    tcx=w//2; box_w=int(w*0.66)
    tb=(tcx-box_w//2, text_top, tcx+box_w//2, text_bot)
    if dark:
        style=dict(text_rgb=(40,34,24),stroke_rgb=(246,243,233),glow_a=205,glow_stroke=1.4,glow_blur=1.0)
    else:
        style=dict(text_rgb=(249,249,251),stroke_rgb=(33,44,68),glow_a=0,glow_stroke=1.0,glow_blur=0.8)
    local=reg.copy()
    koloc.erase_place(local, txt, tb, ko, inpaint_r=5, **style)
    BASE[y:y+h, x:x+w]=local

if __name__=='__main__':
    args=sys.argv[1:]
    idxs=[int(a) for a in args] if args else range(len(btns))
    for k in idxs: localize(k)
    Image.fromarray(BASE,'RGBA').save(os.path.join(SP,'e5_t1_ko.png'))
    print(f'localized {len(list(idxs)) if args else len(btns)} buttons -> e5_t1_ko.png')
