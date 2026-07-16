# -*- coding: utf-8 -*-
"""Tighten Hangul spacing in G1N fonts (res_lang entries 6/7):
- shift each hangul bitmap left so ink starts at x=2 (main 48px) / x=1 (sub 24px)
- set advance (metric byte0 & byte4) = ink_width + tracking, clamped
- reduce ASCII space advance
Bitmaps stay in their slots (same size); only pool bytes + metric bytes change.
Rebuilds res_lang in place on top of the shipped (fully-patched) file."""
import sys, struct, os
import numpy as np, lz4.block
sys.stdout.reconfigure(encoding='utf-8')
SP=os.path.dirname(os.path.abspath(__file__))

SRC=r'C:\Users\Jay\AppData\Roaming\Ryujinx\mods\contents\01007ab012872000\romfs\RES_JP\res_lang.bin'
OUT=r'D:\nsw\rom\노부나가의 야망 신생_일본판\한글패치_테스트\romfs\RES_JP\res_lang.bin'

def kt_dec(b):
    dec=struct.unpack_from('<Q',b,8)[0]; comp=struct.unpack_from('<Q',b,16)[0]
    return lz4.block.decompress(b[24:24+comp],uncompressed_size=dec)
def kt_wrap(orig,new):
    comp=lz4.block.compress(new,mode='high_compression',compression=12,store_size=False)
    return orig[:8]+struct.pack('<Q',len(new))+struct.pack('<Q',len(comp))+comp

HANGUL=set(range(0xAC00,0xD7A4))|set(range(0x3130,0x3190))

def tighten(g1n, cell, left_target, tracking, adv_min, adv_max, space_adv):
    g=bytearray(g1n)
    pool=struct.unpack_from('<I',g,0x14)[0]
    sec_cnt=struct.unpack_from('<I',g,0x1C)[0]
    secs=list(struct.unpack_from(f'<{sec_cnt}I',g,0x20))
    bpr=cell//2  # bytes per row
    n_pix=bpr*cell
    stats=[]
    for si in (0,1):
        if si>=sec_cnt: continue
        so=secs[si]
        cm=np.frombuffer(bytes(g[so:so+0x20000]),dtype='<u2')
        rec=so+0x20000
        done=set()
        for cp in HANGUL:
            gid=int(cm[cp]) if cp<65536 else 0
            if gid==0 or gid in done: continue
            done.add(gid)
            r=rec+gid*12
            if g[r]!=cell: continue          # only full-cell glyphs (ours)
            boff=struct.unpack_from('<I',g,r+8)[0]
            base=pool+boff
            raw=np.frombuffer(bytes(g[base:base+n_pix]),dtype=np.uint8).reshape(cell,bpr)
            px=np.empty((cell,cell),np.uint8)
            px[:,0::2]=raw>>4; px[:,1::2]=raw&0xF
            cols=np.where(px.any(axis=0))[0]
            if len(cols)==0: continue
            x0,x1=int(cols.min()),int(cols.max())
            shift=x0-left_target
            if shift>0:
                px=np.roll(px,-shift,axis=1); px[:,-shift:]=0
                x1-=shift
            new_adv=max(adv_min,min(adv_max,x1+1+tracking))
            # re-encode 4bpp (even pixel = HIGH nibble)
            out=((px[:,0::2]<<4)|px[:,1::2]).astype(np.uint8)
            g[base:base+n_pix]=out.tobytes()
            g[r]=new_adv; g[r+4]=new_adv
            stats.append(new_adv)
        # space
        sp=int(cm[0x20])
        if sp:
            r=rec+sp*12
            g[r]=space_adv; g[r+4]=space_adv
    a=np.array(stats)
    print(f'  cell{cell}: {len(stats)} glyph-records tightened, adv p50={np.percentile(a,50):.0f} '
          f'min={a.min()} max={a.max()}; space->{space_adv}')
    return bytes(g)

res=open(SRC,'rb').read()
cnt=struct.unpack_from('<I',res,4)[0]
outer=[struct.unpack_from('<II',res,16+i*8) for i in range(cnt)]
new_entries={}
for idx,cell,lt,tr,amin,amax,sadv in ((6,48,2,2,26,48,15),(7,24,1,1,13,24,8)):
    o,s=outer[idx]; child=res[o:o+s]
    g1n=kt_dec(child)
    assert g1n[:4]==b'_N1G'
    print(f'entry {idx} ({cell}px):')
    g2=tighten(g1n,cell,lt,tr,amin,amax,sadv)
    new_entries[idx]=kt_wrap(child,g2)
    # verify roundtrip
    assert kt_dec(new_entries[idx])==g2
# outer reassemble
ents=[]
for i,(off,size) in enumerate(outer):
    nxt=outer[i+1][0] if i+1<len(outer) else len(res)
    blob=new_entries.get(i, res[off:off+size])
    ents.append((blob,res[off+size:nxt]))
out=bytearray(res[:outer[0][0]])
for i,(blob,gap) in enumerate(ents):
    struct.pack_into('<II',out,16+i*8,len(out),len(blob))
    out+=blob; out+=gap
open(OUT,'wb').write(out)
print(f'res_lang: {len(res):,} -> {len(out):,} bytes -> {OUT}')
