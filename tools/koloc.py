# -*- coding: utf-8 -*-
"""Shared helpers for localizing res_lang G1T texture atlases to Korean.
Decode (BC1/3/4/7/BGRA8), fit-to-box KO text render, inpaint-erase, mixed-BC encode,
and full res_lang repack across multiple entries."""
import struct, os, io, numpy as np, cv2, lz4.block, texture2ddecoder
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FB=open(r'D:\nsw\rom\노부나가의 야망 신생_일본판\추출원본\SeoulHangangB.ttf','rb').read()
RESJP=r'D:\nsw\rom\노부나가의 야망 신생_일본판\추출원본\romfs\RES_JP\res_lang.bin'

# ---------------- archive parse ----------------
def kt_decompress(b):
    dec=struct.unpack_from('<Q',b,8)[0]; comp=struct.unpack_from('<Q',b,16)[0]
    return lz4.block.decompress(b[24:24+comp],uncompressed_size=dec)
def kt_wrap(orig_child, new_raw):
    """Re-wrap new_raw preserving the original KT header magic+hash (bytes 0-7)."""
    comp=lz4.block.compress(new_raw, mode='high_compression', compression=12, store_size=False)
    return orig_child[:8]+struct.pack('<Q',len(new_raw))+struct.pack('<Q',len(comp))+comp
def link_children(d):
    """Correct KOEI inner LINK: count@4, toc_off@8, TOC=(off,size) pairs."""
    if d[:4]!=b'LINK' or len(d)<20: return None
    cnt=struct.unpack_from('<I',d,4)[0]; toc=struct.unpack_from('<I',d,8)[0]
    if cnt>500000 or toc+cnt*8>len(d): return None
    return [struct.unpack_from('<II',d,toc+i*8) for i in range(cnt)]
def outer_entries(res):
    cnt=struct.unpack_from('<I',res,4)[0]
    return [struct.unpack_from('<II',res,16+i*8) for i in range(cnt)]

def entry_gt1g(res, idx):
    """Return (entry_bytes, coff, orig_child, gt1g) for a single-child texture entry."""
    outer=outer_entries(res); o,s=outer[idx]; e=res[o:o+s]
    coff,csize=struct.unpack_from('<II',e,0x20)
    child=e[coff:coff+csize]; g=kt_decompress(child)
    return e, coff, child, g

