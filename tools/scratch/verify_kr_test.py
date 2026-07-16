import struct, sys
import lz4.block
sys.stdout.reconfigure(encoding='utf-8')

OUT = r'D:\nsw\rom\노부나가의 야망 신생_일본판\한글패치_테스트'

def kt_unwrap(blob):
    assert blob[0] == 1 and blob[1] == 1
    dec_size = struct.unpack_from('<Q', blob, 8)[0]
    comp_size = struct.unpack_from('<Q', blob, 16)[0]
    return lz4.block.decompress(blob[24:24 + comp_size], uncompressed_size=dec_size)

# --- 1) strdata ---
with open(OUT + r'\romfs\MSG\JP\strdata.bin', 'rb') as f:
    dec = kt_unwrap(f.read())
count = struct.unpack_from('<I', dec, 0)[0]
print(f'strdata: {count} sections')
ok = True
for i in range(count):
    off, size = struct.unpack_from('<II', dec, 4 + i * 8)
    n = struct.unpack_from('<I', dec, off + 8)[0] & 0xFFFF
    tab = off + 0x14
    entries = struct.unpack_from(f'<{n}I', dec, tab)
    mono = all(entries[k] <= entries[k+1] for k in range(n - 1))
    last_end = tab + entries[-1]
    while struct.unpack_from('<H', dec, last_end)[0] != 0:
        last_end += 2
    slack = off + size - (last_end + 2)
    ok &= mono and slack == 0
    print(f'  sec{i}: n={n} mono={mono} slack={slack}')
# show the replaced strings
off, _ = struct.unpack_from('<II', dec, 4 + 1 * 8)
tab = off + 0x14
entries = struct.unpack_from('<8I', dec, tab)
for j in (0, 1, 2, 3):
    pos = tab + entries[j]
    end = pos
    while struct.unpack_from('<H', dec, end)[0] != 0:
        end += 2
    print(f'  sec1[{j}] = "{dec[pos:end].decode("utf-16-le")}"')

# --- 2) res_lang / fonts ---
with open(OUT + r'\romfs\RES_JP\res_lang.bin', 'rb') as f:
    res = f.read()
lcount, ver = struct.unpack_from('<II', res, 4)
print(f'\nres_lang: {lcount} entries ver={ver}')
RAMP = ' .:-=+*#%@'
for idx in (6, 7):
    off, size = struct.unpack_from('<II', res, 16 + idx * 8)
    g1n = kt_unwrap(res[off:off + size])
    assert g1n[:4] == b'_N1G', 'bad magic'
    pool = struct.unpack_from('<I', g1n, 0x14)[0]
    secs = [struct.unpack_from('<I', g1n, 0x20 + 4 * i)[0] for i in range(struct.unpack_from('<I', g1n, 0x1C)[0])]
    print(f'entry {idx}: g1n {len(g1n):,} bytes, sections={[hex(s) for s in secs]}')
    for si, label in ((0, 'regular'), (1, 'bold')):
        s = secs[si]
        line = []
        for ch in '처음부터이어하기':
            gid = struct.unpack_from('<H', g1n, s + ord(ch) * 2)[0]
            line.append(f'{ch}={gid}')
        print(f'  sec{si} ({label}) charmap: {" ".join(line)}')
    # render 처 from section 0
    s = secs[0]
    gid = struct.unpack_from('<H', g1n, s + ord('처') * 2)[0]
    rec = s + 0x20000 + gid * 12
    w, h = g1n[rec], g1n[rec + 1]
    bmp = pool + struct.unpack_from('<I', g1n, rec + 8)[0]
    print(f'  render 처 (sec0, {w}x{h}):')
    for y in range(0, h, 2 if h > 24 else 1):  # subsample tall cells for compact output
        row = ''
        for x in range(w):
            i2 = y * w + x
            b = g1n[bmp + i2 // 2]
            v = (b & 0xF) if i2 % 2 == 0 else (b >> 4)
            row += RAMP[v * (len(RAMP) - 1) // 15]
        print('   ' + row)
print('\nALL OK' if ok else 'PROBLEMS FOUND')
