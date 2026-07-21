# -*- coding: utf-8 -*-
"""Rebuild the three v3.7 binary files:
 1) res_lang_exp_ko.bin   (base): e3/c0 t1 = Korean nav atlas; e0 children: 9 reused
    Korean title blobs from shipped res_lang e3 + 1 new render (c108)
 2) res_lang_exp_pk_ko.bin (PUK): e0 c19 reuse + c44-47 new; e3/c0 t0 = Korean banners;
    e4/c0 t1 = Korean buttons (BC7 slot -> BC3 data + fmt byte swap)
 3) res_lang_pk_v37.bin   (PUK): e4/c0 t0 = Korean banners (same art)
All rebuilt with gap-preserving outer TOC and 16-aligned inner children."""
import sys, os, struct
sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import koloc
import numpy as np
from PIL import Image
from bc_encode import encode_bc3

OUT_DIR = os.path.join(SP, 'v37_out')

def link_pairs(d):
    n = struct.unpack_from('<I', d, 4)[0]
    tab = struct.unpack_from('<I', d, 8)[0]
    if not (16 <= tab < len(d) and tab % 4 == 0):
        tab = 0x10
    return tab, [struct.unpack_from('<II', d, tab + i*8) for i in range(n)]

def rebuild_inner_link(blob, repl_children):
    """blob = raw LINK payload with children; repl_children = {idx: new_child_bytes}.
    CRITICAL: preserve EVERYTHING up to the first child's original offset (header, TOC,
    sprite/coordinate tables live between the TOC and the children — see koloc.rebuild_entry
    which keeps e[:coff]). Children are re-laid 16-aligned in original file order and the
    TOC pairs are patched in place inside the preserved prefix."""
    toc, pairs = link_pairs(blob)
    nonzero = [(i, off, sz) for i, (off, sz) in enumerate(pairs) if sz > 0]
    assert nonzero, 'no children'
    first = min(off for _, off, _ in nonzero)
    assert first >= toc + len(pairs) * 8, 'children overlap TOC'
    out = bytearray(blob[:first])
    cursor = first
    new_pairs = {i: (off, sz) for i, (off, sz) in enumerate(pairs) if sz == 0}
    for i, off, sz in sorted(nonzero, key=lambda t: t[1]):     # original file order
        ch = repl_children.get(i, blob[off:off+sz])
        pad = (-cursor) % 16
        out += b'\x00' * pad
        cursor += pad
        new_pairs[i] = (cursor, len(ch))
        out += ch
        cursor += len(ch)
    for i in range(len(pairs)):
        off, sz = new_pairs[i]
        struct.pack_into('<II', out, toc + i*8, off, sz)
    return bytes(out)

def rebuild_outer(res, repl_entries):
    """res = whole res_lang-style file; repl_entries = {idx: new_entry_bytes}.
    Gap-preserving outer rebuild (assemble_res_lang_pk pattern)."""
    outer = koloc.outer_entries(res)
    ents = []
    for i, (off, size) in enumerate(outer):
        nxt = outer[i+1][0] if i+1 < len(outer) else len(res)
        blob = repl_entries.get(i, res[off:off+size])
        gap = res[off+size:nxt]
        ents.append((blob, gap))
    out = bytearray(res[:outer[0][0]])
    for i, (blob, gap) in enumerate(ents):
        struct.pack_into('<II', out, 16 + i*8, len(out), len(blob))
        out += blob
        out += gap
    return bytes(out)

