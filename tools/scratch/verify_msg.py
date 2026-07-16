import struct, sys, re
import lz4.block
sys.stdout.reconfigure(encoding='utf-8')

OUT = r'D:\nsw\rom\노부나가의 야망 신생_일본판\한글패치_테스트\romfs\MSG\JP'

def kt_unwrap(blob):
    dec_size = struct.unpack_from('<Q', blob, 8)[0]
    comp_size = struct.unpack_from('<Q', blob, 16)[0]
    return lz4.block.decompress(blob[24:24 + comp_size], uncompressed_size=dec_size)

def check_strtable(name):
    with open(f'{OUT}\\{name}', 'rb') as f:
        d = kt_unwrap(f.read())
    count = struct.unpack_from('<I', d, 0)[0]
    total = 0
    ko = 0
    for i in range(count):
        off, size = struct.unpack_from('<II', d, 4 + i * 8)
        sid, f1, f2, f3, f4 = struct.unpack_from('<5I', d, off)
        assert sid == 0x134C58 and f3 == 0x14 and f4 == 0xFFFFFF00
        assert f1 == (0x10000 | (size & 0xFFFF)), f'{name} sec{i} f1'
        assert (f2 >> 16) == 4
        n = f2 & 0xFFFF
        tab = off + 0x14
        entries = struct.unpack_from(f'<{n}I', d, tab)
        assert all(entries[k] <= entries[k+1] for k in range(n-1)), f'{name} sec{i} not mono'
        # decode last string ends within section
        last = tab + entries[-1]
        while struct.unpack_from('<H', d, last)[0] != 0:
            last += 2
        assert last + 2 <= off + size
        total += n
        for e in entries:
            pos = tab + e
            cus = []
            while True:
                cu = struct.unpack_from('<H', d, pos)[0]
                pos += 2
                if cu == 0: break
                cus.append(cu)
            if any(0xAC00 <= c <= 0xD7A3 for c in cus):
                ko += 1
    print(f'{name}: {count} sections, {total} strings, {ko} contain Hangul  [OK]')

def check_msggame(name):
    with open(f'{OUT}\\{name}', 'rb') as f:
        d = kt_unwrap(f.read())
    count = struct.unpack_from('<I', d, 0)[0]
    ko = 0
    entries = 0
    for i in range(count):
        off, size = struct.unpack_from('<II', d, 4 + i*8)
        n = struct.unpack_from('<I', d, off)[0]
        offs = struct.unpack_from(f'<{n}I', d, off + 4)
        assert all(offs[k] <= offs[k+1] for k in range(n-1)), f'{name} sec{i} not mono'
        ends = list(offs[1:]) + [size]
        for j in range(n):
            blob = d[off+offs[j]:off+ends[j]]
            entries += 1
            p = 0
            while True:
                st = blob.find(b'\x07\x07\x01', p)
                if st < 0: break
                en = blob.find(b'\x07\x07\x02', st+3)
                if en < 0: break
                raw = blob[st+3:en]
                if len(raw) % 2 == 0:
                    cus = struct.unpack_from(f'<{len(raw)//2}H', raw)
                    if any(0xAC00 <= c <= 0xD7A3 for c in cus):
                        ko += 1
                p = en + 3
    print(f'{name}: {count} sections, {entries} entries, {ko} text-runs contain Hangul  [OK]')

check_strtable('strdata.bin')
check_strtable('ev_strdata.bin')
check_msggame('msggame.bin')
print('\nALL MSG FILES VALID')
