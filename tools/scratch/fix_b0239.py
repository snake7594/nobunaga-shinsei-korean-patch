import json

base = r'C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad'
src_p = base + r'\batches\b0239_dialog.json'
out_p = base + r'\translated\b0239_dialog.json'

with open(src_p, encoding='utf-8') as f:
    src = json.load(f)
with open(out_p, encoding='utf-8') as f:
    out = json.load(f)

NL = '\n'          # real newline
TOK = '\\' + 'n'   # literal backslash + n (the token used in source strings)

# Normalize: translated strings may contain real newlines or already the token.
for it in out['items']:
    it['t'] = it['t'].replace(NL, TOK)

# Validate
assert [x['i'] for x in src['items']] == [x['i'] for x in out['items']], 'i mismatch'
errs = []
for a, b in zip(src['items'], out['items']):
    if a['t'].count(TOK) != b['t'].count(TOK):
        errs.append(('nl', a['i'], a['t'].count(TOK), b['t'].count(TOK)))
    if a['t'].count('<ESC>') != b['t'].count('<ESC>'):
        errs.append(('esc', a['i']))
    import re
    if re.search(r'[぀-ヿ一-鿿]', b['t']):
        errs.append(('kana/kanji', a['i']))
if errs:
    print('ERRORS:', errs)
else:
    with open(out_p, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=0)
    print('OK', len(out['items']))
