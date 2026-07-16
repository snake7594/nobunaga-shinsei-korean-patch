"""Clean Japanese extraction: even-aligned, null-terminated UTF-16LE, requiring kana.
Also locate the radial-menu command words and dump their context."""
import struct, sys, os, re
sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))
d = open(os.path.join(SP, 'main_dec.bin'), 'rb').read()
SEGS = [('.text', 0x0, 0x1480E50), ('.rodata', 0x1481000, 0xA11F98), ('.data', 0x1E93000, 0x182738)]
def seg_of(off):
    for name, base, size in SEGS:
        if base <= off < base + size:
            return name
    return '?'

HIRA = lambda cp: 0x3041 <= cp <= 0x3096
KATA = lambda cp: 0x30A1 <= cp <= 0x30FA or 0x30FC <= cp <= 0x30FF
KANJI = lambda cp: 0x3400 <= cp <= 0x9FFF or 0xF900 <= cp <= 0xFAFF
def is_jp(cp): return HIRA(cp) or KATA(cp) or KANJI(cp)
def is_ok16(cp):
    return (is_jp(cp) or 0x20 <= cp <= 0x7E or cp == 0x3000 or 0xFF01 <= cp <= 0xFF60
            or cp in (0x2026,0x30FB,0x2015,0x3001,0x3002,0x300C,0x300D,0x3008,0x3009,0x300A,
                      0x300B,0x3010,0x3011,0x2018,0x2019,0x201C,0x201D,0x00B7,0x2605,0x2606,
                      0x25CF,0x25A0,0x2192,0x266A,0x00D7,0xFF5E,0x2154,0x00A0))

def extract(base, size):
    out = []
    i = base
    end = base + size
    while i + 1 < end:
        if d[i] == 0 and d[i+1] == 0:
            i += 2; continue
        start = i
        chars = []; ok = True
        while i + 1 < end:
            cu = d[i] | (d[i+1] << 8)
            if cu == 0: i += 2; break
            if not is_ok16(cu):
                ok = False
                while i + 1 < end and (d[i] | (d[i+1] << 8)) != 0: i += 2
                i += 2; break
            chars.append(chr(cu)); i += 2
        if ok and chars:
            s = ''.join(chars)
            if (start - base) % 2 == 0:  # even aligned
                out.append((start, s))
    return out

# collect from rodata + data
alls = []
for name, base, size in SEGS[1:]:
    alls += extract(base, size)

# real Japanese = contains hiragana or katakana (filters misaligned-ASCII garbage)
def script_of(s):
    has_hira = any(HIRA(ord(c)) for c in s)
    has_kata = any(KATA(ord(c)) for c in s)
    has_kanji = any(KANJI(ord(c)) for c in s)
    if has_hira or has_kata:
        return 'JP'          # kana present -> definitely Japanese
    if has_kanji:
        return 'CJK'         # kanji only -> could be JP/CN or misaligned
    return 'other'

jp = []
seen = set()
for off, s in alls:
    if script_of(s) == 'JP' and s not in seen:
        seen.add(s); jp.append((off, s))

print(f'=== REAL Japanese strings (kana-containing, even-aligned, null-terminated): {len(jp)} unique ===\n')
for off, s in sorted(jp, key=lambda x: x[0]):
    print(f'  0x{off:08X}  {s}')

# save
with open(os.path.join(SP, 'main_jp_real.txt'), 'w', encoding='utf-8') as f:
    for off, s in sorted(jp, key=lambda x: x[0]):
        f.write(f'0x{off:08X}\t{s}\n')

# ---- radial menu words: find exact UTF-16 occurrences and context ----
print('\n=== radial-menu command words in main (UTF-16LE, any alignment) ===')
for w in ('評定','内政','任命','軍事','外交','知行','代官','転封'):
    nb = w.encode('utf-16-le')
    starts = [m.start() for m in re.finditer(re.escape(nb), d)]
    for st in starts:
        # extend to full null-terminated string around it
        a = st
        while a - 2 >= 0 and (d[a-2] | (d[a-1] << 8)) != 0 and is_ok16(d[a-2] | (d[a-1] << 8)):
            a -= 2
        b = st
        while b + 1 < len(d) and (d[b] | (d[b+1] << 8)) != 0:
            b += 2
        ctx = d[a:b].decode('utf-16-le', 'replace')
        print(f'  {w} @0x{st:08X} [{seg_of(st)}] aligned={(st-0x1481000)%2==0} full="{ctx[:60]}"')
