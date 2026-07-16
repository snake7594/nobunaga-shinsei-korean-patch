# -*- coding: utf-8 -*-
import json, re, io, os

base = os.path.dirname(os.path.abspath(__file__))
src = json.load(io.open(os.path.join(base, 'batches', 'b0285_dialog.json'), encoding='utf-8'))
out_path = os.path.join(base, 'translated', 'b0285_dialog.json')
out = json.load(io.open(out_path, encoding='utf-8'))

TOKEN = '\\n'  # literal backslash + n (two chars)

for it in out['items']:
    # translated file currently has real newlines; convert to literal \n token
    it['t'] = it['t'].replace('\n', TOKEN)

assert len(src['items']) == len(out['items']), 'count mismatch'
for s, o in zip(src['items'], out['items']):
    assert s['i'] == o['i'], ('i mismatch', s['i'], o['i'])
    assert s['t'].count(TOKEN) == o['t'].count(TOKEN), ('newline token mismatch', s['i'], s['t'], o['t'])
    assert len(re.findall(r'<ESC>[A-Z]{2}', s['t'])) == len(re.findall(r'<ESC>[A-Z]{2}', o['t'])), ('ESC mismatch', s['i'])
    assert not re.search(u'[ぁ-ゖァ-ヺ一-鿿]', o['t']), ('kana/kanji remains', o['i'], o['t'])

with io.open(out_path, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=0)

print('OK', len(out['items']))