# ---------------- G1T texture decode ----------------
def g1t_textures(g):
    """Return list of dicts: {tid,fmt,w,h,data_off,data_len,rgba}."""
    tbl=struct.unpack_from('<I',g,0x0C)[0]; ntex=struct.unpack_from('<I',g,0x10)[0]
    offs=struct.unpack_from(f'<{ntex}I',g,tbl); out=[]
    for k,o in enumerate(offs):
        p=tbl+o; fmt,dxdy=g[p+1],g[p+2]; w=1<<(dxdy&0xF); h=1<<(dxdy>>4)
        ex=struct.unpack_from('<I',g,p+8)[0]; end=tbl+offs[k+1] if k+1<ntex else len(g)
        doff=p+8+ex; data=g[doff:end]; rgba=None
        try:
            if fmt==0x59: rgba=_bc(data,(w//4)*(h//4)*8,w,h,'bc1')
            elif fmt==0x5B: rgba=_bc(data,(w//4)*(h//4)*16,w,h,'bc3')
            elif fmt==0x5C: rgba=_bc(data,(w//4)*(h//4)*8,w,h,'bc4')
            elif fmt==0x5F: rgba=_bc(data,(w//4)*(h//4)*16,w,h,'bc7')
            elif fmt==0x01:
                a=np.frombuffer(data[:w*h*4],np.uint8).reshape(h,w,4)[:,:,[2,1,0,3]]; rgba=a.copy()
        except Exception: rgba=None
        out.append(dict(tid=k,fmt=fmt,w=w,h=h,data_off=doff,data_len=end-doff,rgba=rgba))
    return out
def _bc(data,n,w,h,kind):
    b=bytes(data[:n])
    if kind=='bc1': dec=texture2ddecoder.decode_bc1(b,w,h)
    elif kind=='bc3': dec=texture2ddecoder.decode_bc3(b,w,h)
    elif kind=='bc4': dec=texture2ddecoder.decode_bc4(b,w,h)
    elif kind=='bc7': dec=texture2ddecoder.decode_bc7(b,w,h)
    return np.frombuffer(dec,np.uint8).reshape(h,w,4)[:,:,[2,1,0,3]].copy()

# ---------------- KO fit-to-box render ----------------
def render_ko_fit(ko, box_w, box_h, S=4, text_rgb=(24,28,42), stroke_rgb=(243,243,246),
                  glow_rgb=(255,255,255), glow_a=235, glow_stroke=1.6, glow_blur=1.1,
                  fill=0.98, font_bytes=None, stroke_ratio=1.0):
    """Render KO scaled so its dark-ink bbox fits (box_w,box_h) px. Returns (layer, (ink_cx,ink_cy))."""
    fb=font_bytes if font_bytes is not None else FB
    fsz=44; f=ImageFont.truetype(io.BytesIO(fb),fsz*S); pad=12*S
    W=len(ko)*fsz*S+2*pad; H=fsz*S+2*pad
    sw=max(1,int(stroke_ratio*S))
    probe=Image.new('L',(W,H)); ImageDraw.Draw(probe).text((pad,pad),ko,font=f,fill=255,stroke_width=sw)
    ib=probe.getbbox()
    if ib is None: return None,None
    iw=ib[2]-ib[0]; ih=ib[3]-ib[1]
    fscale=min(box_w*S/iw, box_h*S/ih)*fill/S
    comp=Image.new('RGBA',(W,H),(0,0,0,0))
    if glow_a>0:
        gl=Image.new('RGBA',(W,H),(0,0,0,0))
        ImageDraw.Draw(gl).text((pad,pad),ko,font=f,fill=glow_rgb+(glow_a,),
                                stroke_width=int(glow_stroke*S),stroke_fill=glow_rgb+(glow_a,))
        gl=gl.filter(ImageFilter.GaussianBlur(int(glow_blur*S)))
        comp=Image.alpha_composite(comp,gl)
    ImageDraw.Draw(comp).text((pad,pad),ko,font=f,fill=text_rgb+(255,),
                              stroke_width=sw,stroke_fill=stroke_rgb+(255,))
    mrg=int(5*S); cl,ct,cr,cb=max(0,ib[0]-mrg),max(0,ib[1]-mrg),min(W,ib[2]+mrg),min(H,ib[3]+mrg)
    crop=comp.crop((cl,ct,cr,cb))
    nw=max(1,round(crop.width*fscale)); nh=max(1,round(crop.height*fscale))
    layer=crop.resize((nw,nh),Image.LANCZOS)
    icx=((ib[0]+ib[2])/2-cl)*fscale; icy=((ib[1]+ib[3])/2-ct)*fscale
    return layer,(icx,icy)

def erase_place(base, mask, bbox, ko, keep=None, inpaint_r=4, **style):
    """base: HxWx4 uint8 (modified in place). mask: uint8 dark-text mask (same HxW).
    bbox: (x0,y0,x1,y1) JP ink box. Inpaint mask, place KO fit-to-box centered on bbox."""
    x0,y0,x1,y1=bbox; H,W=base.shape[:2]
    rgb=base[:,:,:3].copy(); al=base[:,:,3].copy()
    m=cv2.dilate(mask,np.ones((5,5),np.uint8),iterations=2)
    if keep is not None: m[keep]=0
    inp=cv2.inpaint(rgb,m,inpaint_r,cv2.INPAINT_TELEA)
    img=Image.fromarray(np.dstack([inp,al]),'RGBA')
    layer,ink=render_ko_fit(ko,x1-x0+1,y1-y0+1,**style)
    if layer is not None:
        jcx=(x0+x1)/2; jcy=(y0+y1)/2
        img.alpha_composite(layer,(int(round(jcx-ink[0])),int(round(jcy-ink[1]))))
    out=np.array(img)
    if keep is not None: out[keep]=base[keep]
    base[:,:,:]=out

# ---------------- BC encode (changed blocks only) ----------------
import sys as _sys; _sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bc_encode import encode_bc3

def mixed_bc3(orig_bc3, orig_rgba, new_rgba):
    """Return BC3 bytes = original for unchanged 4x4 blocks, re-encoded for changed."""
    H,W=orig_rgba.shape[:2]; nbx,nby=W//4,H//4; nblk=nbx*nby
    changed=(orig_rgba.reshape(nby,4,nbx,4,4)!=new_rgba.reshape(nby,4,nbx,4,4)).any(axis=(1,3,4)).reshape(-1)
    new=np.frombuffer(encode_bc3(new_rgba),np.uint8).reshape(nblk,16).copy()
    orig=np.frombuffer(orig_bc3,np.uint8).reshape(nblk,16).copy()
    orig[changed]=new[changed]
    return orig.tobytes(), int(changed.sum())

# ---------------- repack ----------------
def rebuild_entry(res, idx, tex_replacements):
    """tex_replacements: {tid: new_rgba (HxWx4 uint8)}. Rebuild entry idx GT1G in place
    (mixed-BC3 for BC3 textures / raw BGRA8 for fmt 0x01), KT re-wrap, inner LINK 16-align."""
    e, coff, orig_child, g = entry_gt1g(res, idx)
    g=bytearray(g); texs=g1t_textures(bytes(g))
    for tid, new_rgba in tex_replacements.items():
        t=[x for x in texs if x['tid']==tid][0]
        assert (t['h'],t['w'])==new_rgba.shape[:2], f'e{idx} tex{tid} dims {new_rgba.shape[:2]}!={(t["h"],t["w"])}'
        if t['fmt']==0x5B:
            orig_bc3=bytes(g[t['data_off']:t['data_off']+t['data_len']])
            payload,_=mixed_bc3(orig_bc3, t['rgba'], new_rgba)
        elif t['fmt']==0x01:
            payload=new_rgba[:,:,[2,1,0,3]].tobytes()
        else:
            raise ValueError(f'repack fmt 0x{t["fmt"]:02X} unsupported')
        assert len(payload)==t['data_len']
        g[t['data_off']:t['data_off']+t['data_len']]=payload
    new_child=kt_wrap(orig_child, bytes(g))
    new_e=bytearray(e[:coff])+new_child
    struct.pack_into('<II', new_e, 0x20, coff, len(new_child))
    return bytes(new_e)

def rebuild_reslang(base_path, out_path, entry_replacements):
    """entry_replacements: {entry_idx: {tid: new_rgba}}. Rebuild whole res_lang."""
    res=open(base_path,'rb').read()
    outer=outer_entries(res)
    new_entries={i: rebuild_entry(res,i,tr) for i,tr in entry_replacements.items()}
    ents=[]
    for i,(off,size) in enumerate(outer):
        nxt=outer[i+1][0] if i+1<len(outer) else len(res)
        blob=new_entries[i] if i in new_entries else res[off:off+size]
        ents.append((blob, res[off+size:nxt]))
    out=bytearray(res[:outer[0][0]])
    for i,(blob,gap) in enumerate(ents):
        struct.pack_into('<II', out, 16+i*8, len(out), len(blob))
        out+=blob; out+=gap
    open(out_path,'wb').write(out)
    return len(res), len(out)
