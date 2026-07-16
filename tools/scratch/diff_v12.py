"""Byte-diff rebuilt res_lang vs original: verify only intended sub-entries changed."""
import struct, os, sys, hashlib
import lz4.block
sys.stdout.reconfigure(encoding='utf-8')

ORIG = r'D:\nsw\rom\노부나가의 야망 신생_일본판\추출원본\romfs\RES_JP\res_lang.bin'
NEW = r'D:\nsw\rom\노부나가의 야망 신생_일본판\한글패치_테스트\romfs\RES_JP\res_lang.bin'

def parse_link(d):
    count = struct.unpack_from('<I', d, 4)[0]
    return [struct.unpack_from('<II', d, 16 + i * 8) for i in range(count)]

def kt_unwrap(blob):
    dec = struct.unpack_from('<Q', blob, 8)[0]
    comp = struct.unpack_from('<Q', blob, 16)[0]
    return lz4.block.decompress(blob[24:24 + comp], uncompressed_size=dec)

o = open(ORIG, 'rb').read()
n = open(NEW, 'rb').read()
to, tn = parse_link(o), parse_link(n)
print(f'entries: {len(to)} vs {len(tn)}')

for i in range(len(to)):
    bo = o[to[i][0]:to[i][0] + to[i][1]]
    bn = n[tn[i][0]:tn[i][0] + tn[i][1]]
    if bo[:4] == b'LINK' and bn[:4] == b'LINK':
        so, sn = parse_link(bo), parse_link(bn)
        if len(so) != len(sn):
            print(f'entry {i}: SUB COUNT DIFF {len(so)} vs {len(sn)}')
            continue
        diffs = []
        for j in range(len(so)):
            ro = bo[so[j][0]:so[j][0] + so[j][1]]
            rn = bn[sn[j][0]:sn[j][0] + sn[j][1]]
            if hashlib.sha1(ro).digest() != hashlib.sha1(rn).digest():
                # compare decompressed if wrapped
                note = ''
                try:
                    do = kt_unwrap(ro); dn = kt_unwrap(rn)
                    same_size = len(do) == len(dn)
                    ndiff = sum(1 for a, b in zip(do[:64], dn[:64]) if a != b)
                    note = f'(dec {len(do):,}->{len(dn):,}, hdr64diff={ndiff})'
                except Exception as e:
                    note = f'(unwrap err {e})'
                diffs.append((j, note))
        # also check inner header/gap bytes
        hdr_same = bo[:so[0][0]] == bn[:sn[0][0]] if so else True
        if diffs or not hdr_same:
            print(f'entry {i}: {len(diffs)} sub diffs, toc_area_same={hdr_same}')
            for j, note in diffs[:12]:
                print(f'    sub[{j}] changed {note}')
    else:
        if hashlib.sha1(bo).digest() != hashlib.sha1(bn).digest():
            print(f'entry {i}: changed (non-LINK), {len(bo):,} -> {len(bn):,}')
