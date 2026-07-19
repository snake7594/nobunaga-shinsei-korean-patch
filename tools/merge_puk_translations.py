# -*- coding: utf-8 -*-
"""Validate translation/korean_puk/*.json against translation/source_jp_puk/*.json
(index alignment, token-preservation, no leftover kana). Run this after translating a new
batch (from tools/prep_puk_batches.py) and before tools/build_msgpk.py, which reads the
same directories directly — this script only reports problems, it writes no merged dict."""
import json, os, re, sys, glob
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(SP, '..', 'translation', 'source_jp_puk')
KO_DIR  = os.path.join(SP, '..', 'translation', 'korean_puk')

TOKEN_RE = re.compile(r'<ESC>..|<[0-9A-F]{2}>|\\n|\\t|%[sd0-9]|\n|\t')
KANA_RE = re.compile(r'[ぁ-ゖゝゞァ-ヺー-ヿ]')

def norm_tokens(s):
    toks = TOKEN_RE.findall(s)
    return Counter(t.replace('\n','\\n').replace('\t','\\t') for t in toks)

stats = Counter(); fails=[]; tr_new={}
for bpath in sorted(glob.glob(os.path.join(SRC_DIR, '*.json'))):
    bname = os.path.basename(bpath)
    tpath = os.path.join(KO_DIR, bname)
    src = {it['i']: it['t'] for it in json.load(open(bpath, encoding='utf-8'))['items']}
    if not os.path.isfile(tpath):
        stats['missing_file'] += 1
        fails.append((bname,'ALL','translated file missing'))
        continue
    try:
        data = json.load(open(tpath, encoding='utf-8'))
    except Exception as e:
        stats['bad_json'] += 1
        fails.append((bname,'ALL',f'json error: {e}'))
        continue
    got = {it.get('i'): it.get('t','') for it in data.get('items',[])}
    for i, orig in src.items():
        if i not in got:
            stats['idx_missing'] += 1; fails.append((bname,i,'index missing in output')); continue
        ko = got[i]
        if not isinstance(ko,str) or not ko.strip():
            stats['empty'] += 1; fails.append((bname,i,'empty')); continue
        if KANA_RE.search(ko):
            stats['kana_remains'] += 1; fails.append((bname,i,'kana remains: '+ko[:40])); continue
        if norm_tokens(orig) != norm_tokens(ko):
            stats['token_mismatch'] += 1; fails.append((bname,i,f'token mismatch orig={orig[:30]!r} ko={ko[:30]!r}')); continue
        tr_new[orig] = ko
        stats['ok'] += 1

print('validation stats:', dict(stats))
print('usable translations:', len(tr_new))
with open(os.path.join(SP,'puk_translate_report.txt'),'w',encoding='utf-8') as f:
    f.write(f'stats: {dict(stats)}\n\nFAILS ({len(fails)}):\n')
    for b,i,why in fails: f.write(f'{b}\t{i}\t{why}\n')
if fails:
    print(f'{len(fails)} FAILURES — see puk_translate_report.txt, examples:')
    for b,i,why in fails[:20]: print(' ', b, i, why[:80])
else:
    print('all entries valid.')
