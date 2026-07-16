import json, re, sys
sys.stdout.reconfigure(encoding='utf-8')
base = r'C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad'
p = base + r'\translated\b0227_dialog.json'
d = json.load(open(p, encoding='utf-8'))
for it in d['items']:
    it['t'] = it['t'].replace('\n', '\n')  # real newline -> literal backslash+n
with open(p, 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=0)
# validate
src = json.load(open(base + r'\batches\b0227_dialog.json', encoding='utf-8'))
out = json.load(open(p, encoding='utf-8'))
bad = []
for a, b in zip(src['items'], out['items']):
    if a['i'] != b['i']: bad.append(('i', a['i']))
    if a['t'].count('\n') != b['t'].count('\n'): bad.append(('nl', a['i'], a['t'].count('\n'), b['t'].count('\n')))
    if a['t'].count('<ESC>') != b['t'].count('<ESC>'): bad.append(('esc', a['i']))
    if re.search('[぀-ヿ一-鿿]', b['t']): bad.append(('jp', a['i']))
print('count', len(out['items']), 'bad', bad)
print('OUT0:', ascii(out['items'][0]['t']))
