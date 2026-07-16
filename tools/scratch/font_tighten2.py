# -*- coding: utf-8 -*-
"""Tighten hangul spacing — CORRECTED: the engine reads bitmap rows at pitch
ceil(byte0/2) bytes, so narrowing the advance REQUIRES repacking each bitmap's rows
to the new width. Evidence: v2.3 (metrics-only change) rendered shredded rows;
JP half-width glyphs pack 12B rows with byte0=24; sec2 packs ceil(w/2) rows.
Per glyph: shift ink left to x=2, advance=even(ink_right+3) clamp, crop to advance,
repack rows, byte0=byte4=advance, byte5=256-advance//2 (matches JP HW/FW pattern)."""
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

def tighten(g1n, cell, left_target, tracking, adv_min, space_adv):
    g=bytearray(g1n)
    pool=struct.unpack_from('<I',g,0x14)[0]
    sec_cnt=struct.unpack_from('<I',g,0x1C)[0]
    secs=list(struct.unpack_from(f'<{sec_cnt}I',g,0x20))
    src_pitch=cell//2; slot=src_pitch*cell
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
            if g[r]!=cell: continue           # only our full-cell hangul
            boff=struct.unpack_from('<I',g,r+8)[0]
            base=pool+boff
            raw=np.frombuffer(bytes(g[base:base+slot]),dtype=np.uint8).reshape(cell,src_pitch)
            px=np.empty((cell,cell),np.uint8)
            px[:,0::2]=raw>>4; px[:,1::2]=raw&0xF
            cols=np.where(px.any(axis=0))[0]
            if len(cols)==0: continue
            x0,x1=int(cols.min()),int(cols.max())
            shift=max(0,x0-left_target)
            if shift:
                px=np.roll(px,-shift,axis=1); px[:,-shift:]=0
                x1-=shift
            adv=x1+1+tracking
            adv=min(cell, max(adv_min, adv+(adv&1)))   # round UP to even, clamp
            # crop to adv columns, repack rows at adv/2 bytes
            crop=px[:,:adv]
            packed=((crop[:,0::2]<<4)|crop[:,1::2]).astype(np.uint8)  # even px = HIGH nibble
            pb=packed.tobytes()
            g[base:base+slot]=b'\x00'*slot            # clear slot
            g[base:base+len(pb)]=pb                   # front-packed at new pitch
            g[r]=adv; g[r+4]=adv; g[r+5]=256-adv//2
            stats.append(adv)
        # space: even advance + matching byte5; bitmap slot is all zeros already
        sp=int(cm[0x20])
        if sp:
            r=rec+sp*12
            g[r]=space_adv; g[r+4]=space_adv; g[r+5]=256-space_adv//2
    a=np.array(stats)
    print(f'  cell{cell}: {len(stats)} glyphs repacked, adv p50={np.percentile(a,50):.0f} '
          f'min={a.min()} max={a.max()}; space->{space_adv}')
    return bytes(g)

res=open(SRC,'rb').read()
cnt=struct.unpack_from('<I',res,4)[0]
outer=[struct.unpack_from('<II',res,16+i*8) for i in range(cnt)]
new_entries={}
for idx,cell,lt,tr,amin,sadv in ((6,48,2,2,26,16),(7,24,1,1,14,8)):
    o,s=outer[idx]; child=res[o:o+s]
    g1n=kt_dec(child); assert g1n[:4]==b'_N1G'
    print(f'entry {idx} ({cell}px):')
    g2=tighten(g1n,cell,lt,tr,amin,sadv)
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
