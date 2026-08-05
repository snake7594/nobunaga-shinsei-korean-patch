# -*- coding: utf-8 -*-
"""번역 수정 일괄 적용 — data/ko 의 한국어 테이블을 규칙 파일대로 고친다.

두 가지 규칙을 지원한다.

  string : 문자열 전체가 old 와 정확히 같은 항목을 new 로 바꾼다.
           (긴 문장처럼 고유한 것에만 쓸 것)

  blob   : msggame 의 한 블록(런타임에 값과 번갈아 조립되는 조각 묶음)을 통째로 바꾼다.
           `old` 는 그 블록의 조각 배열과 정확히 일치해야 한다. '이', '들' 처럼 짧고
           흔한 조각을 안전하게 고치기 위한 방식이다.
           예) ["이", "에 입성"] -> [": ", "에 입성"]

블록 구조는 원본 게임 파일에서 읽으므로 --jp 가 필요하다(번역해도 조각 개수는 그대로).

  python tools/apply_text_fixes.py --data data/ko/puk_117 \
      --jp "<...>/Program 1/romfs/MSG_PK/JP" --fixes data/fixes/text_fixes.json [--dry]
"""
import sys, os, json, struct, argparse
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import apply_translations as A


def blob_spans(jp_msggame):
    """msggame 의 플랫 런 인덱스를 블록별로 끊어 [(start, count), ...] 로 돌려준다."""
    _, dec = A.kt_unwrap(open(jp_msggame, 'rb').read())
    cnt = struct.unpack_from('<I', dec, 0)[0]
    spans = []; k = 0
    for i in range(cnt):
        off, size = struct.unpack_from('<II', dec, 4 + i * 8)
        n = struct.unpack_from('<I', dec, off)[0]
        offs = struct.unpack_from(f'<{n}I', dec, off + 4); ends = list(offs[1:]) + [size]
        for j in range(n):
            blob = dec[off + offs[j]:off + ends[j]]; p = 0; c = 0
            while True:
                st = blob.find(b'\x07\x07\x01', p)
                if st < 0: break
                en = blob.find(b'\x07\x07\x02', st + 3)
                if en < 0: break
                c += 1            # ko_tables 와 동일하게 **모든 런**을 센다(홀수 길이는 None)
                p = en + 3
            if c:
                spans.append((k, c, (i, j))); k += c
    return spans


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--data', required=True, help='data/ko/<버전> 폴더')
    ap.add_argument('--jp', required=True, help='해당 버전의 원본 MSG 폴더')
    ap.add_argument('--fixes', required=True)
    ap.add_argument('--dry', action='store_true')
    a = ap.parse_args()

    fixes = [f for f in json.load(open(a.fixes, encoding='utf-8')) if f.get('kind')]  # "_" 주석 줄은 건너뜀
    tables = {}
    for f in sorted(os.listdir(a.data)):
        if f.endswith('.bin.json'):
            tables[f] = json.load(open(os.path.join(a.data, f), encoding='utf-8'))

    n_str = n_blob = 0
    # --- string 규칙 ---
    for fx in [f for f in fixes if f.get('kind') == 'string']:
        hit = 0
        for name, t in tables.items():
            if fx.get('file') and t['file'] != fx['file']:
                continue
            for i, v in enumerate(t['ko']):
                if v == fx['old']:
                    t['ko'][i] = fx['new']; hit += 1
        n_str += hit
        print(f"  [string] {hit}건  {fx['old'][:40]!r} -> {fx['new'][:40]!r}")
        if hit == 0:
            print('     ⚠ 일치 없음 — 이미 고쳐졌거나 이 버전엔 없는 문자열')

    # --- blob 규칙 ---
    blob_fixes = [f for f in fixes if f.get('kind') == 'blob']
    if blob_fixes:
        gname = 'msggame.bin.json'
        if gname not in tables:
            sys.exit('msggame 데이터가 없습니다')
        t = tables[gname]
        jp_path = os.path.join(a.jp, 'msggame.bin')
        spans = blob_spans(jp_path)
        # data/ko 는 원문과 같은 조각을 null 로 둔다 → 비교할 땐 원문을 채워 넣는다
        import ko_tables as KT
        _, _, jp_runs, _, _ = KT.read_file(jp_path)
        for fx in blob_fixes:
            old, new = fx['old'], fx['new']
            if len(old) != len(new):
                sys.exit(f'조각 개수는 바꿀 수 없습니다: {old} -> {new}')
            hit = 0
            for start, cnt, coord in spans:
                if cnt != len(old):
                    continue
                cur = [t['ko'][start + k] if t['ko'][start + k] is not None else jp_runs[start + k]
                       for k in range(cnt)]
                if cur == old:
                    t['ko'][start:start + cnt] = new
                    hit += 1
            n_blob += hit
            print(f'  [blob] {hit}건  {old} -> {new}')
            if hit == 0:
                print('     ⚠ 일치 없음')

    print(f'\n합계: string {n_str}건, blob {n_blob}건')
    if a.dry:
        print('(DRY-RUN — 저장하지 않음)')
        return
    for name, t in tables.items():
        json.dump(t, open(os.path.join(a.data, name), 'w', encoding='utf-8'), ensure_ascii=False)
    print(f'저장 완료 -> {a.data}')


if __name__ == '__main__':
    main()
