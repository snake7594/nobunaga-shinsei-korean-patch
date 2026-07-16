import struct, sys
sys.stdout.reconfigure(encoding='utf-8')

def decode_str(d, pos):
    out = []
    while pos + 1 < len(d):
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

def verify(path):
    with open(path, 'rb') as f:
        d = f.read()
    count = struct.unpack_from('<I', d, 0)[0]
    name = path.split('\\')[-1]
    print(f'=== {name}: {count} sections ===')
    total_strings = 0
    for i in range(count):
        off, size = struct.unpack_from('<II', d, 4 + i*8)
        sid, f1, f2, f3, f4 = struct.unpack_from('<5I', d, off)
        n = f2 & 0xFFFF
        f2_hi = f2 >> 16
        assert f2_hi == 4, f'sec{i}: f2 high = {f2_hi}'
        assert f3 == 0x14, f'sec{i}: f3 = {f3:#x}'
        assert sid == 0x134C58 and f4 == 0xFFFFFF00
        assert (f1 >> 16) == 1 and (f1 & 0xFFFF) == (size & 0xFFFF), f'sec{i}: f1 pattern'
        tab = off + f3
        entries = struct.unpack_from(f'<{n}I', d, tab)
        mono = all(entries[k] <= entries[k+1] for k in range(n-1))
        tight = entries[0] == 4 * n if n else True
        # decode ALL strings, verify pool consumed exactly
        pos = tab + entries[0] if n else tab
        last_end = pos
        ok = True
        for e in entries:
            s, end = decode_str(d, tab + e)
            last_end = max(last_end, end)
        sec_end = off + size
        slack = sec_end - last_end
        total_strings += n
        s0, _ = decode_str(d, tab + entries[0]) if n else ('', 0)
        print(f'[{i:2}] n={n:6} mono={mono} tight={tight} slack_at_end={slack}  first="{s0[:40]}"')
    print(f'TOTAL strings: {total_strings}\n')

for p in sys.argv[1:]:
    verify(p)
