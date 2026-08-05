# -*- coding: utf-8 -*-
"""한국어 입력 우회를 **이름 입력 화면 전체**로 확장한다 (1.1.7 PUK main).

이슈 #1의 원본 패치는 이름 입력 화면 중 **한 곳(신규 무장 등록)만** 우회했다. 게임에는
같은 로직이 복제된 화면이 더 있어서, 공주가 성인이 되어 이름을 정할 때처럼 다른 화면에서는
한글이 입력은 되지만 검증에 걸려 진행이 안 된다.

각 이름 입력 화면은 아래 두 곳을 갖는다(구조가 동일하다).

  ① csel wX, wA(#6), wB(#0x1c), eq   ← 입력 가능 최대 글자수: 가나 6 / 전체 28
     → mov wX, #0x1c 로 고정해 한글 이름 길이를 확보

  ② bl <검증함수 0x1330a80> ; cbz w0, <실패> ; tbz wY,#0, <길이검사>
     → tbz 를 무조건 분기(b)로 바꿔 **독음(가나) 검사 루프를 건너뛰고** 길이검사로 직행

원본 패치가 화면 A(0x113e908 / 0x113ea28)에 한 것과 동일한 처리를, 공주 이름 화면
D(0x15c7754 / 0x15c7ad0)에도 적용한다.

  IN=<한글패치된 main>  OUT=<결과>  python patch_hangul_kbd_extra.py
"""
import sys, os, struct, hashlib
import lz4.block
sys.stdout.reconfigure(encoding='utf-8')

IN = os.environ.get('IN')
OUT = os.environ.get('OUT')
if not (IN and OUT):
    sys.exit('IN, OUT 환경변수가 필요합니다')

# (주소, 원본 워드, 새 워드, 설명)  — 원본 워드가 다르면 중단한다(버전 오적용 방지)
PATCHES = [
    (0x15c7754, 0x1A880136, 0x52800396,
     '공주 이름: 최대 글자수 6/28 선택 -> 28 고정 (csel w22,w9,w8,eq -> mov w22,#0x1c)'),
    (0x15c7ad0, 0x36000918, 0x14000048,
     '공주 이름: 독음(가나) 검사 건너뛰고 길이검사로 (tbz w24,#0,#0x15c7bf0 -> b #0x15c7bf0)'),
]


def parse_nso(d):
    flags = struct.unpack_from('<I', d, 0x0C)[0]
    segs = []
    for i, base in enumerate((0x10, 0x20, 0x30)):
        file_off, mem_off, dec_size = struct.unpack_from('<III', d, base)
        comp_size = struct.unpack_from('<I', d, 0x60 + i * 4)[0]
        segs.append(dict(file_off=file_off, mem_off=mem_off, dec_size=dec_size,
                         comp_size=comp_size, compressed=bool(flags & (1 << i))))
    return flags, segs


def decompress_seg(d, s):
    blob = d[s['file_off']:s['file_off'] + (s['comp_size'] if s['compressed'] else s['dec_size'])]
    return lz4.block.decompress(blob, uncompressed_size=s['dec_size']) if s['compressed'] else blob


orig = open(IN, 'rb').read()
assert orig[:4] == b'NSO0', 'NSO0 가 아닙니다'
flags, segs = parse_nso(orig)
raw = [bytearray(decompress_seg(orig, s)) for s in segs]
text = raw[0]
print(f'.text {len(text):,} bytes')

for addr, old, new, desc in PATCHES:
    cur = struct.unpack_from('<I', text, addr)[0]
    if cur == new:
        print(f'  이미 적용됨: {desc}')
        continue
    if cur != old:
        sys.exit(f'중단 — {addr:#x} 의 명령이 예상과 다릅니다 '
                 f'(기대 {old:08X}, 실제 {cur:08X}). 게임 버전이 다를 수 있습니다.')
    struct.pack_into('<I', text, addr, new)
    print(f'  적용: {addr:#x}  {old:08X} -> {new:08X}   {desc}')

new_raw = [bytes(text), bytes(raw[1]), bytes(raw[2])]

# ---- NSO0 재조립 (세그먼트 해시·압축크기 갱신) ----
out = bytearray(orig[:0x100])
cursor = 0x100
for i, (s, seg) in enumerate(zip(segs, new_raw)):
    h = hashlib.sha256(seg).digest()
    comp = lz4.block.compress(seg, mode='high_compression', compression=12,
                              store_size=False) if s['compressed'] else seg
    struct.pack_into('<I', out, 0x10 + i * 0x10, cursor)
    struct.pack_into('<I', out, 0x60 + i * 4, len(comp))
    out[0xA0 + i * 0x20:0xA0 + i * 0x20 + 0x20] = h
    while len(out) < cursor:
        out += b'\x00'
    out += comp
    cursor += len(comp)

open(OUT, 'wb').write(out)
print(f'\n저장: {OUT}  {len(orig):,} -> {len(out):,} bytes')

# ---- 검증 ----
v = open(OUT, 'rb').read()
vflags, vsegs = parse_nso(v)
vraw = [decompress_seg(v, s) for s in vsegs]
for i in range(3):
    assert vraw[i] == new_raw[i], f'세그먼트 {i} 불일치'
    assert hashlib.sha256(vraw[i]).digest() == v[0xA0 + i * 0x20:0xA0 + i * 0x20 + 0x20], f'해시 {i}'
for addr, old, new, desc in PATCHES:
    assert struct.unpack_from('<I', vraw[0], addr)[0] == new, f'패치 미반영 {addr:#x}'
print('검증 통과: 세그먼트 해시·패치 반영 모두 정상')
