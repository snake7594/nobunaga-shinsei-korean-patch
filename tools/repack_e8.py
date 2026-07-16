# -*- coding: utf-8 -*-
"""Repack localized entry-8 command-button atlas into res_lang.bin (JP)."""
import struct, sys, os, numpy as np, lz4.block, texture2ddecoder
from PIL import Image
sys.stdout.reconfigure(encoding='utf-8')
SP=os.path.dirname(os.path.abspath(__file__))
# base = already-patched res_lang (font in 6,7 + labels in 3 + warning in 1); inject entry 8
SRC=r'D:\nsw\rom\노부나가의 야망 신생_일본판\한글패치_테스트\romfs\RES_JP\res_lang.bin'
OUT=r'D:\nsw\rom\노부나가의 야망 신생_일본판\한글패치_테스트\romfs\RES_JP\res_lang.bin'

def kt_decompress(b):
    dec=struct.unpack_from('<Q',b,8)[0]; comp=struct.unpack_from('<Q',b,16)[0]
    return lz4.block.decompress(b[24:24+comp],uncompressed_size=dec)

res=open(SRC,'rb').read()
# outer entries via TOC@16 (contiguous)
cnt=struct.unpack_from('<I',res,4)[0]
outer=[struct.unpack_from('<II',res,16+i*8) for i in range(cnt)]
o8,s8=outer[8]; e8=res[o8:o8+s8]
# inner entry8: TOC@0x20, single child at (0x1680, csize)
coff,csize=struct.unpack_from('<II',e8,0x20)
orig_child=e8[coff:coff+csize]
g=kt_decompress(orig_child)
assert g[:4]==b'GT1G' and len(g)==2099284, (g[:4],len(g))

# --- new GT1G: replace tex0 BC3 (offset 64, 2097152 bytes) ---
mixed=open(os.path.join(SP,'e8_mixed_bc3.bin'),'rb').read()
assert len(mixed)==2097152
new_g=g[:64]+mixed+g[64+2097152:]
assert len(new_g)==len(g)

# --- KT-wrap (preserve header bytes 0-7 = magic+hash; new dec/comp sizes) ---
comp=lz4.block.compress(new_g, mode='high_compression', compression=12, store_size=False)
new_child=orig_child[:8]+struct.pack('<Q',len(new_g))+struct.pack('<Q',len(comp))+comp
assert kt_decompress(new_child)==new_g, 'KT roundtrip failed'
print(f'child: {len(orig_child):,} -> {len(new_child):,} bytes')

# --- rebuild entry 8: preserve bytes[0:coff], append new child, update inner TOC size ---
new_e8=bytearray(e8[:coff])+new_child
struct.pack_into('<II', new_e8, 0x20, coff, len(new_child))  # offset unchanged (16-aligned), new size
new_e8=bytes(new_e8)
print(f'entry8: {len(e8):,} -> {len(new_e8):,} bytes  (child off 0x{coff:x} align16={coff%16==0})')

# --- rebuild outer (TOC@16, contiguous) ---
entries=[]
for i,(off,size) in enumerate(outer):
    nxt=outer[i+1][0] if i+1<len(outer) else len(res)
    entries.append([res[off:off+size], res[off+size:nxt]])  # [blob, gap]
entries[8][0]=new_e8
out=bytearray(res[:outer[0][0]])
for i,(blob,gap) in enumerate(entries):
    struct.pack_into('<II', out, 16+i*8, len(out), len(blob))
    out+=blob; out+=gap
os.makedirs(os.path.dirname(OUT),exist_ok=True)
open(OUT,'wb').write(out)
print(f'written {OUT}: {len(res):,} -> {len(out):,} bytes')

# --- VERIFY: re-parse rebuilt file, extract entry8 tex0, decode, compare to e8_ko ---
v=open(OUT,'rb').read()
vcnt=struct.unpack_from('<I',v,4)[0]
vouter=[struct.unpack_from('<II',v,16+i*8) for i in range(vcnt)]
vo8,vs8=vouter[8]; ve8=v[vo8:vo8+vs8]
vcoff,vcsize=struct.unpack_from('<II',ve8,0x20)
vg=kt_decompress(ve8[vcoff:vcoff+vcsize])
assert vg==new_g, 'GT1G mismatch after rebuild'
dec=texture2ddecoder.decode_bc3(vg[64:64+2097152],2048,1024)
arr=np.frombuffer(dec,np.uint8).reshape(1024,2048,4)[:,:,[2,1,0,3]]
ko=np.array(Image.open(os.path.join(SP,'e8_ko.png')).convert('RGBA'))
# compare only changed (text) regions loosely
diff=np.abs(arr.astype(int)-ko.astype(int)).mean()
print(f'VERIFY OK: entry8 roundtrips; mean|decoded-source|={diff:.2f} (BC3 lossy, expect small)')
# also verify other entries unchanged (fonts 6,7 and labels 3)
for i in (3,6,7):
    a=res[outer[i][0]:outer[i][0]+outer[i][1]]
    b=v[vouter[i][0]:vouter[i][0]+vouter[i][1]]
    print(f'  entry {i} identical: {a==b}')
