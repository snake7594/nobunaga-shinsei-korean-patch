"""Extract Japanese strings from decompressed main executable across encodings,
mapping each hit to its NSO segment (.text/.rodata/.data)."""
import struct, sys, re, os
sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))

d = open(os.path.join(SP, 'main_dec.bin'), 'rb').read()
# segment layout from nso_decompress (mem offsets/sizes)
# .text mem_off=0x0 size=0x1480E50 ; .rodata 0x1481000 size=0xA11F98 ; .data 0x1E93000 size=0x182738
SEGS = [('.text', 0x0, 0x1480E50), ('.rodata', 0x1481000, 0xA11F98), ('.data', 0x1E93000, 0x182738)]
def seg_of(off):
    for name, base, size in SEGS:
        if base <= off < base + size:
            return name
    return '?'

# Japanese codepoint test: hiragana, katakana, CJK ideographs, kanji punctuation
def is_jp(cp):
    return (0x3040 <= cp <= 0x30FF and cp != 0x30FB) or (0x3400 <= cp <= 0x9FFF) or (0xF900 <= cp <= 0xFAFF)

def has_jp(s):
    return any(is_jp(ord(c)) for c in s)

results = {'utf16le': [], 'utf8': [], 'sjis': []}

# ---- UTF-16LE: sequences of printable/JP u16 ----
i = 0
n = len(d)
while i + 1 < n:
    cu = d[i] | (d[i+1] << 8)
    if is_jp(cu) or (0x20 <= cu <= 0x7E) or cu in (0x3000,) or (0xFF01 <= cu <= 0xFF5E):
        start = i
        chars = []
        while i + 1 < n:
            cu = d[i] | (d[i+1] << 8)
            if is_jp(cu) or (0x20 <= cu <= 0x7E) or cu == 0x3000 or (0xFF01 <= cu <= 0xFF60) or cu in (0x2026, 0x30FB, 0x2015, 0x3001, 0x3002, 0x300C, 0x300D):
                chars.append(chr(cu)); i += 2
            else:
                break
        s = ''.join(chars)
        if has_jp(s) and len(s) >= 1:
            results['utf16le'].append((start, s))
    else:
        i += 2 if cu == 0 else 1

# ---- UTF-8: decode runs ----
for m in re.finditer(rb'(?:[\xE3-\xE9][\x80-\xBF][\x80-\xBF]|[\x20-\x7e]){2,}', d):
    try:
        s = m.group().decode('utf-8')
    except UnicodeDecodeError:
        continue
    if has_jp(s):
        results['utf8'].append((m.start(), s))

# ---- Shift-JIS: decode plausible runs ----
for m in re.finditer(rb'(?:[\x81-\x9f\xe0-\xef][\x40-\x7e\x80-\xfc]|[\x20-\x7e]){3,}', d):
    try:
        s = m.group().decode('shift-jis')
    except UnicodeDecodeError:
        continue
    if has_jp(s) and sum(1 for c in s if is_jp(ord(c))) >= 2:
        results['sjis'].append((m.start(), s))

for enc, lst in results.items():
    segc = {}
    for off, s in lst:
        segc[seg_of(off)] = segc.get(seg_of(off), 0) + 1
    print(f'=== {enc}: {len(lst)} JP strings, by segment {segc} ===')
    # unique
    seen = set()
    uniq = []
    for off, s in lst:
        if s not in seen:
            seen.add(s); uniq.append((off, s))
    for off, s in uniq[:80]:
        disp = s.replace('\n', '\\n')
        print(f'  0x{off:08X} [{seg_of(off)}] {disp[:80]}')
    if len(uniq) > 80:
        print(f'  ... +{len(uniq)-80} more unique')
    print()

# save full utf16 unique list (most relevant for UI)
with open(os.path.join(SP, 'main_jp_utf16.txt'), 'w', encoding='utf-8') as f:
    seen = set()
    for off, s in results['utf16le']:
        if s not in seen:
            seen.add(s)
            f.write(f'0x{off:08X}\t{seg_of(off)}\t{s}\n')
print(f'utf16 unique saved: {len(set(s for _,s in results["utf16le"]))}')
