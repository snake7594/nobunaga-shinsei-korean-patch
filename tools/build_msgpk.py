# -*- coding: utf-8 -*-
"""Final MSG_PK (872001 Power-Up Kit program) rebuild.

Merges two translation sets by original-JP-string key:
  1. the base game's dict (translation/source_jp + translation/korean, ~46,979 strings) —
     MSG_PK shares most of its text with the base game's MSG, so this covers it almost
     entirely for free;
  2. the PUK-only additions (translation/source_jp_puk + translation/korean_puk, ~7,815
     strings) for content unique to the Power-Up Kit (new scenarios, policies, tactics...).

PK_MSG_SRC must be a real-hardware dump of the 872001 program's MSG_PK/JP — a PC-based
multi-program NSP extraction does not reproduce this file set correctly. See docs/BUILD.md.
"""
import os, sys, struct, shutil, json, glob
sys.stdout.reconfigure(encoding='utf-8')
import apply_translations as A

PK_IN = os.environ.get('PK_MSG_SRC') or r'D:\nsw\rom\1.1.5\Program 1\romfs\MSG_PK\JP'
OUT   = os.environ.get('PK_MSG_OUT') or r'D:\nsw\rom\nobu16_powerupkit\puk_mod\atmosphere\contents\01007ab012872001\romfs\MSG_PK\JP'
os.makedirs(OUT, exist_ok=True)

SP = os.path.dirname(os.path.abspath(__file__))
TR_DIR = os.path.join(SP, '..', 'translation')

def load_pair_dict(src_dir, ko_dir):
    """translation/<src_dir>/bXXXX.json {i,t=JP} + translation/<ko_dir>/bXXXX.json {i,t=KO}
    -> {JP: KO} dict, keyed by matching filename+index (same convention as apply_translations)."""
    tr = {}
    for bf in glob.glob(os.path.join(TR_DIR, src_dir, '*.json')):
        name = os.path.basename(bf)
        src = {it['i']: it['t'] for it in json.load(open(bf, encoding='utf-8'))['items']}
        kf = os.path.join(TR_DIR, ko_dir, name)
        if not os.path.isfile(kf):
            continue
        for it in json.load(open(kf, encoding='utf-8'))['items']:
            if it['i'] in src and isinstance(it.get('t'), str) and it['t'].strip():
                tr[src[it['i']]] = it['t']
    return tr

tr_base = load_pair_dict('source_jp', 'korean')
tr_puk = load_pair_dict('source_jp_puk', 'korean_puk')
tr = dict(tr_base); tr.update(tr_puk)
print('translation dict: base=%d + puk=%d -> combined=%d' % (len(tr_base), len(tr_puk), len(tr)))

STR_FILES  = ['msgdata.bin','msgev.bin','msgui.bin','msgbre.bin','msgire.bin']
PASS_FILES = ['msgstf.bin']

used=[0]
for f in STR_FILES:
    hdr, dec = A.kt_unwrap(open(os.path.join(PK_IN,f),'rb').read())
    secs = A.read_strtable_raw(dec)
    secs = [[A.translate_str(s, tr, used) for s in sec] for sec in secs]
    dec2 = A.build_strtable(secs)
    open(os.path.join(OUT,f),'wb').write(A.kt_wrap(hdr, dec2))
    print('  %-12s %d -> %d'%(f, len(dec), len(dec2)))
for f in PASS_FILES:
    shutil.copy2(os.path.join(PK_IN,f), os.path.join(OUT,f))
    print('  %-12s passthrough (credits)'%f)
hdr, dec = A.kt_unwrap(open(os.path.join(PK_IN,'msggame.bin'),'rb').read())
dec2 = A.rebuild_msggame(dec, tr, used)
open(os.path.join(OUT,'msggame.bin'),'wb').write(A.kt_wrap(hdr, dec2))
print('  %-12s %d -> %d'%('msggame.bin', len(dec), len(dec2)))
print('translated in-place:', used[0])
print('wrote MSG_PK/JP to', OUT)
