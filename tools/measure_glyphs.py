"""Measure ink metrics of original kanji glyphs vs our Hangul renders."""
import struct, sys
sys.stdout.reconfigure(encoding='utf-8')

def get_glyph(d, sec, ch, pool):
    gid = struct.unpack_from('<H', d, sec + ord(ch) * 2)[0]
    if gid == 0:
        return None
    rec = sec + 0x20000 + gid * 12
    w, h = d[rec], d[rec + 1]
    metrics = d[rec:rec+8]
    off = struct.unpack_from('<I', d, rec + 8)[0]
    base = pool + off
    pix = []
    for y in range(h):
        row = []
        for x in range(w):
            i = y * w + x
            b = d[base + i // 2]
            row.append((b & 0xF) if i % 2 == 0 else (b >> 4))
        pix.append(row)
    return w, h, pix, metrics

def ink_stats(w, h, pix, thresh=4):
    xs = [x for y in range(h) for x in range(w) if pix[y][x] >= thresh]
    ys = [y for y in range(h) for x in range(w) if pix[y][x] >= thresh]
    if not xs:
        return None
    bx = (min(xs), max(xs), min(ys), max(ys))
    # stroke width: mean horizontal run length of ink
    runs = []
    for y in range(h):
        run = 0
        for x in range(w):
            if pix[y][x] >= thresh:
                run += 1
            elif run:
                runs.append(run); run = 0
        if run: runs.append(run)
    coverage = len(xs) / (w * h)
    mean_run = sum(runs) / len(runs) if runs else 0
    return bx, coverage, mean_run

for path, tag in [(sys.argv[1], 'orig'), (sys.argv[2], 'patched')]:
    with open(path, 'rb') as f:
        d = f.read()
    pool = struct.unpack_from('<I', d, 0x14)[0]
    nsec = struct.unpack_from('<I', d, 0x1C)[0]
    secs = [struct.unpack_from('<I', d, 0x20 + 4 * i)[0] for i in range(nsec)]
    chars = '登録設鑑' if tag == 'orig' else '처음부터'
    for si in (0, 1):
        for ch in chars:
            g = get_glyph(d, secs[si], ch, pool)
            if not g:
                continue
            w, h, pix, m = g
            st = ink_stats(w, h, pix)
            if st:
                (x0, x1, y0, y1), cov, run = st
                print(f'{tag} sec{si} {ch}: cell{w} ink x[{x0}..{x1}]({x1-x0+1}) y[{y0}..{y1}]({y1-y0+1}) '
                      f'cov={cov:.2%} stroke~{run:.1f}px metrics={m.hex(" ")}')
