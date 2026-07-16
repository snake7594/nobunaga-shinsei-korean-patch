import json, io, re
base = r'C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad'
inp = json.load(io.open(base + r'\batches\b0286_dialog.json', encoding='utf-8'))
out = json.load(io.open(base + r'\translated\b0286_dialog.json', encoding='utf-8'))
assert [x['i'] for x in inp['items']] == [x['i'] for x in out['items']], 'i mismatch'
ok = True
for a, b in zip(inp['items'], out['items']):
    for tok in ('\\n', '<ESC>', '%s', '%d'):
        if a['t'].count(tok) != b['t'].count(tok):
            ok = False
            print('MISMATCH', a['i'], tok, a['t'].count(tok), b['t'].count(tok))
    if re.search(r'[぀-ヿ一-鿿]', b['t']):
        ok = False
        print('KANA/KANJI remains in', b['i'])
print('count', len(out['items']), 'ok', ok)
