# -*- coding: utf-8 -*-
"""한국어 문자열 테이블 — 내보내기/적용 (저장소 단독 재현용)

이 저장소는 **게임 원본 텍스트를 담지 않습니다.** 대신 "몇 번째 문자열을 어떤 한국어로
바꿀지"만 인덱스 기준으로 담고(`data/ko/<버전>/*.json`), 적용할 때 **사용자 본인이 덤프한
게임 파일**을 읽어 해당 인덱스만 교체합니다. 번역하지 않은 항목은 `null`이라 원문 그대로
남습니다.

지원 포맷
  strtable : strdata/ev_strdata/msg*.bin — 섹션별 문자열 테이블
  msggame  : msggame.bin — 07 07 01 … 07 07 02 마커로 구분된 텍스트 런

사용법
  python ko_tables.py export --jp <원본디렉터리> --ko <한글화된디렉터리> --out <data디렉터리>
  python ko_tables.py apply  --jp <원본디렉터리> --data <data디렉터리> --out <출력디렉터리>
"""
import os, sys, json, struct, argparse, hashlib
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import apply_translations as A

MSGGAME = 'msggame.bin'


# ---------- 읽기 ----------
def read_file(path):
    """(kind, sections, strings) 반환. sections = 섹션별 문자열 개수."""
    hdr, dec = A.kt_unwrap(open(path, 'rb').read())
    if os.path.basename(path) == MSGGAME:
        return 'msggame', None, _read_msggame(dec), hdr, dec
    secs = A.read_strtable_raw(dec)
    return 'strtable', [len(s) for s in secs], [s for sec in secs for s in sec], hdr, dec


def _iter_runs(dec):
    """msggame의 텍스트 런을 (섹션, 블롭, 시작, 끝) 순회 순서대로 내보낸다."""
    count = struct.unpack_from('<I', dec, 0)[0]
    for i in range(count):
        off, size = struct.unpack_from('<II', dec, 4 + i * 8)
        n = struct.unpack_from('<I', dec, off)[0]
        offs = struct.unpack_from(f'<{n}I', dec, off + 4)
        ends = list(offs[1:]) + [size]
        for j in range(n):
            blob = dec[off + offs[j]: off + ends[j]]
            p = 0
            while True:
                st = blob.find(b'\x07\x07\x01', p)
                if st < 0:
                    break
                en = blob.find(b'\x07\x07\x02', st + 3)
                if en < 0:
                    break
                yield blob[st + 3:en]
                p = en + 3


def _read_msggame(dec):
    out = []
    for raw in _iter_runs(dec):
        if len(raw) % 2 == 0 and raw:
            out.append(A.esc(struct.unpack_from(f'<{len(raw)//2}H', raw)))
        else:
            out.append(None)          # 홀수 길이 = 텍스트 아님, 건드리지 않음
    return out


# ---------- 쓰기 ----------
def write_file(path_in, ko, path_out):
    """원본 path_in에 ko(인덱스별 한국어 또는 None)를 적용해 path_out에 쓴다.
    바꿀 것이 하나도 없으면 원본을 그대로 복사한다(재압축으로 바이트가 달라지는 것 방지)."""
    if not any(k is not None for k in ko):
        import shutil
        os.makedirs(os.path.dirname(path_out) or '.', exist_ok=True)
        shutil.copy2(path_in, path_out)
        return
    kind, sections, strings, hdr, dec = read_file(path_in)
    if len(ko) != len(strings):
        raise SystemExit(f'{os.path.basename(path_in)}: 문자열 개수 불일치 '
                         f'(원본 {len(strings)} vs 데이터 {len(ko)}) — 게임 버전이 다릅니다')
    merged = [(k if k is not None else s) for k, s in zip(ko, strings)]

    if kind == 'strtable':
        secs, p = [], 0
        for n in sections:
            secs.append(merged[p:p + n]); p += n
        dec2 = A.build_strtable(secs)
    else:
        dec2 = _rebuild_msggame(dec, merged)

    os.makedirs(os.path.dirname(path_out) or '.', exist_ok=True)
    open(path_out, 'wb').write(A.kt_wrap(hdr, dec2))


