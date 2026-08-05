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
# ⚠️ 반드시 **패치 대상 게임 버전**의 원본 텍스트를 넣을 것. 옛 버전 기준으로 만들면
# 새 버전에서 추가된 문자(예: 1.1.7의 Joy-Con 2 버튼 아이콘 μ ν ξ ο, PlayStation®의 ®,
# 새 크레딧 한자)가 쓰던 글리프를 한글로 재활용해 화면에서 깨진다.
PK=os.environ.get('PK_MSG_SRC') or r'D:\nsw\rom\1.1.7\extract\Program 1\romfs\MSG_PK\JP'
BM=os.environ.get('BASE_MSG_SRC') or r'D:\nsw\rom\1.1.7\extract\Program 0\romfs\MSG\JP'
# 파일 목록을 고정하지 않고 폴더 전체를 훑는다(새 버전에서 파일이 추가돼도 누락 없음)
for f in sorted(os.listdir(PK)):
    if not f.endswith('.bin') or f=='msggame.bin': continue
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
main=open(os.environ.get('MAIN_872001') or r'D:\nsw\rom\1.1.7\extract\Program 1\exefs\main','rb').read()
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
# 안전망: 텍스트 스캔에서 놓쳐도 절대 재활용하면 안 되는 구간
#  0x2000-0x206F 일반 문장부호(‘ ’ “ ” … 등), 0x2100-0x214F 문자꼴 기호(® ™ 등),
#  0x2190-0x21FF 화살표, 0x2500-0x257F 괘선(®가 ┐로 보이는 등 특수 매핑),
#  0x0370-0x03FF 그리스 문자 = 게임의 버튼 아이콘 글리프(μ ν ξ ο …)
for a,b in ((0x2000,0x2070),(0x2100,0x2150),(0x2190,0x2200),(0x2500,0x2580),(0x00A0,0x0100),(0x0370,0x0400)):
    for cp in range(a,b): used.add(cp)
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
OUT=os.environ.get('PK_MSG_OUT') or r'D:\nsw\rom\nobu16_powerupkit\puk_mod_117\atmosphere\contents\01007ab012872001\romfs\MSG_PK\JP'
DLCOUT=os.environ.get('DLC_PK_OUT') or r'D:\nsw\rom\nobu16_powerupkit\puk_mod_117\atmosphere\contents\01007ab012872001\romfs\DLC_PK\JP'
kor=set()
for f in sorted(os.listdir(OUT)):
    if not f.endswith('.bin') or f=='msggame.bin': continue
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
# PK_RES_SRC : 폰트를 꺼낼 **원본(무손상)** res_lang_pk
# PK_RES_BASE: 결과를 얹을 바탕 파일(기본=원본). 이미 이미지가 한글화된 파일을 주면
#              폰트 엔트리(16·17)만 교체하므로 이미지 작업이 보존된다.
PKRES=os.environ.get('PK_RES_SRC') or r'D:\nsw\rom\1.1.7\extract\Program 1\romfs\RES_JP_PK\res_lang_pk.bin'
BASERES=os.environ.get('PK_RES_BASE') or PKRES
OUTRES=os.environ.get('PK_RES_OUT') or r'D:\nsw\rom\nobu16_powerupkit\puk_mod_117\atmosphere\contents\01007ab012872001\romfs\RES_JP_PK\res_lang_pk.bin'
pk=open(PKRES,'rb').read(); pt=toc(pk)
base=open(BASERES,'rb').read(); bt=toc(base)
assert len(bt)==len(pt), '바탕 파일의 엔트리 수가 원본과 다릅니다'
out=bytearray(base)
# 바탕 파일에서 각 엔트리가 실제로 쓸 수 있는 공간(다음 엔트리 시작까지)
_starts=sorted(o for o,_ in bt)
def slot_cap(off):
    nxt=[s for s in _starts if s>off]
    return (min(nxt) if nxt else len(base))-off
for idx in (16,17):
    off,orig_size=pt[idx]                      # 원본(무손상) 폰트를 꺼내 한글 주입
    font=kt_dec(pk[off:off+orig_size]); assert font[:8]==b'_N1G0000'
    print('entry%d:'%idx)
    newfont,added=inject(font,korean_cps)
    assert len(newfont)==len(font)   # 압축 해제 크기 불변 => 872001 폰트 버퍼에 맞음
    boff,bsize=bt[idx]                          # 바탕 파일의 슬롯에 기록
    ne=kt_wrap(base[boff:boff+8],newfont)
    cap=slot_cap(boff)
    assert len(ne)<=cap, f'entry{idx}: 새 폰트 {len(ne)}B > 슬롯 {cap}B'
    out[boff:boff+cap]=ne+b'\x00'*(cap-len(ne))
    struct.pack_into('<II',out,16+idx*8,boff,len(ne))
    print('   decompressed %d (unchanged), compressed %d / slot %d'%(len(newfont),len(ne),cap))
open(OUTRES,'wb').write(out)
print('\nwrote', OUTRES, 'size', len(out), '(unchanged:', len(out)==len(pk), ')')
# verify
v=open(OUTRES,'rb').read();vt=toc(v)
for idx in (16,17):
    off,sz=vt[idx]; g=kt_dec(v[off:off+sz]); assert len(g)==17217348 if idx==16 else True
    cm=np.frombuffer(g,dtype='<u2',count=0x10000,offset=struct.unpack_from('<3I',g,0x20)[0])
    print('  entry%d decompressed=%d hangul=%d'%(idx,len(g),sum(1 for c in range(0xAC00,0xD7A4) if cm[c])))
