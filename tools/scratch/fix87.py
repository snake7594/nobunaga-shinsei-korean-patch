import json, os
base = os.path.dirname(os.path.abspath(__file__))
src = json.load(open(os.path.join(base, 'batches', 'b0087_dialog.json'), encoding='utf-8'))
out = json.load(open(os.path.join(base, 'translated', 'b0087_dialog.json'), encoding='utf-8'))
BSN = '\\' + 'n'  # literal backslash + n
items = []
for a, b in zip(src['items'], out['items']):
    assert a['i'] == b['i']
    t = b['t'].replace('\n', BSN)
    assert a['t'].count(BSN) == t.count(BSN), (a['i'], a['t'], t)
    # ESC tag count check
    assert a['t'].count('<ESC>') == t.count('<ESC>'), a['i']
    items.append({'i': b['i'], 't': t})
assert len(items) == len(src['items'])
with open(os.path.join(base, 'translated', 'b0087_dialog.json'), 'w', encoding='utf-8') as f:
    json.dump({'items': items}, f, ensure_ascii=False, indent=1)
print('OK', len(items))
