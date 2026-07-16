import json, io, re
base = r'C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad'
src = json.load(io.open(base + r'\batches\b0294_dialog.json', encoding='utf-8'))
dst = json.load(io.open(base + r'\translated\b0294_dialog.json', encoding='utf-8'))
print('count', len(dst['items']))
tok = '\\' + 'n'  # literal backslash + n
bad = 0
for a, b in zip(src['items'], dst['items']):
    if a['i'] != b['i']:
        print('i mismatch', a['i'], b['i']); bad += 1
    if a['t'].count(tok) != b['t'].count(tok):
        print('NL mismatch', a['i'], repr(a['t'][:20]), repr(b['t'][:20])); bad += 1
    if a['t'].count('<ESC>') != b['t'].count('<ESC>'):
        print('ESC mismatch', a['i']); bad += 1
    if re.search(r'[぀-ヿ一-鿿]', b['t']):
        print('kana/kanji remains', a['i'], b['t']); bad += 1
print('bad', bad)
