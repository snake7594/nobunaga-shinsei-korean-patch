"""Fully recursive res_lang G1T extractor: walk ALL entries at ANY depth, decode every
texture, compare JP vs SC, dump differing textures from previously-unexamined entries."""
import struct, os, sys, io, hashlib
import numpy as np
import lz4.block
from PIL import Image, ImageDraw
sys.stdout.reconfigure(encoding='utf-8')

def kt_unwrap(b):
    if len(b) >= 24 and b[0] == 1 and b[1] == 1:
        try:
            dec = struct.unpack_from('<Q', b, 8)[0]; comp = struct.unpack_from('<Q', b, 16)[0]
            if dec > 400_000_000 or comp > len(b): return b
            return lz4.block.decompress(b[24:24 + comp], uncompressed_size=dec)
        except Exception: return b
    return b

def is_link(d):
    if d[:4] != b'LINK' or len(d) < 16: return False
    c = struct.unpack_from('<I', d, 4)[0]
    return 0 < c < 100000 and 16 + c*8 <= len(d)

def walk(d, path, out, depth=0):
    """Collect (path, GT1G blob) for every texture at any nesting depth."""
    if depth > 8: return
    d = kt_unwrap(d)
    if d[:4] == b'GT1G':
        out.append((path, d)); return
    if is_link(d):
        c = struct.unpack_from('<I', d, 4)[0]
        for i in range(c):
            o, s = struct.unpack_from('<II', d, 16 + i*8)
            if 0 < o and 0 < s and o+s <= len(d):
                walk(d[o:o+s], f'{path}.{i}', out, depth+1)

def collect(path):
    d = open(path, 'rb').read()
    out = []
    c = struct.unpack_from('<I', d, 4)[0]
    for i in range(c):
        o, s = struct.unpack_from('<II', d, 16 + i*8)
        if o and s: walk(d[o:o+s], f'{i}', out, 1)
    return out

def bc_img(linear, w, h, fourcc):
    dds = bytearray(128)
    struct.pack_into('<4s', dds, 0, b'DDS '); struct.pack_into('<I', dds, 4, 124)
    struct.pack_into('<I', dds, 8, 0x00081007); struct.pack_into('<I', dds, 12, h)
    struct.pack_into('<I', dds, 16, w); struct.pack_into('<I', dds, 20, len(linear))
    struct.pack_into('<I', dds, 76, 32); struct.pack_into('<I', dds, 80, 0x4)
    struct.pack_into('<4s', dds, 84, fourcc); struct.pack_into('<I', dds, 108, 0x1000)
    return Image.open(io.BytesIO(bytes(dds)+linear)).convert('RGBA')

def decode_g1t(g):
    tbl = struct.unpack_from('<I', g, 0x0C)[0]; ntex = struct.unpack_from('<I', g, 0x10)[0]
    if ntex > 4096: return []
    offs = struct.unpack_from(f'<{ntex}I', g, tbl)
    res = []
    for k, o in enumerate(offs):
        p = tbl + o
        if p+12 > len(g): continue
        fmt, dxdy = g[p+1], g[p+2]
        w = 1 << (dxdy & 0xF); h = 1 << (dxdy >> 4)
        ex = struct.unpack_from('<I', g, p+8)[0]
        end = tbl + offs[k+1] if k+1 < ntex else len(g)
        data = g[p+8+ex:end]
        try:
            if fmt == 0x59:
                res.append((bc_img(bytes(data[:(w//4)*(h//4)*8]), w, h, b'DXT1'), f'BC1 {w}x{h}'))
            elif fmt == 0x5B:
                res.append((bc_img(bytes(data[:(w//4)*(h//4)*16]), w, h, b'DXT5'), f'BC3 {w}x{h}'))
            elif fmt == 0x01:
                a = np.frombuffer(data[:w*h*4], dtype=np.uint8).reshape(h, w, 4)
                res.append((Image.fromarray(a[:,:,[2,1,0,3]].copy(),'RGBA'), f'BGRA8 {w}x{h}'))
            else:
                res.append((None, f'fmt0x{fmt:02X} {w}x{h}'))
        except Exception as e:
            res.append((None, f'ERR {e}'))
    return res

JP = r'D:\nsw\merged_sel\RES_JP\res_lang.bin'
if not os.path.exists(JP): JP = r'D:\nsw\rom\노부나가의 야망 신생_일본판\추출원본\romfs\RES_JP\res_lang.bin'
SC = r'D:\nsw\rom\노부나가의 야망 신생_일본판\추출원본\romfs\RES_SC\res_lang.bin'
jp = collect(JP); sc = collect(SC)
print(f'JP textures: {len(jp)}   SC textures: {len(sc)}')
from collections import Counter
jp_by_entry = Counter(p.split('.')[0] for p,_ in jp)
print('JP GT1G count by top entry:', dict(sorted(jp_by_entry.items(), key=lambda x:int(x[0]))))

# differing textures NOT in entries 0-4 (previously unexamined)
sc_map = {p: hashlib.sha1(b).digest() for p, b in sc}
examined = {'0','1','2','3','4'}
new_targets = []
for p, b in jp:
    top = p.split('.')[0]
    if top in examined: continue
    if b[:4] != b'GT1G': continue
    if p not in sc_map or sc_map[p] != hashlib.sha1(b).digest():
        new_targets.append((p, b))
print(f'\nDIFFERING textures in unexamined entries (5,8+): {len(new_targets)}')
tc = Counter(p.split('.')[0] for p,_ in new_targets)
print('  by entry:', dict(sorted(tc.items(), key=lambda x:int(x[0]))))

# also include entry-5 same-or-diff, and ALL textures in small entries as candidates
OUT = r'D:\nsw\rom\노부나가의 야망 신생_일본판\이미지한글화\deep_png'
os.makedirs(OUT, exist_ok=True)
thumbs = []
for (p, b) in new_targets:
    for t, (img, info) in enumerate(decode_g1t(b)):
        if img is None: continue
        nm = f'{p}_{t}'.replace('.', '-')
        img.save(os.path.join(OUT, nm+'.png'))
        bg = Image.new('RGBA', img.size, (28,28,44,255))
        comp = Image.alpha_composite(bg, img).convert('RGB'); comp.thumbnail((256,256))
        thumbs.append((nm, info, comp))
print(f'exported {len(thumbs)} differing textures from unexamined entries')

SHEET = r'D:\nsw\rom\노부나가의 야망 신생_일본판\이미지한글화\contact_sheets'
COLS,ROWS,CW,CH,CAP = 6,6,262,262,18; per=COLS*ROWS
for s in range(0, len(thumbs), per):
    sheet = Image.new('RGB',(COLS*CW+8, ROWS*(CH+CAP)+8),(18,18,28)); dr=ImageDraw.Draw(sheet)
    for idx,(nm,info,im) in enumerate(thumbs[s:s+per]):
        cx=8+(idx%COLS)*CW; cy=8+(idx//COLS)*(CH+CAP)
        sheet.paste(im,(cx+(250-im.width)//2, cy+(250-im.height)//2))
        dr.text((cx+2,cy+CH-12), f'{nm} {info}', fill=(180,220,180))
    sheet.save(os.path.join(SHEET, f'deep_{s//per:02d}.jpg'), quality=82)
print(f'{(len(thumbs)+per-1)//per} deep sheets written')
