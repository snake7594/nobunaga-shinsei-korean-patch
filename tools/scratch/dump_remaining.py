import os, glob, json, re, sys
sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))
TOKEN_RE = re.compile(r'<ESC>..|<[0-9A-F]{2}>|\\n|\\t|%[sd0-9]')
KANA_RE = re.compile(r'[぀-ヿ]')
from collections import Counter
def nt(s): return Counter(TOKEN_RE.findall(s))

src = {}
for bf in glob.glob(os.path.join(SP, 'batches', '*.json')):
    name = os.path.basename(bf)
    for it in json.load(open(bf, encoding='utf-8'))['items']:
        src[(name, it['i'])] = (it['t'], name.split('_')[1].split('.')[0])

good = set()
for tf in glob.glob(os.path.join(SP, 'translated', '*.json')):
    name = os.path.basename(tf)
    try: data = json.load(open(tf, encoding='utf-8'))
    except Exception: continue
    for it in data.get('items', []):
        k = (name, it.get('i'))
        if k not in src: continue
        orig, cat = src[k]; ko = it.get('t', '')
        if isinstance(ko, str) and ko.strip() and not KANA_RE.search(ko) and nt(orig) == nt(ko):
            good.add(orig)

remaining = {}
for (name, i), (orig, cat) in src.items():
    if orig not in good:
        remaining[orig] = cat
items = [{'i': j, 't': t, 'cat': c} for j, (t, c) in enumerate(remaining.items())]
json.dump({'items': items}, open(os.path.join(SP, 'remaining.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print(f'remaining untranslated: {len(items)}')
print('by cat:', dict(Counter(c for c in remaining.values())))
