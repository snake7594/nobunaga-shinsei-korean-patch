# -*- coding: utf-8 -*-
"""Remove manual line breaks (\\n) from DIALOGUE strings so the engine auto-wraps them to
fill the dialogue box, fixing horizontal overflow of Korean lines. FORMATTED strings
(tutorials/help/settings with headers, bullet lists, aligned tables, toggle options) keep
their \\n. Operates on the built MSG_PK files (msgev/msgdata + msggame runs).
Env DRY=1 -> report only. ROOT env picks the MSG_PK/JP dir."""
import struct, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import apply_translations as A

ROOT = os.environ.get('ROOT') or r'D:\nsw\rom\nobu16_powerupkit\puk_mod_117\atmosphere\contents\01007ab012872001\romfs\MSG_PK\JP'
DRY = os.environ.get('DRY') == '1'

# FORMATTED markers -> keep \n (do NOT auto-wrap; would destroy alignment)
CTRL_GLYPH = re.compile(r'[㈀-㏿]')          # ㈀-㏿ incl. button/control glyphs ㌍㍑ etc.
TOGGLE = re.compile(r'\[(유효|무효|표시|비표시|커스텀|일본어|영어|왼손잡이용|오른손잡이용|표준|속도 우선|화질 우선|최고 화질|부대 수 변동 시|영지 변경 시 표시|모두 표시|모두 무효|모두 유효|모두 비표시|일부 표시)')
BULLET_LINE = re.compile(r'(^|\\n)[　 ]*[・･]')     # a line starting with ・ (bullet list)
IDEO_RUN = re.compile(r'　{3,}')                  # 3+ ideographic spaces = column alignment
HEADER = re.compile(r'[【】●※]')                       # help/menu headers, notes

def is_formatted(t):
    if HEADER.search(t): return True
    if CTRL_GLYPH.search(t): return True
    if TOGGLE.search(t): return True
    if BULLET_LINE.search(t): return True
    if IDEO_RUN.search(t): return True
    return False

def strip(t):
    # replace manual breaks with a single space; collapse doubled spaces created thereby
    t2 = t.replace('\\n', ' ')
    t2 = re.sub(r'  +', ' ', t2)
    return t2.strip()

def process_strtable(path, label):
    raw = open(path, 'rb').read()
    hdr, dec = A.kt_unwrap(raw)
    secs = A.read_strtable_raw(dec)
    n_strip = n_keep = 0
    samples_strip, samples_keep = [], []
    new = []
    for sec in secs:
        ns = []
        for t in sec:
            if '\\n' in t and not is_formatted(t):
                if len(samples_strip) < 6:
                    samples_strip.append((t, strip(t)))
                t = strip(t); n_strip += 1
            elif '\\n' in t:
                n_keep += 1
                if len(samples_keep) < 4:
                    samples_keep.append(t)
            ns.append(t)
        new.append(ns)
    print(f'== {label}: dialogue stripped={n_strip}  formatted kept={n_keep}')
    for a, b in samples_strip:
        print(f'   STRIP: {a[:60]!r}')
        print(f'       -> {b[:60]!r}')
    for k in samples_keep:
        print(f'   KEEP : {k[:60]!r}')
    if not DRY:
        dec2 = A.build_strtable(new)
        open(path, 'wb').write(A.kt_wrap(hdr, dec2))
    return n_strip

def process_msggame(path, label):
    raw = open(path, 'rb').read()
    hdr, dec = A.kt_unwrap(raw)
    count = struct.unpack_from('<I', dec, 0)[0]
    new_secs = []
    n_strip = n_keep = 0
    samples = []
    for i in range(count):
        off, size = struct.unpack_from('<II', dec, 4 + i*8)
        n = struct.unpack_from('<I', dec, off)[0]
        offs = struct.unpack_from(f'<{n}I', dec, off + 4)
        ends = list(offs[1:]) + [size]
        blobs = []
        for j in range(n):
            blob = dec[off + offs[j]: off + ends[j]]
            out = bytearray(); p = 0
            while True:
                a = blob.find(b'\x07\x07\x01', p)
                if a < 0:
                    out += blob[p:]; break
                b_ = blob.find(b'\x07\x07\x02', a + 3)
                if b_ < 0:
                    out += blob[p:]; break
                out += blob[p:a + 3]
                rawseg = blob[a + 3:b_]
                if len(rawseg) % 2 == 0 and rawseg:
                    s = A.esc(struct.unpack_from(f'<{len(rawseg)//2}H', rawseg))
                    if '\\n' in s and not is_formatted(s):
                        s2 = strip(s)
                        if len(samples) < 8:
                            samples.append((s, s2))
                        cus = A.unesc(s2)
                        out += struct.pack(f'<{len(cus)}H', *cus)
                        n_strip += 1
                    else:
                        if '\\n' in s:
                            n_keep += 1
                        out += rawseg
                else:
                    out += rawseg
                out += b'\x07\x07\x02'
                p = b_ + 3
            blobs.append(bytes(out))
        sec = bytearray(struct.pack('<I', n))
        pos = 4 + 4 * n; o2 = []
        for b in blobs:
            o2.append(pos); pos += len(b)
        sec += struct.pack(f'<{n}I', *o2)
        for b in blobs:
            sec += b
        new_secs.append(bytes(sec))
    print(f'== {label}: dialogue stripped={n_strip}  formatted kept={n_keep}')
    for a, b in samples[:6]:
        print(f'   STRIP: {a[:60]!r}')
        print(f'       -> {b[:60]!r}')
    if not DRY:
        out = bytearray(struct.pack('<I', count))
        toc_pos = len(out); out += b'\x00' * (8 * count)
        for i, b in enumerate(new_secs):
            while len(out) % 4:
                out += b'\x00'
            struct.pack_into('<II', out, toc_pos + i*8, len(out), len(b))
            out += b
        open(path, 'wb').write(A.kt_wrap(hdr, bytes(out)))
    return n_strip

total = 0
# Only the dialogue-box contexts (confirmed auto-wrap): opening/event narration & speech
# (msgev) and in-game character dialogue (msggame). msgdata = scenario-selection description
# panel whose wrap behavior is uncertain -> left untouched to avoid panel-layout regressions.
total += process_strtable(os.path.join(ROOT, 'msgev.bin'), 'msgev (scenario/event)')
total += process_msggame(os.path.join(ROOT, 'msggame.bin'), 'msggame (in-game dialogue)')
print(f'\nTOTAL dialogue strings de-broken: {total}', '(DRY-RUN)' if DRY else '')
