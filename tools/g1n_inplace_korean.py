# -*- coding: utf-8 -*-
"""Inject Korean into a G1N font WITHOUT growing it: overwrite UNUSED full-width JP glyph
bitmaps in-place with Korean glyphs (same cell size), remap charmap. Font byte-size stays
identical -> fits 872001's fixed font buffer. Then rebuild res_lang_pk (v3-style)."""
import struct, os, sys
import numpy as np, lz4.block
sys.stdout.reconfigure(encoding='utf-8')
import g1n_extend as GE   # reuse render_cell, load_font, FONT_REG/BOLD
import apply_translations as A

def kt_dec(b):
    dec=struct.unpack_from('<Q',b,8)[0]; comp=struct.unpack_from('<Q',b,16)[0]
    return lz4.block.decompress(b[24:24+comp],uncompressed_size=dec)
def kt_wrap(orig8,new_raw):
    comp=lz4.block.compress(new_raw,mode='high_compression',compression=12,store_size=False)
    return orig8[:8]+struct.pack('<Q',len(new_raw))+struct.pack('<Q',len(comp))+comp
def toc(res):
    c=struct.unpack_from('<I',res,4)[0]; return [struct.unpack_from('<II',res,16+i*8) for i in range(c)]

# ---------- gather used JP codepoints + needed Korean ----------
def strtable_cps(dec,out):
    for sec in A.read_strtable_raw(dec):
        for s in sec:
            for c in s: out.add(ord(c))
def msggame_cps(dec,out):
    B=bytes(dec); i=0
    while True:
        st=B.find(b'\x07\x07\x01',i)
        if st<0: break
        en=B.find(b'\x07\x07\x02',st+3)
        if en<0: break
        raw=B[st+3:en]
        if len(raw)%2==0:
            for c in raw.decode('utf-16-le',errors='replace'): out.add(ord(c))
        i=en+3

used=set()
PK=r'D:\nsw\rom\1.1.5\Program 1\romfs\MSG_PK\JP'
BM=r'D:\nsw\rom\1.1.5\Program 0\romfs\MSG\JP'
for f in ['msgdata.bin','msgev.bin','msgui.bin','msgbre.bin','msgire.bin','msgstf.bin']:
    strtable_cps(kt_dec(open(os.path.join(PK,f),'rb').read()),used)
msggame_cps(kt_dec(open(os.path.join(PK,'msggame.bin'),'rb').read()),used)
for f in ['strdata.bin','ev_strdata.bin']: strtable_cps(kt_dec(open(os.path.join(BM,f),'rb').read()),used)
msggame_cps(kt_dec(open(os.path.join(BM,'msggame.bin'),'rb').read()),used)
# DLC_PK .n16 string tables (original JP, pristine source) -- keep all their glyphs,
# since some fields (kana reading/search keys) are intentionally left untranslated.
DLCSRC=os.environ.get('DLC_PK_SRC') or r'D:\nsw\rom\1.1.5\Program 1\romfs\DLC_PK\JP'
if os.path.isdir(DLCSRC):
    import glob as _glob2
    from n16_reader import n16_unwrap as _n16_unwrap2, read_section_strings as _n16_strs2
    for f in _glob2.glob(os.path.join(DLCSRC,'*.n16')):
        dd=open(f,'rb').read()
        _,dec,_=_n16_unwrap2(dd)
        if len(dec)>=4 and struct.unpack_from('<I',dec,0)[0]==0x134C58:
            for s in _n16_strs2(dec,0,len(dec)):
                for c in s: used.add(ord(c))
# main null-terminated UTF-16 strings
main=open(r'D:\nsw\rom\1.1.5\Program 1\exefs\main','rb').read()
def is_text(v): return v==0x20 or 0x30<=v<=0x7e or 0x3000<=v<=0x9fff or 0xf900<=v<=0xfaff or 0xff00<=v<=0xffef or 0xac00<=v<=0xd7a3
i=0;n=len(main)-1
while i<n-1:
    v=main[i]|(main[i+1]<<8)
    if is_text(v):
        run=[];j=i
        while j<n-1:
            w=main[j]|(main[j+1]<<8)
            if w==0: break
            if not is_text(w): run=[];break
            run.append(w);j+=2
        if len(run)>=3 and (main[j]|(main[j+1]<<8))==0:
            for w in run:
                if w>0x2000: used.add(w)
        i=j+2
    else: i+=2
# also always-keep: kana, ascii, common punctuation/symbols
for cp in list(range(0x3000,0x30FF))+list(range(0x20,0x7f))+list(range(0xFF00,0xFFF0)): used.add(cp)
print('used JP codepoints (keep):', len(used))

