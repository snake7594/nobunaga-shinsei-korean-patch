# -*- coding: utf-8 -*-
"""Deterministic risk pre-scan of the msgev strip audit: flag strings whose \\n likely carries
STRUCTURE (tabs/alignment, numbered or bulleted lists, key:value tables, ASCII art) that a
naive strip would damage. These are candidates to PROTECT (keep \\n)."""
import json, re, sys, os
sys.stdout.reconfigure(encoding='utf-8')
A = json.load(open(sys.argv[1], encoding='utf-8'))
strips = [e for e in A if e['act'] == 'strip']
print('total strip entries:', len(strips))

def flags(t):
    f = []
    if '\\t' in t: f.append('TAB')
    if re.search(r'(^|\\n)\s*[0-9０-９]+[.．、)）]', t): f.append('NUMLIST')
    if re.search(r'(^|\\n)\s*[・･*\-–—●○▲△▼▽◆◇■□★☆]', t): f.append('BULLET')
    if re.search(r'[：:]\s*$', t.split('\\n')[0]) and '\\n' in t: f.append('KEYVAL')
    if t.count('\\n') >= 4: f.append('MANY_NL')
    if re.search(r'[【】〔〕『』〈〉《》\[\]]', t): f.append('BRACKET')
    if re.search(r'　{2,}', t): f.append('IDEO2')
    if re.search(r'[=＝]{3,}|[ー―‐-]{5,}', t): f.append('RULE')
    return f

from collections import Counter
c = Counter()
examples = {}
for e in strips:
    fs = flags(e['before'])
    for f in fs:
        c[f] += 1
        examples.setdefault(f, []).append(e)
print('flag counts:', dict(c))
for f in c:
    print(f'\n=== {f} ({c[f]}) ===')
    for e in examples[f][:4]:
        print(f"  i={e['i']}: {e['before'][:70]!r}")
        print(f"      -> {e['after'][:70]!r}")
