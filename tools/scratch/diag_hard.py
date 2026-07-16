import os, json, glob, re, sys
sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))
TOKEN_RE = re.compile(r'<ESC>..|<[0-9A-F]{2}>|\\n|\\t|%[sd0-9]')
KANA_RE = re.compile(r'[぀-ヿ]')
from collections import Counter
def nt(s): return Counter(TOKEN_RE.findall(s))

hard = json.load(open(os.path.join(SP, 'hard_batches.json'), encoding='utf-8'))
reasons = Counter()
samples = {'kana': [], 'token': [], 'empty': []}
for f in hard:
    src = {it['i']: it['t'] for it in json.load(open(os.path.join(SP, 'batches', f), encoding='utf-8'))['items']}
    tp = os.path.join(SP, 'translated', f)
    if not os.path.exists(tp):
        reasons['missing_file'] += 1; continue
    try:
        out = {it['i']: it['t'] for it in json.load(open(tp, encoding='utf-8')).get('items', [])}
    except Exception as e:
        reasons['bad_json'] += 1; continue
    for i, orig in src.items():
        ko = out.get(i, '')
        if not isinstance(ko, str) or not ko.strip():
            reasons['empty'] += 1
            if len(samples['empty']) < 3: samples['empty'].append((orig, ko))
            continue
        if KANA_RE.search(ko):
            reasons['kana'] += 1
            if len(samples['kana']) < 5:
                kanas = ''.join(sorted(set(KANA_RE.findall(ko))))
                samples['kana'].append((orig[:60], ko[:80], kanas))
            continue
        if nt(orig) != nt(ko):
            reasons['token'] += 1
            if len(samples['token']) < 5:
                d_src = nt(orig); d_ko = nt(ko)
                diff = {k: (d_src.get(k,0), d_ko.get(k,0)) for k in set(d_src)|set(d_ko) if d_src.get(k,0)!=d_ko.get(k,0)}
                samples['token'].append((orig[:50], ko[:60], diff))
            continue
        reasons['ok'] += 1
print('reasons:', dict(reasons))
for cat, ss in samples.items():
    if ss:
        print(f'\n=== {cat} samples ===')
        for s in ss:
            print(repr(s))
