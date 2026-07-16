import struct, sys
import lz4.block
from PIL import Image
sys.stdout.reconfigure(encoding='utf-8')

OUT = r'D:\nsw\rom\노부나가의 야망 신생_일본판\한글패치_테스트'
SP = sys.argv[1]

def kt_unwrap(blob):
    dec_size = struct.unpack_from('<Q', blob, 8)[0]
    comp_size = struct.unpack_from('<Q', blob, 16)[0]
    return lz4.block.decompress(blob[24:24 + comp_size], uncompressed_size=dec_size)

# --- strdata checks ---
with open(OUT + r'\romfs\MSG\JP\strdata.bin', 'rb') as f:
    dec = kt_unwrap(f.read())
count = struct.unpack_from('<I', dec, 0)[0]
all_ok = True
for i in range(count):
    off, size = struct.unpack_from('<II', dec, 4 + i * 8)
    sid, f1, f2, f3, f4 = struct.unpack_from('<5I', dec, off)
    n = f2 & 0xFFFF
    ok = (sid == 0x134C58 and f3 == 0x14 and f4 == 0xFFFFFF00
          and f1 == (0x10000 | (size & 0xFFFF)) and (f2 >> 16) == 4)
    tab = off + 0x14
    entries = struct.unpack_from(f'<{n}I', dec, tab)
    mono = all(entries[k] <= entries[k + 1] for k in range(n - 1))
    all_ok &= ok and mono
    print(f'strdata sec{i}: n={n} hdr_ok={ok} mono={mono}')
off = struct.unpack_from('<II', dec, 4 + 1 * 8)[0]
tab = off + 0x14
entries = struct.unpack_from(f'<{struct.unpack_from("<I", dec, off + 8)[0] & 0xFFFF}I', dec, tab)
def read_s(j):
    pos = tab + entries[j]
    end = pos
    while struct.unpack_from('<H', dec, end)[0] != 0:
        end += 2
    return dec[pos:end].decode('utf-16-le')
for j in (1, 2, 3, 86, 87, 88, 97):
    print(f'  sec1[{j}] = "{read_s(j)}"')

# --- font: measure + compose preview image ---
with open(OUT + r'\romfs\RES_JP\res_lang.bin', 'rb') as f:
    res = f.read()
off, size = struct.unpack_from('<II', res, 16 + 6 * 8)
g1n = kt_unwrap(res[off:off + size])
pool = struct.unpack_from('<I', g1n, 0x14)[0]
secs = [struct.unpack_from('<I', g1n, 0x20 + 4 * i)[0] for i in range(3)]

def glyph_img(sec, ch):
    gid = struct.unpack_from('<H', g1n, sec + ord(ch) * 2)[0]
    if gid == 0:
        return None
    rec = sec + 0x20000 + gid * 12
    w, h = g1n[rec], g1n[rec + 1]
    base = pool + struct.unpack_from('<I', g1n, rec + 8)[0]
    img = Image.new('L', (w, h), 0)
    p = img.load()
    for y in range(h):
        for x in range(w):
            i = y * w + x
            b = g1n[base + i // 2]
            p[x, y] = ((b >> 4) if i % 2 == 0 else (b & 0xF)) * 17  # even pixel = high nibble
    return img

def ink_stats(img):
    w, h = img.size
    p = img.load()
    xs = [x for y in range(h) for x in range(w) if p[x, y] >= 68]
    ys = [y for y in range(h) for x in range(w) if p[x, y] >= 68]
    runs = []
    for y in range(h):
        run = 0
        for x in range(w):
            if p[x, y] >= 68:
                run += 1
            elif run:
                runs.append(run); run = 0
        if run: runs.append(run)
    return (max(xs) - min(xs) + 1, max(ys) - min(ys) + 1, min(ys),
            sum(runs) / len(runs) if runs else 0)

print('\nink metrics (patched, 48px):')
for si in (0, 1):
    for ch in '처음등텐':
        w, hh, y0, run = ink_stats(glyph_img(secs[si], ch))
        print(f'  sec{si} {ch}: ink {w}x{hh} y0={y0} stroke~{run:.1f}px')
for ch in '登録':
    w, hh, y0, run = ink_stats(glyph_img(secs[0], ch))
    print(f'  sec0 kanji {ch}: ink {w}x{hh} y0={y0} stroke~{run:.1f}px')

# preview sheet: menu lines in sec0 and sec1
lines = ['처음부터', '등록무장편집', '추가 콘텐츠', '감상 설정 라이선스 튜토리얼', '登録武将編集設定']
cellh = 48
sheet = Image.new('L', (48 * 14, cellh * len(lines) * 2 + 20), 0)
for row, si in enumerate((0, 1)):
    for li, line in enumerate(lines):
        x = 0
        y = (row * len(lines) + li) * cellh + row * 20
        for ch in line:
            if ch == ' ':
                x += 20
                continue
            gi = glyph_img(secs[si], ch)
            if gi:
                sheet.paste(gi, (x, y))
            x += gi.size[0] + 2 if gi else 24
sheet = sheet.point(lambda v: 255 - v)  # black on white for viewing
sheet.save(SP + r'\preview_v2.png')
print(f'\npreview saved, ALL_OK={all_ok}')
