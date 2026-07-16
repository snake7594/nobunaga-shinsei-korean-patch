"""Extract textures from the previously-missed res_lang entries (correct LINK TOC parse)."""
import struct, sys, os, io
import numpy as np, lz4.block, texture2ddecoder
from PIL import Image, ImageDraw
sys.stdout.reconfigure(encoding='utf-8')

def kt(b):
    if len(b)>=24 and b[0]==1 and b[1]==1:
        try:
            dec=struct.unpack_from('<Q',b,8)[0]; comp=struct.unpack_from('<Q',b,16)[0]
            if dec>5e8 or comp>len(b): return None
            return lz4.block.decompress(b[24:24+comp],uncompressed_size=dec)
        except: return None
    return None
def link_children(d):
    if d[:4]!=b'LINK' or len(d)<20: return None
    cnt=struct.unpack_from('<I',d,4)[0]; toc=struct.unpack_from('<I',d,8)[0]
    if cnt>500000 or toc+cnt*8>len(d): return None
    ch=[]
    for i in range(cnt):
        o,s=struct.unpack_from('<II',d,toc+i*8)
        ch.append(d[o:o+s] if (s and o+s<=len(d)) else None)
    return ch
def bc_dds(linear,w,h,fourcc):
    dds=bytearray(128)
    struct.pack_into('<4s',dds,0,b'DDS '); struct.pack_into('<I',dds,4,124)
    struct.pack_into('<I',dds,8,0x00081007); struct.pack_into('<I',dds,12,h)
    struct.pack_into('<I',dds,16,w); struct.pack_into('<I',dds,20,len(linear))
    struct.pack_into('<I',dds,76,32); struct.pack_into('<I',dds,80,0x4)
    struct.pack_into('<4s',dds,84,fourcc); struct.pack_into('<I',dds,108,0x1000)
    return Image.open(io.BytesIO(bytes(dds)+linear)).convert('RGBA')
def dec_g1t(g):
    tbl=struct.unpack_from('<I',g,0x0C)[0]; ntex=struct.unpack_from('<I',g,0x10)[0]
    if ntex>8192: return []
    offs=struct.unpack_from(f'<{ntex}I',g,tbl); res=[]
    for k,o in enumerate(offs):
        p=tbl+o
        if p+12>len(g): continue
        fmt,dxdy=g[p+1],g[p+2]; w=1<<(dxdy&0xF); h=1<<(dxdy>>4)
        ex=struct.unpack_from('<I',g,p+8)[0]; end=tbl+offs[k+1] if k+1<ntex else len(g)
        data=g[p+8+ex:end]
        try:
            if fmt==0x59: res.append((bc_dds(bytes(data[:(w//4)*(h//4)*8]),w,h,b'DXT1'),f'BC1 {w}x{h}'))
            elif fmt==0x5B: res.append((bc_dds(bytes(data[:(w//4)*(h//4)*16]),w,h,b'DXT5'),f'BC3 {w}x{h}'))
            elif fmt==0x5C:
                dec=texture2ddecoder.decode_bc4(bytes(data[:(w//4)*(h//4)*8]),w,h)
                a=np.frombuffer(dec,dtype=np.uint8).reshape(h,w,4); res.append((Image.fromarray(a[:,:,[2,1,0,3]].copy(),'RGBA'),f'BC4 {w}x{h}'))
            elif fmt==0x5F:
                dec=texture2ddecoder.decode_bc7(bytes(data[:(w//4)*(h//4)*16]),w,h)
                a=np.frombuffer(dec,dtype=np.uint8).reshape(h,w,4); res.append((Image.fromarray(a[:,:,[2,1,0,3]].copy(),'RGBA'),f'BC7 {w}x{h}'))
            elif fmt==0x01:
                a=np.frombuffer(data[:w*h*4],dtype=np.uint8).reshape(h,w,4); res.append((Image.fromarray(a[:,:,[2,1,0,3]].copy(),'RGBA'),f'BGRA8 {w}x{h}'))
            else: res.append((None,f'fmt0x{fmt:02X} {w}x{h}'))
        except Exception as e: res.append((None,f'ERR{e}'))
    return res

JP=r'D:\nsw\rom\노부나가의 야망 신생_일본판\추출원본\romfs\RES_JP\res_lang.bin'
d=open(JP,'rb').read()
OUT=r'D:\nsw\rom\노부나가의 야망 신생_일본판\이미지한글화\hidden_png'
SHEET=r'D:\nsw\rom\노부나가의 야망 신생_일본판\이미지한글화\contact_sheets'
os.makedirs(OUT,exist_ok=True)
ENTRIES=[5,8,9,11,12,13,16,24]
for i in ENTRIES:
    o,s=struct.unpack_from('<II',d,16+i*8); sub=d[o:o+s]
    ch=link_children(sub)
    g=kt(ch[0])
    if g is None or g[:4]!=b'GT1G': print(f'entry {i}: no GT1G'); continue
    imgs=dec_g1t(g)
    ok=[(t,im,info) for t,(im,info) in enumerate(imgs) if im]
    print(f'entry {i}: {len(imgs)} textures, {len(ok)} decoded')
    thumbs=[]
    for t,im,info in ok:
        im.save(os.path.join(OUT,f'e{i}_{t:03d}.png'))
        bg=Image.new('RGBA',im.size,(235,235,240,255))
        comp=Image.alpha_composite(bg,im).convert('RGB'); comp.thumbnail((240,240))
        thumbs.append((f'e{i}_{t}',info,comp))
    per=42; COLS=7; CW=232; CH=210; CAP=16
    for sidx in range(0,len(thumbs),per):
        rows=(min(per,len(thumbs)-sidx)+COLS-1)//COLS
        sheet=Image.new('RGB',(COLS*CW+8,rows*(CH+CAP)+8),(40,40,55)); dr=ImageDraw.Draw(sheet)
        for idx,(nm,info,im) in enumerate(thumbs[sidx:sidx+per]):
            cx=8+(idx%COLS)*CW; cy=8+(idx//COLS)*(CH+CAP)
            sheet.paste(im,(cx+(224-im.width)//2,cy+(200-im.height)//2))
            dr.text((cx+2,cy+CH-2),f'{nm} {info}',fill=(255,255,150))
        sheet.save(os.path.join(SHEET,f'hidden_e{i}_{sidx//per}.jpg'),quality=80)
    print(f'  sheets: hidden_e{i}_*')
