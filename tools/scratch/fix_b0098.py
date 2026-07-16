# -*- coding: utf-8 -*-
import io, re, json

base = r'C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad'
p = base + r'\translated\b0098_dialog.json'
raw = io.open(p, encoding='utf-8').read()

# Extract items: texts contain literal backslash-n sequences, no embedded quotes
pairs = re.findall(r'\{"i": (\d+), "t": "(.*?)"\}', raw)
items = [{"i": int(i), "t": t} for i, t in pairs]

src = json.load(io.open(base + r'\batches\b0098_dialog.json', encoding='utf-8'))
assert len(items) == len(src['items']) == 60, len(items)
for a, b in zip(src['items'], items):
    assert a['i'] == b['i']
    assert a['t'].count('\\n') == b['t'].count('\\n'), (a['i'], a['t'].count('\\n'), b['t'].count('\\n'))
    assert re.findall(r'<ESC>..', a['t']) == re.findall(r'<ESC>..', b['t']), a['i']
    assert not re.search(u'[぀-ヿ一-鿿]', b['t']), (a['i'], b['t'])

out = json.dumps({"items": items}, ensure_ascii=False, indent=0)
io.open(p, 'w', encoding='utf-8', newline='\n').write(out)
print('OK', len(items))
