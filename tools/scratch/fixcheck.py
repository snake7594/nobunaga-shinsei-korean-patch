# -*- coding: utf-8 -*-
import json, re

base = r'C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad'
out = base + r'\translated\b0141_dialog.json'
src = base + r'\batches\b0141_dialog.json'

d = json.load(open(out, encoding='utf-8'))
s = json.load(open(src, encoding='utf-8'))
sm = {it['i']: it['t'] for it in s['items']}

TOK = '\\n'  # literal backslash + n (as decoded from source JSON "\\n")

fixed = []
for it in d['items']:
    t = it['t']
    # normalize: real newlines -> literal backslash-n token
    t = t.replace('\r\n', '\n').replace('\n', TOK)
    it['t'] = t
    fixed.append(it)

bad = []
for it in fixed:
    if it['t'].count(TOK) != sm[it['i']].count(TOK):
        bad.append(it['i'])
    if re.search(r'[぀-ヿ一-鿿]', it['t']):
        bad.append(('kana/kanji', it['i']))

json.dump({'items': fixed}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('items:', len(fixed), 'bad:', bad)
