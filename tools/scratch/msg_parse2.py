import struct, sys
sys.stdout.reconfigure(encoding='utf-8')

def decode_str(d, pos, limit=None):
    out = []
    while pos + 1 < (limit or len(d)):
        cu = struct.unpack_from('<H', d, pos)[0]
        pos += 2
        if cu == 0:
            break
        out.append(cu)
    s = ''
    for cu in out:
        if cu == 0x1B: s += '<ESC>'
        elif cu == 0x0A: s += '\\n'
        elif cu < 0x20: s += f'<{cu:02X}>'
        else: s += chr(cu)
    return s, pos

def parse_section(d, off, size, tag):
    sid, f1, f2, f3 = struct.unpack_from('<4I', d, off)
    tab = off + f3
    nA = f1 // 4
    # read offsets until we hit the first string (min offset value)
    first_val = struct.unpack_from('<I', d, tab)[0]
    # total entries = distance from table start to first string / 4
    n_total = first_val // 4
    entries = struct.unpack_from(f'<{n_total}I', d, tab)
    nB = n_total - nA
    # verify monotonic and boundary
    mono = all(entries[i] <= entries[i+1] for i in range(n_total-1))
    end_last, _ = decode_str(d, tab + entries[-1])
    sec_end = off + size
    print(f'{tag}: id=0x{sid:X} entriesA={nA} entriesB={nB} total={n_total} mono={mono} '
          f'f2=0x{f2:X} strpool=[0x{first_val:X}..0x{sec_end-tab:X}]')
    def show(idx_list, label):
        print(f'  {label}:')
        for i in idx_list:
            if 0 <= i < n_total:
                s, _ = decode_str(d, tab + entries[i])
                print(f'    [{i}] {s[:110]}')
    show([0, 1, 2, nA//2], 'A samples')
    # entries pointing into f2+ region (event texts)
    f2_rel = f2 + (off - tab)  # f2 is section-relative → table-relative
    idx_f2 = next((i for i, e in enumerate(entries) if e >= f2_rel), None)
    if idx_f2 is not None:
        show([idx_f2, idx_f2+1], f'first entries >= f2 (idx {idx_f2})')
    if nB > 0:
        show([nA, nA+2, nA+nB//2], 'B samples')

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
        print(f'section {i} @0x{off:X}: FAILED {type(e).__name__} {e}')
