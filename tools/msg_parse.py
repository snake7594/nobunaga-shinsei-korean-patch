import struct, sys

def decode_str(d, pos):
    """null-terminated UTF-16LE starting at pos; returns (text, end)"""
    out = []
    while pos + 1 < len(d):
        cu = struct.unpack_from('<H', d, pos)[0]
        pos += 2
        if cu == 0:
            break
        out.append(cu)
    # render with visible escapes
    s = ''
    for cu in out:
        if cu == 0x1B:
            s += '<ESC>'
        elif cu == 0x0A:
            s += '\\n'
        elif cu < 0x20:
            s += f'<{cu:02X}>'
        else:
            s += chr(cu)
    return s, pos

def parse_section(d, off, size, tag, sample=8):
    sid, f1, f2, f3 = struct.unpack_from('<4I', d, off)
    tab_start = off + f3          # table base (offsets are relative to this)
    tabA_end = tab_start + f1     # f1 = table A size in bytes?
    nA = f1 // 4
    # find where table B ends: first string should start at min offset value
    entriesA = struct.unpack_from(f'<{nA}I', d, tab_start)
    print(f'{tag}: id=0x{sid:X} f1=0x{f1:X}({nA} entries) f2=0x{f2:X} f3=0x{f3:X} size=0x{size:X}')
    # sanity: do entriesA point to valid strings?
    print(f'  tableA first offsets: {[hex(e) for e in entriesA[:4]]} last: {[hex(e) for e in entriesA[-2:]]}')
    # table B: from tabA_end to tab_start+min(entryA values)?
    minA = min(entriesA)
    nB = (tab_start + minA - tabA_end) // 4
    entriesB = struct.unpack_from(f'<{nB}I', d, tabA_end) if nB > 0 else ()
    print(f'  tableB inferred entries: {nB}, first: {[hex(e) for e in entriesB[:4]]}')
    print(f'  f2 (0x{f2:X}) vs min tableB offset: {hex(min(entriesB)) if entriesB else "-"}')
    print(f'  sample table A strings:')
    for i in list(range(min(sample, nA))) + [nA//2, nA-1]:
        s, _ = decode_str(d, tab_start + entriesA[i])
        print(f'    A[{i}] +0x{entriesA[i]:X}: {s[:80]}')
    if entriesB:
        print(f'  sample table B strings:')
        for i in list(range(min(4, nB))) + [nB//2]:
            s, _ = decode_str(d, tab_start + entriesB[i])
            print(f'    B[{i}] +0x{entriesB[i]:X}: {s[:120]}')

path = sys.argv[1]
with open(path, 'rb') as f:
    d = f.read()
count = struct.unpack_from('<I', d, 0)[0]
print(f'=== {path.split(chr(92))[-1]}: {len(d):,} bytes, {count} sections ===')
for i in range(count):
    off, size = struct.unpack_from('<II', d, 4 + i*8)
    try:
        parse_section(d, off, size, f'section {i}')
    except Exception as e:
        print(f'section {i} @0x{off:X}: FAILED {e}')
    print()
