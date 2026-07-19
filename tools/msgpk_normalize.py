# -*- coding: utf-8 -*-
"""Normalize MSG_PK output in place: fullwidth ASCII/space/interpunct -> halfwidth,
matching the base-game msg_fix.py convention. Length-preserving (1:1 char swap)."""
import struct, os, sys, re
import lz4.block
sys.stdout.reconfigure(encoding='utf-8')
import apply_translations as A

# PK_MSG_OUT: build_msgpk.py's output dir — run that step first, this normalizes in place.
OUT = os.environ.get('PK_MSG_OUT') or r'D:\nsw\rom\nobu16_powerupkit\puk_mod\atmosphere\contents\01007ab012872001\romfs\MSG_PK\JP'

NORM={}
for cp in range(0xFF01,0xFF5F): NORM[cp]=cp-0xFEE0
NORM[0x3000]=0x20
NORM[0x00B7]=0x30FB
NORM[0x2014]=0x30FC

def norm_str(t):
    return ''.join(chr(NORM.get(ord(c),ord(c))) for c in t)

STR_FILES=['msgdata.bin','msgev.bin','msgui.bin','msgbre.bin','msgire.bin']
tot=0
for f in STR_FILES:
    path=os.path.join(OUT,f)
    hdr, dec = A.kt_unwrap(open(path,'rb').read())
    secs = A.read_strtable_raw(dec)
    n=0
    new_secs=[]
    for sec in secs:
        ns=[]
        for s in sec:
            s2=norm_str(s)
            if s2!=s: n+=1
            ns.append(s2)
        new_secs.append(ns)
    dec2 = A.build_strtable(new_secs)
    open(path,'wb').write(A.kt_wrap(hdr,dec2))
    print('%-12s normalized %d strings'%(f,n))
    tot+=n

# msggame.bin text runs
path=os.path.join(OUT,'msggame.bin')
hdr, dec = A.kt_unwrap(open(path,'rb').read())
blob=bytearray(dec)
B=bytes(blob); i=0; n=0
starts=[]
while True:
    s=B.find(b'\x07\x07\x01',i)
    if s<0: break
    e=B.find(b'\x07\x07\x02',s+3)
    if e<0: break
    starts.append((s+3,e)); i=e+3
for s,e in starts:
    if (e-s)%2: continue
    for k in range(s,e,2):
        u=blob[k]|(blob[k+1]<<8)
        v=NORM.get(u)
        if v is not None:
            blob[k]=v&0xFF; blob[k+1]=v>>8; n+=1
open(path,'wb').write(A.kt_wrap(hdr,bytes(blob)))
print('msggame.bin  normalized %d chars across %d text runs'%(n,len(starts)))
tot+=n
print('TOTAL normalized:', tot)
