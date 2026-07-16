import json, io
base = r'C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad'
out_path = base + r'\translated\b0272_dialog.json'
src = json.load(io.open(base + r'\batches\b0272_dialog.json', encoding='utf-8'))
out = json.load(io.open(out_path, encoding='utf-8'))
for b in out['items']:
    b['t'] = b['t'].replace('\r\n', '\n').replace('\n', '\\n')
with io.open(out_path, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=0)
# verify
out2 = json.load(io.open(out_path, encoding='utf-8'))
bad = 0
for a, b in zip(src['items'], out2['items']):
    assert a['i'] == b['i']
    if a['t'].count('\\n') != b['t'].count('\\n'):
        print('NL mismatch', a['i'], a['t'].count('\\n'), b['t'].count('\\n')); bad += 1
    if a['t'].count('<ESC>') != b['t'].count('<ESC>'):
        print('ESC mismatch', a['i']); bad += 1
    if any('぀' <= c <= 'ヿ' or '一' <= c <= '鿿' for c in b['t']):
        print('JP chars remain', a['i']); bad += 1
print('items', len(out2['items']), 'bad =', bad)
