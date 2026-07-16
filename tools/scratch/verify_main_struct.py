import struct, sys, hashlib
sys.stdout.reconfigure(encoding='utf-8')
SP = r'C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad'
v = open(SP + r'\main_patched', 'rb').read()
o = open(r'D:\nsw\rom\노부나가의 야망 신생_일본판\추출원본\exefs\main', 'rb').read()
assert v[:4] == b'NSO0'
segs = []
for i, base in enumerate((0x10, 0x20, 0x30)):
    fo, mo, ds = struct.unpack_from('<III', v, base)
    cs = struct.unpack_from('<I', v, 0x60 + i * 4)[0]
    segs.append((fo, mo, ds, cs))
    print(f'seg{i}: file_off=0x{fo:X} mem_off=0x{mo:X} dec=0x{ds:X} comp=0x{cs:X}')
pos = 0x100
for fo, mo, ds, cs in segs:
    assert fo == pos, f'gap {hex(fo)} != {hex(pos)}'
    assert fo + cs <= len(v)
    pos = fo + cs
print('module_id(build) same:', v[0x40:0x60] == o[0x40:0x60])
print('api/dynstr/dynsym extents same:', v[0x88:0xA0] == o[0x88:0xA0])
print('flags:', hex(struct.unpack_from('<I', v, 0xC)[0]))
print('STRUCTURE OK')
