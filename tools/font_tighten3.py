# -*- coding: utf-8 -*-
"""Tighten hangul spacing v3 — satisfy BOTH render paths:
- Path A (dialogue): draws glyph quad 1:1 (width=byte0) and advances pen by byte4.
- Path B (some windows): draws glyph into a FIXED cell (48px), stretching the byte0-wide
  texture — so byte0/bitmap must stay 48 to avoid horizontal stretching.
Therefore: bitmaps and byte0/byte5 stay EXACTLY as v2.2 (centered ink, 48-wide, no
stretch anywhere, no pitch issues); ONLY byte4 (advance) is reduced.
Centering math: with ink span [L,R], gap between consecutive hangul inks =
(adv-1-R)+L2 = (ink_w+4-1-(L+ink_w-1))+L2 = 4-L+L2 ~= 4px, independent of centering.
"""
import sys, struct, os
import numpy as np, lz4.block
sys.stdout.reconfigure(encoding='utf-8')

SRC=os.path.join(os.path.dirname(os.path.abspath(__file__)),'reslang_v22.bin')  # pristine v2.2
OUT=r'D:\nsw\rom\노부나가의 야망 신생_일본판\한글패치_테스트\romfs\RES_JP\res_lang.bin'

def kt_dec(b):
    dec=struct.unpack_from('<Q',b,8)[0]; comp=struct.unpack_from('<Q',b,16)[0]
    return lz4.block.decompress(b[24:24+comp],uncompressed_size=dec)
def kt_wrap(orig,new):
    comp=lz4.block.compress(new,mode='high_compression',compression=12,store_size=False)
    return orig[:8]+struct.pack('<Q',len(new))+struct.pack('<Q',len(comp))+comp

HANGUL=set(range(0xAC00,0xD7A4))|set(range(0x3130,0x3190))

def tighten(g1n, cell, pad, adv_min, space_adv):
    g=bytearray(g1n)
    pool=struct.unpack_from('<I',g,0x14)[0]
    sec_cnt=struct.unpack_from('<I',g,0x1C)[0]
    secs=list(struct.unpack_from(f'<{sec_cnt}I',g,0x20))
    pitch=cell//2; slot=pitch*cell
    stats=[]
    for si in (0,1):
        if si>=sec_cnt: continue
        so=secs[si]
        cm=np.frombuffer(bytes(g[so:so+0x20000]),dtype='<u2')
        rec=so+0x20000
        done=set()
        for cp in sorted(HANGUL):
            if cp>=65536: continue
            gid=int(cm[cp])
            if gid==0 or gid in done: continue
            done.add(gid)
            r=rec+gid*12
            if g[r]!=cell: continue        # only our full-cell hangul glyphs
            boff=struct.unpack_from('<I',g,r+8)[0]
            base=pool+boff
            raw=np.frombuffer(bytes(g[base:base+slot]),dtype=np.uint8).reshape(cell,pitch)
            px=np.empty((cell,cell),np.uint8)
            px[:,0::2]=raw>>4; px[:,1::2]=raw&0xF
            cols=np.where(px.any(axis=0))[0]
            if len(cols)==0: continue
            ink_w=int(cols.max())-int(cols.min())+1
            adv=ink_w+pad
            adv=min(cell,max(adv_min,adv+(adv&1)))   # even, clamped
            g[r+4]=adv                                # ONLY the advance byte
            stats.append(adv)
        sp=int(cm[0x20])
        if sp: g[rec+sp*12+4]=space_adv               # space advance only
    a=np.array(stats)
    print(f'  cell{cell}: {len(stats)} advances set, p50={np.percentile(a,50):.0f} '
          f'min={a.min()} max={a.max()}; space adv->{space_adv} (byte0/bitmap untouched)')
    return bytes(g)

res=open(SRC,'rb').read()
cnt=struct.unpack_from('<I',res,4)[0]
outer=[struct.unpack_from('<II',res,16+i*8) for i in range(cnt)]
new_entries={}
for idx,cell,pad,amin,sadv in ((6,48,4,26,16),(7,24,2,14,8)):
    o,s=outer[idx]; child=res[o:o+s]
    g1n=kt_dec(child); assert g1n[:4]==b'_N1G'
    print(f'entry {idx} ({cell}px):')
    g2=tighten(g1n,cell,pad,amin,sadv)
    new_entries[idx]=kt_wrap(child,g2)
    assert kt_dec(new_entries[idx])==g2
ents=[]
for i,(off,size) in enumerate(outer):
    nxt=outer[i+1][0] if i+1<len(outer) else len(res)
    blob=new_entries.get(i,res[off:off+size])
    ents.append((blob,res[off+size:nxt]))
out=bytearray(res[:outer[0][0]])
for i,(blob,gap) in enumerate(ents):
    struct.pack_into('<II',out,16+i*8,len(out),len(blob))
    out+=blob; out+=gap
open(OUT,'wb').write(out)
print(f'res_lang: {len(res):,} -> {len(out):,} -> {OUT}')
