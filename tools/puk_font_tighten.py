# -*- coding: utf-8 -*-
"""Tighten PK font (res_lang_pk.bin entries 16/17) Hangul advance (byte4 only), matching
font_tighten3.py's algorithm exactly. In-place at the ORIGINAL offset/slot (same pattern
as g1n_inplace_korean.py): only the TOC size field for entries 16/17 changes (to the new,
smaller compressed size); every other entry's offset+size is byte-identical to before.
Decompressed size is asserted unchanged -> preserves the crash-safety invariant."""
import sys, struct, os
import numpy as np, lz4.block
sys.stdout.reconfigure(encoding='utf-8')

SRC = os.environ.get('PK_RES_OUT') or r'D:\nsw\rom\nobu16_powerupkit\puk_mod\atmosphere\contents\01007ab012872001\romfs\RES_JP_PK\res_lang_pk.bin'
OUT=SRC  # in place -- run this AFTER g1n_inplace_korean.py has produced this file

def kt_dec(b):
    dec=struct.unpack_from('<Q',b,8)[0]; comp=struct.unpack_from('<Q',b,16)[0]
    return lz4.block.decompress(b[24:24+comp],uncompressed_size=dec)
def kt_wrap(orig,new):
    comp=lz4.block.compress(new,mode='high_compression',compression=12,store_size=False)
    return orig[:8]+struct.pack('<Q',len(new))+struct.pack('<Q',len(comp))+comp
def toc(res):
    c=struct.unpack_from('<I',res,4)[0]; return [struct.unpack_from('<II',res,16+i*8) for i in range(c)]

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
            if g[r]!=cell: continue
            boff=struct.unpack_from('<I',g,r+8)[0]
            base=pool+boff
            raw=np.frombuffer(bytes(g[base:base+slot]),dtype=np.uint8).reshape(cell,pitch)
            px=np.empty((cell,cell),np.uint8)
            px[:,0::2]=raw>>4; px[:,1::2]=raw&0xF
            cols=np.where(px.any(axis=0))[0]
            if len(cols)==0: continue
            ink_w=int(cols.max())-int(cols.min())+1
            adv=ink_w+pad
            adv=min(cell,max(adv_min,adv+(adv&1)))
            g[r+4]=adv
            stats.append(adv)
        sp=int(cm[0x20])
        if sp: g[rec+sp*12+4]=space_adv
    a=np.array(stats) if stats else np.array([0])
    print(f'  cell{cell}: {len(stats)} advances set, p50={np.percentile(a,50):.0f} '
          f'min={a.min()} max={a.max()}; space adv->{space_adv}')
    return bytes(g)

res=open(SRC,'rb').read()
tc=toc(res)
out=bytearray(res)
for idx,cell,pad,amin,sadv in ((16,48,4,26,16),(17,24,2,14,8)):
    off,orig_size=tc[idx]
    # physical slot = space up to the NEXT entry's fixed offset, not the current (already-
    # shrunk, from the earlier Korean-injection pass) toc-declared size -- there's slack.
    next_off = tc[idx+1][0]
    slot = next_off - off
    child=res[off:off+orig_size]
    g1n=kt_dec(child); assert g1n[:8]==b'_N1G0000'
    orig_dec_size=len(g1n)
    print(f'entry {idx} ({cell}px), offset={off} toc_size={orig_size} physical_slot={slot}:')
    g2=tighten(g1n,cell,pad,amin,sadv)
    assert len(g2)==orig_dec_size, 'decompressed size changed! unsafe for 872001 fixed buffer'
    ne=kt_wrap(child,g2)
    assert len(ne)<=slot, f'entry{idx} re-tightened blob grew beyond physical slot ({len(ne)} > {slot})'
    out[off:off+slot]=ne+b'\x00'*(slot-len(ne))
    struct.pack_into('<II',out,16+idx*8,off,len(ne))   # only this entry's size field changes
    print(f'  compressed {orig_size} -> {len(ne)}  (physical slot {slot}, offsets of all other entries untouched)')

assert len(out)==len(res), 'overall file size changed!'
open(OUT,'wb').write(bytes(out))

# verify
v=open(OUT,'rb').read(); vt=toc(v)
assert all(vt[i][0]==tc[i][0] for i in range(len(tc))), 'an offset moved!'
assert all(v[tc[i][0]:tc[i][0]+tc[i][1]]==res[tc[i][0]:tc[i][0]+tc[i][1]] for i in range(len(tc)) if i not in (16,17)), 'unrelated entry bytes changed!'
EXPECT_DEC = {16: 17217348, 17: 6395540}
for idx in (16,17):
    off,sz=vt[idx]; g=kt_dec(v[off:off+sz])
    assert len(g)==EXPECT_DEC[idx], f'entry{idx} decompressed size drifted: {len(g)}'
    print(f'  entry{idx} decompressed size confirmed unchanged: {len(g)}')
print('VERIFY OK: file size unchanged, all non-16/17 entries byte-identical, offsets untouched.')