def replace_tex_in_g1t(g, tid, new_rgba, allow_fmt_swap=False):
    """Return new g1t bytes with texture tid's data replaced (BC3 encode).
    If the slot is BC7 (0x5F) and allow_fmt_swap, swap fmt byte to BC3 (same block size)."""
    texs = koloc.g1t_textures(g)
    t = texs[tid]
    g2 = bytearray(g)
    if t['fmt'] == 0x5B:
        orig = bytes(g[t['data_off']:t['data_off']+t['data_len']])
        payload, _ = koloc.mixed_bc3(orig, t['rgba'], new_rgba)
    elif t['fmt'] == 0x5F and allow_fmt_swap:
        payload = encode_bc3(new_rgba)
        need = (t['w']//4)*(t['h']//4)*16
        payload = payload[:need]
        # find the fmt byte location: texture record starts at data_off - 8 - ex... simpler:
        # walk table again to get record offset
        tbl = struct.unpack_from('<I', g, 0x0C)[0]
        ntex = struct.unpack_from('<I', g, 0x10)[0]
        offs = struct.unpack_from(f'<{ntex}I', g, tbl)
        p = tbl + offs[tid]
        assert g2[p+1] == 0x5F
        g2[p+1] = 0x5B
    else:
        raise ValueError(f'unsupported fmt 0x{t["fmt"]:X}')
    assert len(payload) <= t['data_len'], (len(payload), t['data_len'])
    g2[t['data_off']:t['data_off']+len(payload)] = payload
    return bytes(g2)

def get_entry(res, idx):
    off, sz = koloc.outer_entries(res)[idx]
    return res[off:off+sz]

def child_blob(entry_payload, idx):
    toc, pairs = link_pairs(entry_payload)
    off, sz = pairs[idx]
    return entry_payload[off:off+sz]

def load_npy(name):
    return np.load(os.path.join(OUT_DIR, name + '.npy'))

# ---------- 1) base res_lang_exp ----------
EXP = open(r'D:\nsw\rom\1.1.5\Program 0\romfs\RES_JP\res_lang_exp.bin', 'rb').read()
SHIP_BASE = open(r'D:\nsw\rom\nobu16_powerupkit\patch_build\romfs\RES_JP\res_lang.bin', 'rb').read()

# e3: nav atlas t1 (KT-child inside LINK(1))
e3 = get_entry(EXP, 3)
c0 = child_blob(e3, 0)
g = koloc.kt_decompress(c0)
ko_nav = np.array(Image.open(os.path.join(SP, 'e5_t1_ko.png')).convert('RGBA'))
g_new = replace_tex_in_g1t(g, 1, ko_nav)
e3_new = rebuild_inner_link(e3, {0: koloc.kt_wrap(c0, g_new)})

# e0: children reuse from shipped base e3 + c108 new
ship_e3 = get_entry(SHIP_BASE, 3)
e0 = get_entry(EXP, 0)
repl0 = {}
for j in [1, 36, 38, 51, 52, 53, 64, 69, 72]:
    repl0[j] = child_blob(ship_e3, j)
c108 = child_blob(e0, 108)
g108 = koloc.kt_decompress(c108)
g108_new = replace_tex_in_g1t(g108, 0, load_npy('exp_e0_c108'))
repl0[108] = koloc.kt_wrap(c108, g108_new)
e0_new = rebuild_inner_link(e0, repl0)

exp_new = rebuild_outer(EXP, {0: e0_new, 3: e3_new})
p1 = os.path.join(OUT_DIR, 'res_lang_exp_ko.bin')
open(p1, 'wb').write(exp_new)
print(f'res_lang_exp_ko.bin: {len(EXP):,} -> {len(exp_new):,}')

# ---------- 2) PUK res_lang_exp_pk ----------
EXPPK = open(r'D:\nsw\rom\1.1.5\Program 1\romfs\RES_JP_PK\res_lang_exp_pk.bin', 'rb').read()
SHIP_PK = open(r'D:\nsw\rom\nobu16_powerupkit\puk_mod\atmosphere\contents\01007ab012872001\romfs\RES_JP_PK\res_lang_pk.bin', 'rb').read()

# e0: c19 reuse + c44-47 new
ship_e18 = get_entry(SHIP_PK, 18)
e0pk = get_entry(EXPPK, 0)
repl = {19: child_blob(ship_e18, 19)}
for j, name in [(44, 'exppk_e0_c44'), (45, 'exppk_e0_c45'), (46, 'exppk_e0_c46'), (47, 'exppk_e0_c47')]:
    cj = child_blob(e0pk, j)
    gj = koloc.kt_decompress(cj)
    gj_new = replace_tex_in_g1t(gj, 0, load_npy(name))
    repl[j] = koloc.kt_wrap(cj, gj_new)
e0pk_new = rebuild_inner_link(e0pk, repl)

# e3: banners t0
e3pk = get_entry(EXPPK, 3)
c0 = child_blob(e3pk, 0)
g = koloc.kt_decompress(c0)
g_new = replace_tex_in_g1t(g, 0, load_npy('banner_t0'))
e3pk_new = rebuild_inner_link(e3pk, {0: koloc.kt_wrap(c0, g_new)})

# e4: buttons t1 (BC7 slot)
e4pk = get_entry(EXPPK, 4)
c0 = child_blob(e4pk, 0)
g = koloc.kt_decompress(c0)
g_new = replace_tex_in_g1t(g, 1, load_npy('btn_t1'), allow_fmt_swap=True)
e4pk_new = rebuild_inner_link(e4pk, {0: koloc.kt_wrap(c0, g_new)})

exppk_new = rebuild_outer(EXPPK, {0: e0pk_new, 3: e3pk_new, 4: e4pk_new})
p2 = os.path.join(OUT_DIR, 'res_lang_exp_pk_ko.bin')
open(p2, 'wb').write(exppk_new)
print(f'res_lang_exp_pk_ko.bin: {len(EXPPK):,} -> {len(exppk_new):,}')

# ---------- 3) res_lang_pk e4 banners ----------
e4 = get_entry(SHIP_PK, 4)
c0 = child_blob(e4, 0)
g = koloc.kt_decompress(c0)
g_new = replace_tex_in_g1t(g, 0, load_npy('banner_t0'))
e4_new = rebuild_inner_link(e4, {0: koloc.kt_wrap(c0, g_new)})
pk_new = rebuild_outer(SHIP_PK, {4: e4_new})
p3 = os.path.join(OUT_DIR, 'res_lang_pk_v37.bin')
open(p3, 'wb').write(pk_new)
print(f'res_lang_pk_v37.bin: {len(SHIP_PK):,} -> {len(pk_new):,}')

# ---------- verification: reparse everything ----------
def verify(path, checks):
    res = open(path, 'rb').read()
    outer = koloc.outer_entries(res)
    assert all(off + sz <= len(res) for off, sz in outer), 'outer OOB'
    for (e, c, tid, probe_rgba) in checks:
        ent = get_entry(res, e)
        cb = child_blob(ent, c)
        g = cb if cb[:4] in (b'GT1G', b'G1TG') else koloc.kt_decompress(cb)
        texs = koloc.g1t_textures(g)
        t = texs[tid]
        assert t['rgba'] is not None, f'{path} e{e}c{c}t{tid} undecodable'
        if probe_rgba is not None:
            diff = np.abs(t['rgba'].astype(int) - probe_rgba.astype(int)).mean()
            print(f'  {os.path.basename(path)} e{e}/c{c}/t{tid}: diff={diff:.2f}')
    print(f'  {os.path.basename(path)}: OK ({len(outer)} entries)')

def verify_entry_structure(orig_entry, new_entry, replaced):
    """Prefix (header+TOC+sprite tables) must match byte-for-byte outside the TOC pair
    slots; untouched children must be byte-identical."""
    toc_o, pairs_o = link_pairs(orig_entry)
    toc_n, pairs_n = link_pairs(new_entry)
    assert toc_o == toc_n and len(pairs_o) == len(pairs_n)
    first_o = min(off for off, sz in pairs_o if sz > 0)
    first_n = min(off for off, sz in pairs_n if sz > 0)
    assert first_o == first_n, (first_o, first_n)
    po = bytearray(orig_entry[:first_o])
    pn = bytearray(new_entry[:first_n])
    for i in range(len(pairs_o)):                     # blank out TOC pair slots
        for b in range(8):
            po[toc_o + i*8 + b] = 0
            pn[toc_o + i*8 + b] = 0
    assert bytes(po) == bytes(pn), 'prefix (sprite tables) corrupted!'
    for i, (of, sz) in enumerate(pairs_o):
        if sz == 0 or i in replaced:
            continue
        nf, nsz = pairs_n[i]
        assert orig_entry[of:of+sz] == new_entry[nf:nf+nsz], f'untouched child {i} changed'
    return True

print('== structural verify (prefix + untouched children) ==')
for label, orig_res, new_path, checks in [
    ('exp', EXP, p1, [(0, {1, 36, 38, 51, 52, 53, 64, 69, 72, 108}), (3, {0})]),
    ('exppk', EXPPK, p2, [(0, {19, 44, 45, 46, 47}), (3, {0}), (4, {0})]),
    ('res_lang_pk', SHIP_PK, p3, [(4, {0})]),
]:
    new_res = open(new_path, 'rb').read()
    for e_idx, replaced in checks:
        oe = get_entry(orig_res, e_idx)
        ne = get_entry(new_res, e_idx)
        verify_entry_structure(oe, ne, replaced)
        print(f'  {label} e{e_idx}: structure OK')

print('== verify ==')
verify(p1, [(3, 0, 1, ko_nav), (0, 108, 0, load_npy('exp_e0_c108')), (0, 1, 0, None)])
verify(p2, [(0, 44, 0, load_npy('exppk_e0_c44')), (3, 0, 0, load_npy('banner_t0')), (4, 0, 1, load_npy('btn_t1'))])
verify(p3, [(4, 0, 0, load_npy('banner_t0'))])
print('ALL REBUILDS VERIFIED')
