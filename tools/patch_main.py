"""Patch exefs/main (NSO0): replace hardcoded JP system strings with Korean (in-place,
byte-length-bounded), recompress segments, recompute SHA256 hashes, rebuild NSO0, verify."""
import struct, sys, os, hashlib
import lz4.block
sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))
SRC_MAIN = r'D:\nsw\merged_exefs\main'   # 1.1.4 merged main (was base — WRONG)
OUT_MAIN = os.path.join(SP, 'main_patched')

# JP original -> Korean (Korean UTF-16 byte length must be <= JP; null-padded)
PATCHES = {
    "イベントデータが不正です：'%04d.bin' (ResID:%d)": "이벤트 데이터 오류：'%04d.bin' (ResID:%d)",
    "チュートリアルを行いますか?": "튜토리얼을 진행할까요?",
    "グラフィックライブラリ初期化エラー2": "그래픽 라이브러리 초기화 오류2",
    "マイドキュメントの取得に失敗": "내 문서 폴더 접근 실패",
    "ダウンロードコンテンツが見つかりません": "다운로드 콘텐츠를 찾을 수 없음",
    "セーブデータが壊れています": "세이브 데이터가 손상됨",
}

def parse_nso(d):
    assert d[:4] == b'NSO0'
    flags = struct.unpack_from('<I', d, 0x0C)[0]
    segs = []
    for i, base in enumerate((0x10, 0x20, 0x30)):
        file_off, mem_off, dec_size = struct.unpack_from('<III', d, base)
        comp_size = struct.unpack_from('<I', d, 0x60 + i * 4)[0]
        segs.append(dict(file_off=file_off, mem_off=mem_off, dec_size=dec_size,
                         comp_size=comp_size, compressed=bool(flags & (1 << i)),
                         check_hash=bool(flags & (1 << (i + 3)))))
    return flags, segs

def decompress_seg(d, s):
    blob = d[s['file_off']:s['file_off'] + (s['comp_size'] if s['compressed'] else s['dec_size'])]
    if s['compressed']:
        blob = lz4.block.decompress(blob, uncompressed_size=s['dec_size'])
    assert len(blob) == s['dec_size']
    return blob

with open(SRC_MAIN, 'rb') as f:
    orig = f.read()
flags, segs = parse_nso(orig)
raw = [decompress_seg(orig, s) for s in segs]   # [text, rodata, data]
text, rodata, data = raw[0], bytearray(raw[1]), raw[2]

# ---- apply string patches to rodata ----
patched = 0
for jp, ko in PATCHES.items():
    jb = jp.encode('utf-16-le')
    kb = ko.encode('utf-16-le')
    assert len(kb) <= len(jb), f'Korean too long: {ko} ({len(kb)} > {len(jb)})'
    repl = kb + b'\x00' * (len(jb) - len(kb))   # pad to same length, keep null terminator area
    idx = rodata.find(jb)
    assert idx != -1, f'not found: {jp}'
    # ensure single JP occurrence (SC/TC copies are different bytes)
    assert rodata.find(jb, idx + 2) == -1, f'multiple occurrences: {jp}'
    rodata[idx:idx + len(jb)] = repl
    patched += 1
    print(f'  patched: {jp[:24]}... -> {ko}')
print(f'{patched} strings patched in .rodata')
rodata = bytes(rodata)
new_raw = [text, rodata, data]

# ---- rebuild NSO0 ----
out = bytearray(orig[:0x100])   # keep header skeleton (module id, api extents, etc.)
cursor = 0x100
for i, (s, seg) in enumerate(zip(segs, new_raw)):
    h = hashlib.sha256(seg).digest()
    comp = lz4.block.compress(seg, mode='high_compression', compression=12, store_size=False) if s['compressed'] else seg
    struct.pack_into('<I', out, 0x10 + i * 0x10, cursor)          # file_off
    # mem_off (0x14) and dec_size (0x18) unchanged
    struct.pack_into('<I', out, 0x60 + i * 4, len(comp))          # compressed size
    out[0xA0 + i * 0x20:0xA0 + i * 0x20 + 0x20] = h               # segment hash
    # append
    while len(out) < cursor:
        out += b'\x00'
    out += comp
    cursor += len(comp)

with open(OUT_MAIN, 'wb') as f:
    f.write(out)
print(f'wrote {OUT_MAIN}: {len(orig):,} -> {len(out):,} bytes')

# ---- verify: reparse, decompress, compare to intended ----
v = open(OUT_MAIN, 'rb').read()
vflags, vsegs = parse_nso(v)
vraw = [decompress_seg(v, s) for s in vsegs]
assert vraw[0] == text, 'text mismatch'
assert vraw[1] == rodata, 'rodata mismatch'
assert vraw[2] == data, 'data mismatch'
for i, s in enumerate(vsegs):
    assert hashlib.sha256(vraw[i]).digest() == v[0xA0 + i * 0x20:0xA0 + i * 0x20 + 0x20], f'hash{i}'
# confirm Korean present, JP gone
for jp, ko in PATCHES.items():
    assert vraw[1].find(jp.encode('utf-16-le')) == -1, f'JP remains: {jp}'
    assert vraw[1].find(ko.encode('utf-16-le')) != -1, f'KO missing: {ko}'
print('VERIFY OK: segments roundtrip, hashes valid, JP->KO confirmed')
