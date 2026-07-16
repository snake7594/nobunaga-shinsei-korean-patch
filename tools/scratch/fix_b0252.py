import json, re, os
base = os.path.dirname(os.path.abspath(__file__))
src = json.load(open(os.path.join(base, 'batches', 'b0252_dialog.json'), encoding='utf-8'))
out = json.load(open(os.path.join(base, 'translated', 'b0252_dialog.json'), encoding='utf-8'))

BSN = '\\' + 'n'  # literal backslash + n (two chars)
fixed = []
ok = True
for s, o in zip(src['items'], out['items']):
    t = o['t'].replace('\n', BSN)  # convert real newlines to literal token
    if s['i'] != o['i']:
        ok = False; print('index mismatch', s['i'], o['i'])
    if s['t'].count(BSN) != t.count(BSN):
        ok = False; print('newline count mismatch i', s['i'], s['t'].count(BSN), t.count(BSN))
    # ESC tag check
    if len(re.findall(r'<ESC>[A-Z]{2}', s['t'])) != len(re.findall(r'<ESC>[A-Z]{2}', t)):
        ok = False; print('ESC mismatch i', s['i'])
    # residual kana/kanji check
    if re.search(r'[぀-ヺー-ヿ一-鿿]', t):  # kana/kanji, excluding middle dot U+30FB
        ok = False; print('kana/kanji remains i', s['i'], repr(t))
    fixed.append({'i': o['i'], 't': t})

print('count', len(fixed), 'ok', ok)
if ok:
    with open(os.path.join(base, 'translated', 'b0252_dialog.json'), 'w', encoding='utf-8') as f:
        json.dump({'items': fixed}, f, ensure_ascii=False, indent=1)
    print('saved')