def _rebuild_msggame(dec, merged):
    it = iter(range(len(merged)))
    count = struct.unpack_from('<I', dec, 0)[0]
    new_secs = []
    for i in range(count):
        off, size = struct.unpack_from('<II', dec, 4 + i * 8)
        n = struct.unpack_from('<I', dec, off)[0]
        offs = struct.unpack_from(f'<{n}I', dec, off + 4)
        ends = list(offs[1:]) + [size]
        blobs = []
        for j in range(n):
            blob = dec[off + offs[j]: off + ends[j]]
            out = bytearray(); p = 0
            while True:
                st = blob.find(b'\x07\x07\x01', p)
                if st < 0:
                    out += blob[p:]; break
                en = blob.find(b'\x07\x07\x02', st + 3)
                if en < 0:
                    out += blob[p:]; break
                out += blob[p:st + 3]
                raw = blob[st + 3:en]
                k = next(it)
                s = merged[k]
                if s is not None and len(raw) % 2 == 0 and raw:
                    cus = A.unesc(s)
                    out += struct.pack(f'<{len(cus)}H', *cus)
                else:
                    out += raw
                out += b'\x07\x07\x02'
                p = en + 3
            blobs.append(bytes(out))
        sec = bytearray(struct.pack('<I', n))
        pos = 4 + 4 * n
        o2 = []
        for b in blobs:
            o2.append(pos); pos += len(b)
        sec += struct.pack(f'<{n}I', *o2)
        for b in blobs:
            sec += b
        new_secs.append(bytes(sec))
    out = bytearray(struct.pack('<I', count))
    toc = len(out); out += b'\x00' * (8 * count)
    for i, b in enumerate(new_secs):
        while len(out) % 4:
            out += b'\x00'
        struct.pack_into('<II', out, toc + i * 8, len(out), len(b))
        out += b
    return bytes(out)


# ---------- CLI ----------
def cmd_export(args):
    os.makedirs(args.out, exist_ok=True)
    total = tr = 0
    index = {}
    for f in sorted(os.listdir(args.jp)):
        if not f.endswith('.bin'):
            continue
        jp_path, ko_path = os.path.join(args.jp, f), os.path.join(args.ko, f)
        if not os.path.exists(ko_path):
            print(f'  - {f}: 한글화본 없음, 건너뜀'); continue
        kind, sections, jp_s, _, _ = read_file(jp_path)
        _, _, ko_s, _, _ = read_file(ko_path)
        if len(jp_s) != len(ko_s):
            print(f'  ! {f}: 개수 불일치 {len(jp_s)} vs {len(ko_s)} — 건너뜀'); continue
        ko = [None if (k == j or k is None) else k for j, k in zip(jp_s, ko_s)]
        n_tr = sum(1 for x in ko if x is not None)
        total += len(ko); tr += n_tr
        json.dump({'file': f, 'kind': kind, 'sections': sections, 'count': len(ko), 'ko': ko},
                  open(os.path.join(args.out, f + '.json'), 'w', encoding='utf-8'),
                  ensure_ascii=False)
        index[f] = {'kind': kind, 'count': len(ko), 'translated': n_tr}
        print(f'  {f:16s} {n_tr:6d}/{len(ko):6d} 번역됨')
    json.dump(index, open(os.path.join(args.out, '_index.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print(f'합계: {tr}/{total} 문자열 번역됨 -> {args.out}')


def cmd_apply(args):
    os.makedirs(args.out, exist_ok=True)
    for f in sorted(os.listdir(args.data)):
        if not f.endswith('.bin.json'):
            continue
        d = json.load(open(os.path.join(args.data, f), encoding='utf-8'))
        name = d['file']
        jp_path = os.path.join(args.jp, name)
        if not os.path.exists(jp_path):
            print(f'  ! {name}: 원본 없음 — 건너뜀'); continue
        write_file(jp_path, d['ko'], os.path.join(args.out, name))
        print(f'  {name:16s} 적용 완료')
    # 번역 대상이 아닌 나머지 원본 파일도 그대로 복사(패치 폴더 완성도)
    if args.copy_rest:
        import shutil
        for f in sorted(os.listdir(args.jp)):
            dst = os.path.join(args.out, f)
            if not os.path.exists(dst):
                shutil.copy2(os.path.join(args.jp, f), dst)
                print(f'  {f:16s} 원본 복사')
    print(f'-> {args.out}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    e = sub.add_parser('export', help='원본+한글화본 비교 -> data JSON')
    e.add_argument('--jp', required=True); e.add_argument('--ko', required=True)
    e.add_argument('--out', required=True); e.set_defaults(func=cmd_export)
    a = sub.add_parser('apply', help='원본 + data JSON -> 한글화본')
    a.add_argument('--jp', required=True); a.add_argument('--data', required=True)
    a.add_argument('--out', required=True)
    a.add_argument('--copy-rest', action='store_true', help='번역 없는 파일도 함께 복사')
    a.set_defaults(func=cmd_apply)
    args = ap.parse_args()
    args.func(args)
