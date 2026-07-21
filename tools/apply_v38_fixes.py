# -*- coding: utf-8 -*-
"""Apply v3.8 dialogue-quality fixes to ghpatch canonical JSONs.
Fixes are keyed by EXACT JP source string; the Korean value is replaced only if it
matches the expected old value (safety). Token preservation asserted."""
import json, glob, os, re, sys
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))
GH = r'D:\nsw\rom\ghpatch\translation'
TOK = re.compile(r'<ESC>..|<[0-9A-F]{2}>|\\n|\\t|%[sd0-9]')
def toks(s): return Counter(TOK.findall(s))

chains = json.load(open(os.path.join(SP, 'split_chains.json'), encoding='utf-8'))
agent_fixes = json.load(open(os.path.join(SP, 'agent1_fixes.json'), encoding='utf-8'))

FIXES = []   # (jp, old_ko, new_ko)
for f in agent_fixes:
    c = chains[f['idx']]
    for jp, old, new in zip(c['jp'], c['ko'], f['ko']):
        if old != new:
            FIXES.append((jp, old, new))

# manual fixes (fragments referenced by chain idx)
def frag(idx, k):
    c = chains[idx]
    return c['jp'][k], c['ko'][k]

jp, old = frag(1671, 0)      # '...これより' -> add trailing space
FIXES.append((jp, old, old + ' '))
jp, old = frag(1672, 0)      # 'て、天下を！？...' stutter
FIXES.append((jp, old, old.replace('처, 천하를', '천, 천하를', 1)))
jp, old = frag(3401, 0)      # '...お世話' mid-word cut
FIXES.append((jp, old, old.replace('앞으로 신세를 지겠습', '앞으로 신세 질 생각', 1)))
jp, old = frag(2097, 0)      # '...お世' mid-word cut
FIXES.append((jp, old, old.replace('이제부터 신세를 지', '이제부터 신세 질 참', 1)))

# standalone table strings (stutters) — keyed by JP with expected KO substring swap
STANDALONE = [
    ('て、敵襲！', '저, 적습', '적, 적습'),
    ('て、敵が取り乱しておる', '저, 적이', '적, 적이'),
]

applied = 0
missed = []
files = sorted(glob.glob(os.path.join(GH, 'source_jp', '*.json'))) + \
        sorted(glob.glob(os.path.join(GH, 'source_jp_puk', '*.json')))
for sf in files:
    kf = sf.replace(os.sep + 'source_jp' + os.sep, os.sep + 'korean' + os.sep) \
           .replace(os.sep + 'source_jp_puk' + os.sep, os.sep + 'korean_puk' + os.sep)
    if not os.path.isfile(kf):
        continue
    src = {it['i']: it['t'] for it in json.load(open(sf, encoding='utf-8'))['items']}
    ko = json.load(open(kf, encoding='utf-8'))
    touched = False
    for it in ko['items']:
        j = src.get(it['i'], '')
        t = it.get('t', '')
        for jp, old, new in FIXES:
            if j == jp and t == old:
                assert toks(old) == toks(new), (jp, new)
                it['t'] = new
                touched = True
                applied += 1
                print('FIX', os.path.basename(kf), it['i'])
                print('   old:', repr(old[:64]))
                print('   new:', repr(new[:64]))
        for jp, osub, nsub in STANDALONE:
            if jp in j and osub in t:
                it['t'] = t.replace(osub, nsub, 1)
                touched = True
                applied += 1
                print('FIX(stutter)', os.path.basename(kf), it['i'], osub, '->', nsub)
    if touched:
        json.dump(ko, open(kf, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)

want = len(FIXES)
print(f'\napplied {applied} replacements (fix rules: {want} chain-frag + {len(STANDALONE)} stutter)')
