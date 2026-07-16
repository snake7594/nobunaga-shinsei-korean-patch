import re, sys

path = sys.argv[1]
with open(path, 'rb') as f:
    d = f.read()

# ASCII strings of length >= 4
pat = re.compile(rb'[\x20-\x7e]{4,}')

keywords = [b'font', b'Font', b'FONT', b'.ttf', b'.otf', b'.ttc', b'bfttf', b'bffnt',
            b'nn::pl', b'pl:u', b'pl:s', b'Nintendo', b'Yu Gothic', b'FOT-', b'Seurat',
            b'gothic', b'Gothic', b'mincho', b'Mincho']

seen = set()
results = []
for m in pat.finditer(d):
    s = m.group()
    if any(k in s for k in keywords):
        if s not in seen:
            seen.add(s)
            results.append((m.start(), s))

for off, s in results:
    try:
        txt = s.decode('ascii')
    except UnicodeDecodeError:
        continue
    print(f'0x{off:08X}  {txt}')
print(f'-- {len(results)} unique matches --', file=sys.stderr)
