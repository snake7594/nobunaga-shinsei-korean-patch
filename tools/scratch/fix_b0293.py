import json, re, os
base = os.path.dirname(os.path.abspath(__file__))
BS = chr(92)
TOK = BS + 'n'  # literal backslash-n
a = json.load(open(os.path.join(base, 'batches', 'b0293_dialog.json'), encoding='utf-8'))
b = json.load(open(os.path.join(base, 'translated', 'b0293_dialog.json'), encoding='utf-8'))
for y in b['items']:
    y['t'] = y['t'].replace('\n', TOK)
assert [x['i'] for x in a['items']] == [y['i'] for y in b['items']]
for x, y in zip(a['items'], b['items']):
    for tok in [TOK, '<ESC>CC', '<ESC>CA', '<ESC>CZ', '%s']:
        assert x['t'].count(tok) == y['t'].count(tok), (x['i'], tok, x['t'].count(tok), y['t'].count(tok))
    assert not re.search(u'[぀-ヿ一-鿿]', y['t']), (x['i'], y['t'])
with open(os.path.join(base, 'translated', 'b0293_dialog.json'), 'w', encoding='utf-8') as f:
    json.dump(b, f, ensure_ascii=False, indent=0)
print('OK', len(b['items']))
