import json, re, os
base = os.path.dirname(os.path.abspath(__file__))
src = json.load(open(os.path.join(base,'batches','b0146_dialog.json'),encoding='utf-8'))
p = os.path.join(base,'translated','b0146_dialog.json')
dst = json.load(open(p,encoding='utf-8'))
NL = chr(92)+'n'  # literal backslash + n
for it in dst['items']:
    it['t'] = it['t'].replace('\n', NL).replace(NL+NL, NL)
with open(p,'w',encoding='utf-8') as f:
    json.dump({"items": dst['items']}, f, ensure_ascii=False, indent=0)
d2 = json.load(open(p,encoding='utf-8'))
ok = True
for a,b in zip(src['items'], d2['items']):
    if a['i']!=b['i']: ok=False; print('i mismatch', a['i'], b['i'])
    if a['t'].count(NL)!=b['t'].count(NL):
        ok=False; print('NL mismatch', a['i'], a['t'].count(NL), b['t'].count(NL))
    if re.findall('<ESC>[A-Z]{2}', a['t'])!=re.findall('<ESC>[A-Z]{2}', b['t']):
        ok=False; print('ESC mismatch', a['i'])
    if re.search('[぀-ヿ一-鿿]', b['t']):
        ok=False; print('JP remains', a['i'], b['t'])
    if '\n' in b['t']:
        ok=False; print('real newline remains', a['i'])
print('items:', len(d2['items']), 'ALL OK' if ok else 'FAILED')
