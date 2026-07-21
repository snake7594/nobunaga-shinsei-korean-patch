# -*- coding: utf-8 -*-
"""Survey the Korean corpus for the awkwardness classes seen in screenshots:
 A) dual particles after FIXED hangul (을(를), 은(는), 이(가), 와(과), 로(으로) ...)
 B) glued words before particles (heuristic: long hangul run + dual particle)
 C) suspicious endings: 습니다군/습니다요/해합시다/써합시다 etc.
 D) stutter mismatch: 'X, Y...' where X != first syllable of following word (with JP 、check)
Counts only; a few short samples per class."""
import json, glob, os, re, sys
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')

GH = r'D:\nsw\rom\ghpatch\translation'
DUAL = re.compile(r'(을\(를\)|를\(을\)|은\(는\)|는\(은\)|이\(가\)|가\(이\)|와\(과\)|과\(와\)|로\(으로\)|으로\(로\))')
ENDINGS = re.compile(r'(습니다군|습니다요|입니다군|써합시다|해합시다|하겠습니다군)')
STUTTER = re.compile(r'(^|[\s>」])([가-힣]), ([가-힣])')

def hangul_final(ch):
    if not ch:
        return None
    code = ord(ch) - 0xAC00
    return code % 28 if 0 <= code < 11172 else None

stats = Counter()
samples = {k: [] for k in ['A-fixed', 'A-placeholder', 'C', 'D']}
files = sorted(glob.glob(os.path.join(GH, 'korean', '*.json'))) + \
        sorted(glob.glob(os.path.join(GH, 'korean_puk', '*.json')))
for f in files:
    data = json.load(open(f, encoding='utf-8'))
    for it in data['items']:
        t = it.get('t', '')
        for m in DUAL.finditer(t):
            prev = t[m.start()-1] if m.start() > 0 else ''
            if hangul_final(prev) is not None:
                stats['A-fixed'] += 1
                if len(samples['A-fixed']) < 8:
                    samples['A-fixed'].append(t[max(0, m.start()-12):m.end()+2])
            else:
                stats['A-placeholder'] += 1
                if len(samples['A-placeholder']) < 4:
                    samples['A-placeholder'].append(t[max(0, m.start()-12):m.end()+2])
        for m in ENDINGS.finditer(t):
            stats['C'] += 1
            if len(samples['C']) < 8:
                samples['C'].append(t[max(0, m.start()-14):m.end()+2])
        for m in STUTTER.finditer(t):
            if m.group(2) != m.group(3):
                stats['D'] += 1
                if len(samples['D']) < 8:
                    samples['D'].append(t[max(0, m.start()-4):m.end()+8])
print('counts:', dict(stats))
for k, v in samples.items():
    print(f'-- {k}:')
    for s in v:
        print('   ', repr(s))
