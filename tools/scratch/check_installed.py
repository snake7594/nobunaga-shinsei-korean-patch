"""Check the INSTALLED translated strdata for any remaining wheel kanji (as substrings),
and dump every string containing them with section/index."""
import struct, sys, lz4.block
sys.stdout.reconfigure(encoding='utf-8')

def unwrap(b):
    return lz4.block.decompress(b[24:24 + struct.unpack_from('<Q', b, 16)[0]],
                                uncompressed_size=struct.unpack_from('<Q', b, 8)[0])

def read_sections(path):
    d = unwrap(open(path, 'rb').read())
    count = struct.unpack_from('<I', d, 0)[0]
    secs = []
    for i in range(count):
        off, size = struct.unpack_from('<II', d, 4 + i * 8)
        n = struct.unpack_from('<I', d, off + 8)[0] & 0xFFFF
        tab = off + 0x14
        entries = struct.unpack_from(f'<{n}I', d, tab)
        strs = []
        for e in entries:
            pos = tab + e
            cus = []
            while True:
                cu = struct.unpack_from('<H', d, pos)[0]
                pos += 2
                if cu == 0:
                    break
                cus.append(cu)
            strs.append(''.join(chr(c) for c in cus))
        secs.append(strs)
    return secs

WHEEL = ['評定', '内政', '任命', '軍事', '外交']
def has_jp_kanji(s):
    return any(0x3040 <= ord(c) <= 0x30FF or 0x3400 <= ord(c) <= 0x9FFF for c in s)

INST = r'C:\Users\Jay\AppData\Roaming\Ryujinx\mods\contents\01007ab012872000\romfs\MSG\JP\strdata.bin'
secs = read_sections(INST)
print(f'INSTALLED strdata: {len(secs)} sections, sizes {[len(s) for s in secs]}')

# any string still containing wheel kanji?
total_jp = 0
for si, strs in enumerate(secs):
    for j, s in enumerate(strs):
        for w in WHEEL:
            if w in s:
                total_jp += 1
                if total_jp <= 40:
                    print(f'  sec{si}[{j}] contains {w}: {s[:50]!r}')
                break
print(f'\nstrings still containing wheel kanji: {total_jp}')

# also: how many strings still have ANY Japanese kanji/kana at all?
any_jp = sum(1 for strs in secs for s in strs if has_jp_kanji(s))
print(f'strings with ANY CJK/kana remaining: {any_jp} / {sum(len(s) for s in secs)}')
