"""Scan all translated batches, collect validation failures, and emit retry batches
(placed in batches/ as r####_cat.json so apply_translations picks them up automatically).
Retry outputs go to translated/r####_cat.json."""
import os, json, glob, re
import sys
sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))

TOKEN_RE = re.compile(r'<ESC>..|<[0-9A-F]{2}>|\\n|\\t|%[sd0-9]')
KANA_RE = re.compile(r'[぀-ヿ]')
from collections import Counter

def norm_tokens(s):
    return Counter(TOKEN_RE.findall(s))

RID_START = int(sys.argv[1]) if len(sys.argv) > 1 else 9000

# source strings keyed by (batch_file, i) — ALL batches (b*.json and r*.json)
src = {}
for bf in glob.glob(os.path.join(SP, 'batches', '*.json')):
    data = json.load(open(bf, encoding='utf-8'))
    name = os.path.basename(bf)
    cat = name.split('_')[1].split('.')[0]
    for it in data['items']:
        src[(name, it['i'])] = (it['t'], cat)

# good translations already produced (scan ALL translated files)
bad = []   # list of (orig, cat)
for tf in glob.glob(os.path.join(SP, 'translated', '*.json')):
    name = os.path.basename(tf)
    try:
        data = json.load(open(tf, encoding='utf-8'))
    except Exception:
        continue
good_origs = set()  # any valid translation exists
for tf in glob.glob(os.path.join(SP, 'translated', '*.json')):
    name = os.path.basename(tf)
    try:
        data = json.load(open(tf, encoding='utf-8'))
    except Exception:
        continue
    for it in data.get('items', []):
        key = (name, it.get('i'))
        if key not in src:
            continue
        orig, cat = src[key]
        ko = it.get('t', '')
        if not isinstance(ko, str) or not ko.strip():
            bad.append((orig, cat)); continue
        if KANA_RE.search(ko):
            bad.append((orig, cat)); continue
        if norm_tokens(orig) != norm_tokens(ko):
            bad.append((orig, cat)); continue
        good_origs.add(orig)

# retry = strings that are bad AND have no good translation anywhere
seen = set()
uniq = []
for orig, cat in bad:
    if orig in seen or orig in good_origs:
        continue
    seen.add(orig)
    uniq.append((orig, cat))
print(f'failures to retry (no good version anywhere): {len(uniq)}')
by_cat = {}
for orig, cat in uniq:
    by_cat.setdefault(cat, []).append(orig)
print('by cat:', {k: len(v) for k, v in by_cat.items()})

# write retry batches
rid = RID_START
manifest = []
PER = 40
for cat, items in by_cat.items():
    for k in range(0, len(items), PER):
        chunk = items[k:k+PER]
        name = f'r{rid:04d}_{cat}.json'
        json.dump({'cat': cat, 'items': [{'i': j, 't': t} for j, t in enumerate(chunk)]},
                  open(os.path.join(SP, 'batches', name), 'w', encoding='utf-8'),
                  ensure_ascii=False)
        manifest.append(name)
        rid += 1
json.dump(manifest, open(os.path.join(SP, 'retry_batches.json'), 'w'), separators=(',', ':'))
print(f'{len(manifest)} retry batches written')
