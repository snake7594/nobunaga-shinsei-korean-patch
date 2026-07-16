"""Strict extraction of well-formed Japanese string literals from main.
Only null-terminated strings in .rodata/.data with coherent JP+ASCII content."""
import struct, sys, os
sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))
d = open(os.path.join(SP, 'main_dec.bin'), 'rb').read()

SEGS = [('.text', 0x0, 0x1480E50), ('.rodata', 0x1481000, 0xA11F98), ('.data', 0x1E93000, 0x182738)]
def seg_of(off):
    for name, base, size in SEGS:
        if base <= off < base + size:
            return name
    return '?'

def is_jp(cp):
    return (0x3040 <= cp <= 0x30FA) or (0x30FC <= cp <= 0x30FF) or (0x3400 <= cp <= 0x9FFF) or (0xF900 <= cp <= 0xFAFF)
def is_ok16(cp):
    return (is_jp(cp) or 0x20 <= cp <= 0x7E or cp == 0x3000 or 0xFF01 <= cp <= 0xFF60
            or cp in (0x2026, 0x30FB, 0x2015, 0x3001, 0x3002, 0x300C, 0x300D, 0x3008, 0x3009,
                      0x300A, 0x300B, 0x3010, 0x3011, 0x2018, 0x2019, 0x201C, 0x201D, 0x00B7,
                      0x2605, 0x2606, 0x25CF, 0x25A0, 0x2192, 0x266A, 0x00D7))

def extract_utf16(base, size):
    """null-terminated UTF-16LE strings; return those with >=1 JP char and clean content."""
    out = []
    i = base
    end = base + size
    while i + 1 < end:
        # candidate start: aligned and not preceded arbitrarily
        cu = d[i] | (d[i+1] << 8)
        if cu == 0:
            i += 2
            continue
        start = i
        chars = []
        ok = True
        while i + 1 < end:
            cu = d[i] | (d[i+1] << 8)
            if cu == 0:
                i += 2
                break
            if not is_ok16(cu):
                ok = False
                # skip to next null
                while i + 1 < end and (d[i] | (d[i+1] << 8)) != 0:
                    i += 2
                i += 2
                break
            chars.append(chr(cu))
            i += 2
        if ok and chars:
            s = ''.join(chars)
            njp = sum(1 for c in s if is_jp(ord(c)))
            if njp >= 1 and len(s) >= 1:
                out.append((start, s, njp))
    return out

def extract_utf8(base, size):
    out = []
    i = base
    end = base + size
    while i < end:
        if d[i] == 0:
            i += 1
            continue
        start = i
        buf = bytearray()
        while i < end and d[i] != 0:
            buf.append(d[i]); i += 1
        try:
            s = buf.decode('utf-8')
        except UnicodeDecodeError:
            continue
        njp = sum(1 for c in s if is_jp(ord(c)))
        if njp >= 1 and all(is_ok16(ord(c)) for c in s):
            out.append((start, s, njp))
    return out

for enc, fn in (('UTF-16LE', extract_utf16), ('UTF-8', extract_utf8)):
    print(f'\n========== {enc} (null-terminated, .rodata + .data) ==========')
    allhits = []
    for name, base, size in SEGS[1:]:  # rodata, data
        allhits += [(off, s, njp, name) for off, s, njp in fn(base, size)]
    # dedup
    seen = set()
    uniq = [h for h in allhits if not (h[1] in seen or seen.add(h[1]))]
    # sort by JP density * length to surface real text
    uniq.sort(key=lambda h: -h[2])
    print(f'total {len(allhits)} hits, {len(uniq)} unique')
    from collections import Counter
    print('by segment:', Counter(h[3] for h in allhits))
    print('\n-- top by Japanese-char count --')
    for off, s, njp, seg in uniq[:60]:
        print(f'  0x{off:08X} [{seg}] jp={njp:3} {s[:90]}')
    # save
    with open(os.path.join(SP, f'main_jp_{enc.replace("-","").lower()}.txt'), 'w', encoding='utf-8') as f:
        for off, s, njp, seg in uniq:
            f.write(f'0x{off:08X}\t{seg}\t{njp}\t{s}\n')
