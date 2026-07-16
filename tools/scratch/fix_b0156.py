import json, os
base = os.path.dirname(os.path.abspath(__file__))
src = json.load(open(os.path.join(base,'batches','b0156_dialog.json'), encoding='utf-8'))
out = json.load(open(os.path.join(base,'translated','b0156_dialog.json'), encoding='utf-8'))
BSN = '\\' + 'n'  # literal backslash + n
items = []
for a, b in zip(src['items'], out['items']):
    assert a['i'] == b['i']
    t = b['t'].replace('\n', BSN)  # real newline -> literal \n token
    assert a['t'].count(BSN) == t.count(BSN), (a['i'], a['t'], t)
    items.append({'i': b['i'], 't': t})
assert len(items) == len(src['items'])
json.dump({'items': items}, open(os.path.join(base,'translated','b0156_dialog.json'),'w',encoding='utf-8'), ensure_ascii=False, indent=0)
print('ok', len(items))
