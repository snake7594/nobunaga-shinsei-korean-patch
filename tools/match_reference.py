# -*- coding: utf-8 -*-
"""참고 번역(엑셀) ↔ 게임 원문 매칭.

`reference/신생_이벤트_원문대조번역.xlsx` 는 게임 화면을 OCR 한 일본어 원문과 그에 대한
한국어 번역이 들어 있다. OCR이라 원문에 오탈자가 있어(てある↔である, リ↔り, 隹↔誰 …)
글자 그대로는 게임 텍스트와 매칭되지 않는다. 그래서 **한자만 뽑아 3-gram 색인**으로
후보를 좁히고 유사도로 확정한다(한자는 OCR 정확도가 높고 변별력도 크다).

결과: reference_match.json — [{file, index, jp, cur_ko, ref_ko, score}]

  python tools/match_reference.py --jp <원본 MSG 폴더> [--jp2 <기본판 MSG 폴더>] \
      --data data/ko/puk_117 [--data2 data/ko/base] --out reference_match.json
"""
import sys, os, re, json, argparse
from collections import defaultdict
from difflib import SequenceMatcher
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ko_tables as K

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XLSX = os.path.join(ROOT, 'reference', '신생_이벤트_원문대조번역.xlsx')

ESC = re.compile(r'<ESC>C.')
PLACE = re.compile(r'\[[a-z]+\d+\]')
KANJI = re.compile(r'[一-鿿]')


def kanji_only(s):
    """한자만 남긴다 — OCR이 가장 잘 맞추고 변별력이 큰 부분."""
    s = ESC.sub('', s)
    s = PLACE.sub('', s)
    return ''.join(KANJI.findall(s))


def load_reference():
    import openpyxl
    wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
    ws = wb.worksheets[0]
    out = []
    for jp, ko, ev in ws.iter_rows(min_row=1, values_only=True):
        if not jp or not ko:
            continue
        jp = str(jp).strip(); ko = str(ko).strip()
        if len(jp) < 4:
            continue
        out.append((jp, ko))
    return out


def load_game(jp_dir, data_dir):
    """게임 원문 + 현재 번역을 (파일, 인덱스, 원문, 현재번역)으로."""
    rows = []
    for f in sorted(os.listdir(data_dir)):
        if not f.endswith('.bin.json'):
            continue
        d = json.load(open(os.path.join(data_dir, f), encoding='utf-8'))
        name = d['file']
        p = os.path.join(jp_dir, name)
        if not os.path.exists(p):
            continue
        _, _, jp, _, _ = K.read_file(p)
        for i, ko in enumerate(d['ko']):
            if i >= len(jp) or not jp[i]:
                continue
            rows.append((name, i, jp[i], ko))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--jp', required=True); ap.add_argument('--data', required=True)
    ap.add_argument('--jp2'); ap.add_argument('--data2')
    ap.add_argument('--out', required=True)
    ap.add_argument('--min-kanji', type=int, default=6, help='이 개수 미만 한자면 건너뜀')
    ap.add_argument('--score', type=float, default=0.72)
    a = ap.parse_args()

    ref = load_reference()
    print(f'참고 번역 {len(ref):,}행')
    game = load_game(a.jp, a.data)
    if a.jp2 and a.data2:
        game += load_game(a.jp2, a.data2)
    print(f'게임 문자열 {len(game):,}개')

    # 한자 3-gram 색인
    idx = defaultdict(list)
    gk = []
    for n, (name, i, jp, ko) in enumerate(game):
        k = kanji_only(jp)
        gk.append(k)
        if len(k) < a.min_kanji:
            continue
        for t in {k[j:j+3] for j in range(len(k) - 2)}:
            idx[t].append(n)

    out = []
    unmatched = 0
    for jp_ref, ko_ref in ref:
        k = kanji_only(jp_ref)
        if len(k) < a.min_kanji:
            unmatched += 1; continue
        cand = defaultdict(int)
        for t in {k[j:j+3] for j in range(len(k) - 2)}:
            for n in idx.get(t, ()):
                cand[n] += 1
        if not cand:
            unmatched += 1; continue
        top = sorted(cand.items(), key=lambda kv: -kv[1])[:40]
        best, bs = None, 0.0
        for n, _ in top:
            s = SequenceMatcher(None, k, gk[n]).ratio()
            if s > bs:
                bs, best = s, n
        if best is None or bs < a.score:
            unmatched += 1; continue
        name, i, jp, ko = game[best]
        out.append({'file': name, 'index': i, 'jp': jp, 'cur_ko': ko,
                    'ref_ko': ko_ref, 'ref_jp': jp_ref, 'score': round(bs, 3)})

    # 같은 게임 문자열에 여러 참고행이 붙으면 점수 높은 것만
    bykey = {}
    for r in out:
        k2 = (r['file'], r['index'])
        if k2 not in bykey or r['score'] > bykey[k2]['score']:
            bykey[k2] = r
    res = sorted(bykey.values(), key=lambda r: (r['file'], r['index']))
    json.dump(res, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'매칭 {len(res):,}건 (미매칭 참고행 {unmatched:,})  -> {a.out}')


if __name__ == '__main__':
    main()