# ---------- in-place Korean injection ----------
def inject(g1n, korean_cps):
    g=bytearray(g1n)
    first_sec=struct.unpack_from('<I',g,0x0C)[0]
    pool_off=struct.unpack_from('<I',g,0x14)[0]
    nsec=struct.unpack_from('<I',g,0x1C)[0]
    sec_offs=[struct.unpack_from('<I',g,0x20+4*i)[0] for i in range(nsec)]
    bounds=sec_offs+[pool_off]
    styles={0:(GE.FONT_REG,39/48,24.5/48),1:(GE.FONT_BOLD,41/48,24.5/48)}
    total_added=0; total_short=0
    for si in range(nsec):
        if si not in styles: continue
        s,e=sec_offs[si],bounds[si+1]
        cm=np.frombuffer(g,dtype='<u2',count=0x10000,offset=s).copy()
        rec_off=s+0x20000; n_rec=(e-rec_off)//12
        # ref full-width metrics from 一
        ref_gid=int(cm[ord('一')]); rm=g[rec_off+ref_gid*12:rec_off+ref_gid*12+8]
        w,h=rm[0],rm[1]; bmp_sz=w*h//2
        # gid -> codepoint (first mapping)
        gid2cp={}
        for cp in np.nonzero(cm)[0]:
            gid2cp.setdefault(int(cm[cp]),int(cp))
        # unused full-width gids (metrics == ref, cp not used)
        unused=[]
        for gid in range(1,n_rec):
            mo=rec_off+gid*12
            if g[mo]==w and g[mo+1]==h:
                cp=gid2cp.get(gid)
                if cp is not None and cp not in used:
                    unused.append((gid,cp))
        font_path,ink,cy=styles[si]
        added=0
        need=[cp for cp in korean_cps if cm[cp]==0]
        for k,cp in enumerate(need):
            if k>=len(unused):
                total_short+=1; continue
            gid,oldcp=unused[k]
            cell=GE.render_cell(chr(cp),font_path,w,h,round(h*ink),cy)
            bmp_rel=struct.unpack_from('<I',g,rec_off+gid*12+8)[0]
            assert len(cell)==bmp_sz
            g[pool_off+bmp_rel:pool_off+bmp_rel+bmp_sz]=cell   # overwrite bitmap in place
            cm[cp]=gid; cm[oldcp]=0
            added+=1
        # write charmap back
        g[s:s+0x20000]=cm.tobytes()
        print('  sec%d: cell %dx%d  unused-fullwidth=%d  Korean added=%d  short=%d'%(si,w,h,len(unused),added,len(need)-added))
        total_added+=added
    assert len(g)==len(g1n), 'size changed!'
    return bytes(g), total_added

# ---------- Korean codepoints needed (from MSG_PK + DLC_PK translations) ----------
OUT=r'D:\nsw\rom\nobu16_powerupkit\puk_mod\atmosphere\contents\01007ab012872001\romfs\MSG_PK\JP'
DLCOUT=os.environ.get('DLC_PK_OUT') or r'D:\nsw\rom\nobu16_powerupkit\puk_mod\atmosphere\contents\01007ab012872001\romfs\DLC_PK\JP'
kor=set()
for f in ['msgdata.bin','msgev.bin','msgui.bin','msgbre.bin','msgire.bin']:
    strtable_cps(kt_dec(open(os.path.join(OUT,f),'rb').read()),kor)
msggame_cps(kt_dec(open(os.path.join(OUT,'msggame.bin'),'rb').read()),kor)
if os.path.isdir(DLCOUT):
    import glob as _glob
    from n16_reader import n16_unwrap as _n16_unwrap, read_section_strings as _n16_strs
    for f in _glob.glob(os.path.join(DLCOUT,'*.n16')):
        dd=open(f,'rb').read()
        _,dec,_=_n16_unwrap(dd)
        if len(dec)>=4 and struct.unpack_from('<I',dec,0)[0]==0x134C58:
            for s in _n16_strs(dec,0,len(dec)):
                for c in s: kor.add(ord(c))
korean_cps=sorted(c for c in kor if 0xAC00<=c<=0xD7A3)
print('Korean needed:', len(korean_cps))

# ---------- build res_lang_pk (fonts injected in-place, v3-style repack) ----------
PKRES=r'D:\nsw\rom\1.1.5\Program 1\romfs\RES_JP_PK\res_lang_pk.bin'
OUTRES=r'D:\nsw\rom\nobu16_powerupkit\puk_mod\atmosphere\contents\01007ab012872001\romfs\RES_JP_PK\res_lang_pk.bin'
pk=open(PKRES,'rb').read(); pt=toc(pk)
out=bytearray(pk)
for idx in (16,17):
    off,orig_size=pt[idx]
    font=kt_dec(pk[off:off+orig_size]); assert font[:8]==b'_N1G0000'
    print('entry%d:'%idx)
    newfont,added=inject(font,korean_cps)
    assert len(newfont)==len(font)   # SAME decompressed size => fits buffer
    ne=kt_wrap(pk[off:off+8],newfont)
    assert len(ne)<=orig_size
    out[off:off+orig_size]=ne+b'\x00'*(orig_size-len(ne))
    struct.pack_into('<II',out,16+idx*8,off,len(ne))
    print('   decompressed size %d (unchanged), compressed %d/%d'%(len(newfont),len(ne),orig_size))
open(OUTRES,'wb').write(out)
print('\nwrote', OUTRES, 'size', len(out), '(unchanged:', len(out)==len(pk), ')')
# verify
v=open(OUTRES,'rb').read();vt=toc(v)
for idx in (16,17):
    off,sz=vt[idx]; g=kt_dec(v[off:off+sz]); assert len(g)==17217348 if idx==16 else True
    cm=np.frombuffer(g,dtype='<u2',count=0x10000,offset=struct.unpack_from('<3I',g,0x20)[0])
    print('  entry%d decompressed=%d hangul=%d'%(idx,len(g),sum(1 for c in range(0xAC00,0xD7A4) if cm[c])))
