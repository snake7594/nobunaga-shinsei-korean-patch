import struct, sys
sys.stdout.reconfigure(encoding='utf-8')

path = sys.argv[1]
sec_list = [int(x) for x in sys.argv[2].split(',')]
with open(path, 'rb') as f:
    d = f.read()

for si in sec_list:
    off, size = struct.unpack_from('<II', d, 4 + si*8)
    n = struct.unpack_from('<I', d, off)[0]
    offs = struct.unpack_from(f'<{n}I', d, off + 4)
    print(f'== section {si}: n={n} ==')
    ends = list(offs[1:]) + [size]
    for k in list(range(min(5, n))) + ([n//2, n-1] if n > 6 else []):
        s, e = offs[k], ends[k]
        blob = d[off+s:off+e]
        hx = ' '.join(f'{b:02x}' for b in blob[:48])
        print(f'  [{k}] +0x{s:X} len={e-s}')
        print(f'      {hx}')
        # try utf16 decode from various starts
        for skip in (0, 1, 2, 3):
            if (len(blob) - skip) >= 2 and (s + skip) % 2 == 0 or skip in (1, 3):
                try:
                    t = blob[skip:].decode('utf-16-le', 'ignore')[:40]
                    t = ''.join(c if c.isprintable() else f'⌁' for c in t).rstrip('⌁')
                    if t and any('　' <= c <= '￯' or c.isalnum() for c in t):
                        print(f'      u16@{skip}: {t}')
                        break
                except Exception:
                    pass
    print()
