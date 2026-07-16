import json, re

base = r'C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad'
p = base + r'\translated\b0177_dialog.json'
inp = base + r'\batches\b0177_dialog.json'

d = json.load(open(p, encoding='utf-8'))
src = json.load(open(inp, encoding='utf-8'))

TOK = '\\n'  # literal backslash + n (2 chars)

for it in d['items']:
    # my strings contain real newlines; convert to literal backslash-n token
    it['t'] = it['t'].replace('\n', TOK)

assert len(d['items']) == len(src['items'])
for a, b in zip(src['items'], d['items']):
    assert a['i'] == b['i']
    assert a['t'].count(TOK) == b['t'].count(TOK), (a['i'], a['t'].count(TOK), b['t'].count(TOK))
    m = re.search(r'[぀-ヿ一-鿿]', b['t'])
    assert not m, (b['i'], b['t'])

with open(p, 'w', encoding='utf-8') as f:
    json.dump({'items': d['items']}, f, ensure_ascii=False, indent=0)
print('ok', len(d['items']))
