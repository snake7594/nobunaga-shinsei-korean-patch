import json, io
base = r'C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad'
src = json.load(io.open(base + r'\batches\b0272_dialog.json', encoding='utf-8'))
out = json.load(io.open(base + r'\translated\b0272_dialog.json', encoding='utf-8'))
assert len(src['items']) == len(out['items']) == 60
bad = 0
for a, b in zip(src['items'], out['items']):
    assert a['i'] == b['i']
    if a['t'].count('\\n') != b['t'].count('\\n'):
        print('NL mismatch', a['i'], a['t'].count('\\n'), b['t'].count('\\n')); bad += 1
    if a['t'].count('<ESC>') != b['t'].count('<ESC>'):
        print('ESC mismatch', a['i']); bad += 1
print('bad =', bad)
