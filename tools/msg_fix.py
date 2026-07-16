# -*- coding: utf-8 -*-
"""Fix dialogue overflow in MSG files (all transformations are UTF-16 length-preserving):
1) Normalize full-width forms -> ASCII (FF01-FF5E -> -0xFEE0), U+3000 -> space,
   U+00B7 -> U+30FB (missing glyph), U+2014 -> U+30FC.
2) ev_strdata: strings whose \\n-segments exceed the dialogue box width (calibrated from
   JP originals = 1056 units) get their manual \\n replaced by spaces so the ENGINE
   re-wraps them greedily (minimal display lines).
In-place edits on decompressed blobs, re-KT-wrapped; containers untouched."""
import sys, struct, os, re
import numpy as np, lz4.block
sys.stdout.reconfigure(encoding='utf-8')

MOD=r'C:\Users\Jay\AppData\Roaming\Ryujinx\mods\contents\01007ab012872000\romfs\MSG\JP'
OUTD=r'D:\nsw\rom\노부나가의 야망 신생_일본판\한글패치_테스트\romfs\MSG\JP'
NEWFONT=r'D:\nsw\rom\노부나가의 야망 신생_일본판\한글패치_테스트\romfs\RES_JP\res_lang.bin'

def kt_dec(b):
    dec=struct.unpack_from('<Q',b,8)[0]; comp=struct.unpack_from('<Q',b,16)[0]
    return lz4.block.decompress(b[24:24+comp],uncompressed_size=dec)
def kt_wrap(orig,new):
    comp=lz4.block.compress(new,mode='high_compression',compression=12,store_size=False)
    return orig[:8]+struct.pack('<Q',len(new))+struct.pack('<Q',len(comp))+comp

# ---- advance table from the TIGHTENED font ----
d=open(NEWFONT,'rb').read(); o,s=struct.unpack_from('<II',d,16+6*8); g=kt_dec(d[o:o+s])
secs=list(struct.unpack_from('<3I',g,0x20))
cm0=np.frombuffer(g,dtype='<u2',count=65536,offset=secs[0]); rec0=secs[0]+0x20000
ADV={}
for cp in range(0x10000):
    gid=int(cm0[cp])
    if gid: ADV[cp]=g[rec0+gid*12+4]
print('adv table:', len(ADV), 'glyphs | 가:',ADV.get(0xAC00),'space:',ADV.get(0x20))
assert cm0[0x30FC]!=0, 'ー missing'

# ---- normalization map (1:1 UTF-16 units) ----
NORM={}
for cp in range(0xFF01,0xFF5F): NORM[cp]=cp-0xFEE0
NORM[0x3000]=0x20
NORM[0x00B7]=0x30FB
NORM[0x2014]=0x30FC
W_STRIP=1000
PLACE=re.compile(r'\[[a-z]+\d+\]')

def norm_str(t):
    return ''.join(chr(NORM.get(ord(c),ord(c))) for c in t)
def seg_width(seg):
    w=0; i=0; n=len(seg)
    while i<n:
        c=seg[i]
        if c=='\x1b' and i+2<n and seg[i+1]=='C': i+=3; continue
        w+=ADV.get(ord(c),48); i+=1
    for m in PLACE.finditer(seg):
        lit=sum(ADV.get(ord(c),48) for c in m.group(0))
        w+=max(0, 390-lit)          # assume substituted name ~10 hangul
    return w

def iter_strings(blob):
    """yield (abs_off, char_len, text) for each string in an offset-table MSG container."""
    cnt=struct.unpack_from('<I',blob,0)[0]
    for i in range(cnt):
        off,size=struct.unpack_from('<II',blob,4+i*8)
        n=struct.unpack_from('<H',blob,off+8)[0]
        tbl=off+0x14
        offs=struct.unpack_from(f'<{n}I',blob,tbl)
        for j in range(n):
            so=tbl+offs[j]
            e=so
            while e<off+size-1 and blob[e:e+2]!=b'\x00\x00': e+=2
            yield so,(e-so)//2, blob[so:e].decode('utf-16-le',errors='replace')

def fix_table(path, strip_nl):
    raw=open(path,'rb').read(); blob=bytearray(kt_dec(raw))
    n_norm=0; n_strip=0; over=[]
    for so,clen,t in list(iter_strings(bytes(blob))):
        t2=norm_str(t)
        if strip_nl and '\n' in t2:
            segs=t2.split('\n')
            if any(seg_width(x)>W_STRIP for x in segs):
                t2=t2.replace('\n',' '); n_strip+=1
                tot=seg_width(t2)
                if tot>3*1056: over.append((tot,t2[:40]))
        if t2!=t:
            b=t2.encode('utf-16-le')
            assert len(b)==clen*2
            blob[so:so+len(b)]=b; n_norm+=1
    return bytes(raw), bytes(blob), n_norm, n_strip, over

def fix_msggame(path):
    raw=open(path,'rb').read(); blob=bytearray(kt_dec(raw))
    n=0; i=0
    B=bytes(blob)
    starts=[]
    while True:
        i=B.find(b'\x07\x07\x01',i)
        if i<0: break
        e=B.find(b'\x07\x07\x02',i+3)
        if e<0: break
        starts.append((i+3,e)); i=e+3
    for s,e in starts:
        if (e-s)%2: continue
        for k in range(s,e,2):
            u=blob[k]|(blob[k+1]<<8)
            v=NORM.get(u)
            if v is not None:
                blob[k]=v&0xFF; blob[k+1]=v>>8; n+=1
    return raw, bytes(blob), n, len(starts)

os.makedirs(OUTD,exist_ok=True)
# ev_strdata: normalize + strip overflow \n
raw,blob,nn,ns,over=fix_table(os.path.join(MOD,'ev_strdata.bin'),strip_nl=True)
open(os.path.join(OUTD,'ev_strdata.bin'),'wb').write(kt_wrap(raw,blob))
print(f'ev_strdata: {nn} strings modified, {ns} \\n-stripped, {len(over)} still >3 lines packed')
for w,t in over[:8]: print(f'   {w}u: {t}...')
# strdata: normalize only
raw,blob,nn,ns,_=fix_table(os.path.join(MOD,'strdata.bin'),strip_nl=False)
open(os.path.join(OUTD,'strdata.bin'),'wb').write(kt_wrap(raw,blob))
print(f'strdata: {nn} strings normalized')
# msggame: normalize inside text runs
raw,blob,n,nr=fix_msggame(os.path.join(MOD,'msggame.bin'))
open(os.path.join(OUTD,'msggame.bin'),'wb').write(kt_wrap(raw,blob))
print(f'msggame: {n} chars normalized across {nr} text runs')
