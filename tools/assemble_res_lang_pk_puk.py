# -*- coding: utf-8 -*-
"""Assemble final res_lang_pk.bin: start from the current mod build (font entries 16/17
already fixed size-preserving in-place), wholesale-replace outer entries 18 (labels) and
21 (badges) with their newly localized LINK archive blobs. Mirrors koloc.rebuild_reslang's
gap-preserving TOC rebuild, but with pre-built replacement blobs instead of per-texture
tex_replacements (entries 18/21 are LINK-of-many-children, not single-G1T entries)."""
import sys, os, struct
sys.path.insert(0,'.'); import koloc
sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))

SRC = os.environ.get('PK_RES_OUT') or r'D:\nsw\rom\nobu16_powerupkit\puk_mod\atmosphere\contents\01007ab012872001\romfs\RES_JP_PK\res_lang_pk.bin'
OUT = SRC  # in place

res = open(SRC, 'rb').read()
outer = koloc.outer_entries(res)
print('entries:', len(outer))

new_blobs = {
    18: open(os.path.join(SP, 'e18_new_link.bin'), 'rb').read(),
    21: open(os.path.join(SP, 'e21_new_link.bin'), 'rb').read(),
}
for i, b in new_blobs.items():
    assert b[:4] == b'LINK', f'entry{i} replacement not a LINK archive'

ents = []
for i, (off, size) in enumerate(outer):
    nxt = outer[i+1][0] if i+1 < len(outer) else len(res)
    blob = new_blobs[i] if i in new_blobs else res[off:off+size]
    gap = res[off+size:nxt]
    ents.append((blob, gap))

out = bytearray(res[:outer[0][0]])
for i, (blob, gap) in enumerate(ents):
    struct.pack_into('<II', out, 16 + i*8, len(out), len(blob))
    out += blob
    out += gap

open(OUT, 'wb').write(bytes(out))
print(f'res_lang_pk.bin: {len(res):,} -> {len(out):,} bytes')

# ---- verify ----
v = open(OUT, 'rb').read()
vouter = koloc.outer_entries(v)
assert len(vouter) == len(outer)
bad = 0
for i, (off, size) in enumerate(vouter):
    if off < 0 or off + size > len(v):
        print('OOB entry', i); bad += 1
print('BAD entries:', bad)

# font entries 16/17 must be byte-identical (offset + content unchanged)
for idx in (16, 17):
    a = res[outer[idx][0]:outer[idx][0]+outer[idx][1]]
    b = v[vouter[idx][0]:vouter[idx][0]+vouter[idx][1]]
    print(f'  entry{idx} (font) identical: {a == b}  same_offset: {vouter[idx][0]==outer[idx][0]}')
    off, sz = vouter[idx]
    g = koloc.kt_decompress(v[off:off+sz])
    print(f'    decompressed size: {len(g)}')

# entries 18/21 re-parse correctly with expected child counts
for idx, expect in [(18, 43), (21, 33)]:
    off, size = vouter[idx]
    blob = v[off:off+size]
    ch = koloc.link_children(blob)
    print(f'  entry{idx}: {len(ch)} children (expect {expect})', 'OK' if len(ch)==expect else 'MISMATCH')
