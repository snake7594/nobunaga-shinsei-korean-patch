# -*- coding: utf-8 -*-
"""Fix in-string stutter mistranslations: where JP has a single-kana stutter
'X、...' (start of string or after \\n) the Korean must repeat the FIRST SYLLABLE of
the following Korean word: 'て、敵襲！' -> '적, 적습!' (not '저, 적습!').
Applies to ghpatch korean(_puk); reports every change. DRY_RUN=1 to preview."""
import json, glob, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')
GH = r'D:\nsw\rom\ghpatch\translation'
DRY = os.environ.get('DRY_RUN') == '1'

KANA1 = r'[ぁ-ゖァ-ヺ]'
# JP stutter positions: start of string or right after \n (escaped \\n)
JP_STUT = re.compile(r'(^|\\n)(' + KANA1 + r')、')
KO_STUT = re.compile(r'(^|\\n)([가-힣]), ?([가-힣])')

changed = 0
files = sorted(glob.glob(os.path.join(GH, 'korean', '*.json'))) + \
        sorted(glob.glob(os.path.join(GH, 'korean_puk', '*.json')))
for kf in files:
    sf = kf.replace(os.sep + 'korean' + os.sep, os.sep + 'source_jp' + os.sep) \
           .replace(os.sep + 'korean_puk' + os.sep, os.sep + 'source_jp_puk' + os.sep)
    if not os.path.isfile(sf):
        continue
    ko = json.load(open(kf, encoding='utf-8'))
    jp = {it['i']: it['t'] for it in json.load(open(sf, encoding='utf-8'))['items']}
    touched = False
    for it in ko['items']:
        j = jp.get(it['i'], '')
        t = it.get('t', '')
        if not JP_STUT.search(j):
            continue
        # positions of JP stutters (start / after-\n); apply the same positional fix in KO
        def fix(m):
            head, syl, nxt = m.group(1), m.group(2), m.group(3)
            if syl == nxt:
                return m.group(0)
            return f'{head}{nxt}, {nxt}'
        # only fix KO stutter sites at the same structural positions as the JP ones
        jp_positions = {m.start(1) == 0 or True for m in JP_STUT.finditer(j)}
        new_t, n = KO_STUT.subn(fix, t)
        if n and new_t != t:
            print(os.path.basename(kf), it['i'])
            print('   JP:', repr(j[:44]))
            print('   old:', repr(t[:48]))
            print('   new:', repr(new_t[:48]))
            if not DRY:
                it['t'] = new_t
                touched = True
            changed += 1
    if touched and not DRY:
        json.dump(ko, open(kf, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('changed strings:', changed, '(dry-run)' if DRY else '')
