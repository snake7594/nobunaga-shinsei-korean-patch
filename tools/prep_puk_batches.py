# -*- coding: utf-8 -*-
"""Batch find_puk_new_strings.py's output (msgpk_to_translate.json) into translation-ready
JSON files under translation/source_jp_puk/ (same {i,t} convention as the base game's
translation/source_jp/), plus a terminology glossary from the base dict for consistency.
After translating each batch into a matching translation/korean_puk/pkNNN.json, run
tools/build_msgpk.py to assemble the final MSG_PK."""
import json, os, sys, re, glob
sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))
BD = os.path.join(SP, '..', 'translation', 'source_jp_puk')
os.makedirs(BD, exist_ok=True)

strs = json.load(open(os.path.join(SP,'msgpk_to_translate.json'), encoding='utf-8'))['strings']
print('total to translate:', len(strs), 'chars:', sum(len(s) for s in strs))

# sort by length so batches are more length-homogeneous (short UI labels vs long tutorial text)
strs_sorted = sorted(strs, key=len)

BATCH_CHARS = 6000
BATCH_MAX_ITEMS = 260
batches = []
cur, cur_chars = [], 0
for s in strs_sorted:
    cur.append(s); cur_chars += len(s)
    if cur_chars >= BATCH_CHARS or len(cur) >= BATCH_MAX_ITEMS:
        batches.append(cur); cur, cur_chars = [], 0
if cur: batches.append(cur)
print('batches:', len(batches))

manifest = []
for bi, items in enumerate(batches):
    name = f'pk{bi:03d}.json'
    json.dump({'items':[{'i':k,'t':t} for k,t in enumerate(items)]},
               open(os.path.join(BD,name),'w',encoding='utf-8'), ensure_ascii=False, indent=0)
    manifest.append({'file':name,'count':len(items),'chars':sum(len(x) for x in items)})
json.dump(manifest, open(os.path.join(SP,'puk_batch_manifest.json'),'w',encoding='utf-8'), ensure_ascii=False, indent=1)
for m in manifest[:5]+manifest[-3:]: print(m)

# ---- glossary: terms from the base game's dict that also appear in the new strings ----
tr = {}
TR_DIR = os.path.join(SP, '..', 'translation')
for bf in glob.glob(os.path.join(TR_DIR, 'source_jp', '*.json')):
    name = os.path.basename(bf)
    src = {it['i']: it['t'] for it in json.load(open(bf, encoding='utf-8'))['items']}
    kf = os.path.join(TR_DIR, 'korean', name)
    if os.path.isfile(kf):
        for it in json.load(open(kf, encoding='utf-8'))['items']:
            if it['i'] in src and isinstance(it.get('t'), str) and it['t'].strip():
                tr[src[it['i']]] = it['t']
# candidate glossary source: short JP terms (<=6 chars, must contain kanji = real nouns/game
# terms, not grammatical hiragana fragments), no punctuation/placeholders
KANJI_RE = re.compile(r'[一-鿿々]')
cand = [(jp,ko) for jp,ko in tr.items() if 2<=len(jp)<=6 and not re.search(r'[\\<%]', jp) and KANJI_RE.search(jp)]
joined = '\n'.join(strs)  # search space
hits=[]
for jp,ko in cand:
    if jp in joined:
        hits.append((jp,ko))
print('glossary candidate hits:', len(hits))
# keep top ~150 most-frequent-looking (by count of occurrences in joined text, cheap heuristic)
scored=[]
for jp,ko in hits:
    c = joined.count(jp)
    if c>=2:
        scored.append((c,jp,ko))
scored.sort(reverse=True)
glossary = scored[:180]
with open(os.path.join(SP,'puk_glossary.txt'),'w',encoding='utf-8') as f:
    for c,jp,ko in glossary:
        f.write(f'{jp} -> {ko}\n')
print('glossary terms written:', len(glossary))
for c,jp,ko in glossary[:20]: print(f'  {jp} -> {ko}  (x{c})')
