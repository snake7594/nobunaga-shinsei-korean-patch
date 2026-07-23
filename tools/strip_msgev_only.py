# -*- coding: utf-8 -*-
"""Remove manual line breaks (\\n) from msgev ONLY (full-width scenario/event narration &
cutscene text, which the engine auto-wraps). msggame (nameplate/portrait dialogue box that
SHRINKS the font to fit one line) is NEVER touched. Formatted strings (headers/bullets/
aligned tables/toggles/control glyphs) keep their \\n.

Evidence msgev == full-width wrapping box (safe to strip): FLOW_PK cutscene text is shown at
speaker=99998 full-width (even semantic speech); JP per-line width p50~=864-912 across all
msgev bands vs msggame p50=528 (narrower nameplate box). See NOTE_dialogue_linebreak.md.

Env: ROOT=<MSG_PK/JP dir>, DRY=1 report-only, DUMP=<path.json> to emit an audit of every
strip/keep decision for review."""
import struct, os, re, sys, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import apply_translations as A

ROOT = os.environ.get('ROOT') or r'D:\nsw\rom\nobu16_powerupkit\puk_mod_117\atmosphere\contents\01007ab012872001\romfs\MSG_PK\JP'
DRY = os.environ.get('DRY') == '1'
DUMP = os.environ.get('DUMP')
# PROTECT: JSON list of exact 'before' strings (or {'before': ...} objects) that must KEEP \n.
# Matched by content so it works across game versions whose msgev indices differ.
PROTECT = set()
_pp = os.environ.get('PROTECT')
if _pp and os.path.exists(_pp):
    for e in json.load(open(_pp, encoding='utf-8')):
        PROTECT.add(e['before'] if isinstance(e, dict) else e)
    print(f'PROTECT: {len(PROTECT)} content-matched strings will keep \\n')

CTRL_GLYPH = re.compile(r'[㈀-㏿]')                    # circled/parenthesized & unit control glyphs
TOGGLE = re.compile(r'\[(유효|무효|표시|비표시|커스텀|일본어|영어|왼손잡이용|오른손잡이용|표준|속도 우선|화질 우선|최고 화질|부대 수 변동 시|영지 변경 시 표시|모두 표시|모두 무효|모두 유효|모두 비표시|일부 표시)')
BULLET_LINE = re.compile(r'(^|\\n)[　 ]*[・･]')          # a line starting with a bullet
IDEO_RUN = re.compile(r'　{3,}')                        # 3+ ideographic spaces = column alignment
HEADER = re.compile(r'[【】●※]')                          # menu/help headers, notes

def is_formatted(t):
    return bool(HEADER.search(t) or CTRL_GLYPH.search(t) or TOGGLE.search(t)
                or BULLET_LINE.search(t) or IDEO_RUN.search(t))

def strip(t):
    t2 = t.replace('\\n', ' ')
    t2 = re.sub(r'  +', ' ', t2)
    return t2.strip()

def process(path, dump_path=None):
    raw = open(path, 'rb').read()
    hdr, dec = A.kt_unwrap(raw)
    secs = A.read_strtable_raw(dec)
    n_strip = n_keep = 0
    audit = []
    new = []
    gidx = 0
    for sec in secs:
        ns = []
        for t in sec:
            act = 'none'
            if '\\n' in t:
                if t in PROTECT:
                    n_keep += 1; act = 'keep_protected'
                elif is_formatted(t):
                    n_keep += 1; act = 'keep_formatted'
                else:
                    t2 = strip(t); n_strip += 1; act = 'strip'
                    if dump_path is not None:
                        audit.append({'i': gidx, 'act': act, 'before': t, 'after': t2})
                    t = t2
                if dump_path is not None and act in ('keep_formatted', 'keep_protected'):
                    audit.append({'i': gidx, 'act': act, 'before': t, 'after': t})
            ns.append(t); gidx += 1
        new.append(ns)
    print(f'== msgev: stripped={n_strip}  kept(formatted+protected)={n_keep}  (msggame untouched)')
    if dump_path is not None:
        json.dump(audit, open(dump_path, 'w', encoding='utf-8'), ensure_ascii=False)
        print(f'   audit -> {dump_path} ({len(audit)} entries)')
    if not DRY:
        dec2 = A.build_strtable(new)
        open(path, 'wb').write(A.kt_wrap(hdr, dec2))
        print('   written:', path)
    return n_strip

process(os.path.join(ROOT, 'msgev.bin'), DUMP)
