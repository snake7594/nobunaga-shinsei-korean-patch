# -*- coding: utf-8 -*-
"""폰트 글리프 커버리지 감사 — 게임에 실제로 표시되는 문자 중 **폰트에 글리프가 없어
화면에서 깨지는 문자**를 찾는다.

한글패치는 폰트의 '안 쓰는 일본어 글리프' 자리를 한글로 재활용하는데, 그 판단을 옛
게임 버전 텍스트로 하면 새 버전에서 추가된 문자(버튼 아이콘 등)가 깨진다. 릴리스 전
반드시 돌릴 것.

  python tools/audit_glyphs.py --res <res_lang(_pk).bin> --entry 16 --msg <한글화된 MSG 폴더>
"""
import sys, os, re, struct, argparse
import numpy as np, lz4.block
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import apply_translations as A


def kt_dec(b):
    dec = struct.unpack_from('<Q', b, 8)[0]; comp = struct.unpack_from('<Q', b, 16)[0]
    return lz4.block.decompress(b[24:24 + comp], uncompressed_size=dec)


def font_glyphs(res_path, entry):
    d = open(res_path, 'rb').read()
    o, s = struct.unpack_from('<II', d, 16 + entry * 8)
    g = kt_dec(d[o:o + s])
    if g[:8] != b'_N1G0000':
        sys.exit(f'엔트리 {entry}는 G1N 폰트가 아닙니다 ({g[:8]!r})')
    secs = list(struct.unpack_from('<3I', g, 0x20))
    cm = np.frombuffer(g, dtype='<u2', count=65536, offset=secs[0])
    return {cp for cp in range(0x10000) if int(cm[cp])}


def strings_of(path):
    hdr, dec = A.kt_unwrap(open(path, 'rb').read())
    if os.path.basename(path) == 'msggame.bin':
        out = []
        cnt = struct.unpack_from('<I', dec, 0)[0]
        for i in range(cnt):
            off, size = struct.unpack_from('<II', dec, 4 + i * 8)
            n = struct.unpack_from('<I', dec, off)[0]
            offs = struct.unpack_from(f'<{n}I', dec, off + 4); ends = list(offs[1:]) + [size]
            for j in range(n):
                blob = dec[off + offs[j]:off + ends[j]]; p = 0
                while True:
                    st = blob.find(b'\x07\x07\x01', p)
                    if st < 0: break
                    en = blob.find(b'\x07\x07\x02', st + 3)
                    if en < 0: break
                    raw = blob[st + 3:en]
                    if len(raw) % 2 == 0 and raw:
                        out.append(((i, j), A.esc(struct.unpack_from(f'<{len(raw)//2}H', raw))))
                    p = en + 3
        return out
    return list(enumerate(s for sec in A.read_strtable_raw(dec) for s in sec))


ESC = re.compile(r'<ESC>C.')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--res', required=True, help='폰트가 든 res_lang(_pk).bin')
    ap.add_argument('--entry', type=int, default=16, help='폰트 엔트리 번호 (PUK 16, 기본판 6)')
    ap.add_argument('--msg', required=True, nargs='+', help='검사할 MSG 폴더(들)')
    a = ap.parse_args()

    have = font_glyphs(a.res, a.entry)
    print(f'폰트 글리프: {len(have):,}  ({os.path.basename(a.res)} entry {a.entry})')

    from collections import Counter
    missing = Counter(); where = {}
    total = 0
    for d in a.msg:
        for f in sorted(os.listdir(d)):
            if not f.endswith('.bin'):
                continue
            for key, t in strings_of(os.path.join(d, f)):
                total += 1
                for ch in ESC.sub('', t).replace('\\n', '').replace('\\t', ''):
                    cp = ord(ch)
                    if cp < 0x20 or cp in have:
                        continue
                    missing[ch] += 1
                    where.setdefault(ch, (f, key, t[:70]))
    print(f'검사 문자열: {total:,}')
    if not missing:
        print('\n✅ 깨지는 문자 없음')
        return 0
    print(f'\n❌ 폰트에 없는 문자 {len(missing)}종 (총 {sum(missing.values())}회)')
    for ch, n in missing.most_common():
        f, key, t = where[ch]
        print(f'  {ch!r} U+{ord(ch):04X}  {n:5d}회  예: {f} {key} | {t}')
    return 1


if __name__ == '__main__':
    sys.exit(main())
