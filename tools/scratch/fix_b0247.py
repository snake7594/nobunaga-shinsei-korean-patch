import json, re, sys
sys.stdout.reconfigure(encoding='utf-8')
base = r'C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad'
p = base + r'\translated\b0247_dialog.json'
a = json.load(open(p, encoding='utf-8'))
BSN = chr(92) + 'n'  # literal backslash + n
for x in a['items']:
    x['t'] = x['t'].replace('\n', BSN)  # real newline -> literal token
b = json.load(open(base + r'\batches\b0247_dialog.json', encoding='utf-8'))
assert len(a['items']) == len(b['items']) == 60, len(a['items'])
bad = []
for x, y in zip(a['items'], b['items']):
    if x['i'] != y['i']: bad.append(('i', x['i']))
    if x['t'].count(BSN) != y['t'].count(BSN): bad.append(('nl', x['i'], x['t'].count(BSN), y['t'].count(BSN)))
    if x['t'].count('<ESC>') != y['t'].count('<ESC>'): bad.append(('esc', x['i']))
    if re.search('[぀-ヺ一-鿿]', x['t'].replace('・', '')): bad.append(('jp', x['i']))
print('bad:', bad)
assert not bad
with open(p, 'w', encoding='utf-8') as f:
    json.dump(a, f, ensure_ascii=False, indent=0)
print('OK', len(a['items']))
