import json
base = r'C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad'
p = base + r'\translated\b0072_dialog.json'
src = base + r'\batches\b0072_dialog.json'
d = json.load(open(p, encoding='utf-8'))
s = json.load(open(src, encoding='utf-8'))
tok = '\\n'  # literal backslash + n (2 chars), as in source strings
for it in d['items']:
    if '\n' in it['t']:
        it['t'] = it['t'].replace('\n', tok)
assert len(d['items']) == len(s['items'])
for a, b in zip(d['items'], s['items']):
    assert a['i'] == b['i']
    ca, cb = a['t'].count(tok), b['t'].count(tok)
    assert ca == cb, (a['i'], ca, cb)
json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('ok', len(d['items']))
