import re, sys

keywords = [b'font', b'ttf', b'otf', b'ttc', b'bffnt', b'glyph',
            b'nn::pl', b'pl:u', b'Seurat', b'gothic', b'mincho', b'typeface']

def scan(d, tag):
    out = []
    # ASCII
    for m in re.finditer(rb'[\x20-\x7e]{4,}', d):
        s = m.group()
        low = s.lower()
        if any(k in low for k in keywords):
            out.append((m.start(), 'A', s.decode('ascii', 'replace')))
    # UTF-16LE
    for m in re.finditer(rb'(?:[\x20-\x7e]\x00){4,}', d):
        s = m.group().decode('utf-16-le', 'replace')
        low = s.lower().encode()
        if any(k in low for k in keywords):
            out.append((m.start(), 'W', s))
    for off, kind, s in out:
        print(f'{tag}  0x{off:08X} {kind}  {s}')
    return len(out)

total = 0
for path in sys.argv[1:]:
    tag = path.split('\\')[-1].replace('_dec.bin', '')
    with open(path, 'rb') as f:
        d = f.read()
    total += scan(d, tag)
print(f'-- total {total} --', file=sys.stderr)
