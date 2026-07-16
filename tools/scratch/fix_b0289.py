# -*- coding: utf-8 -*-
import json

base = r'C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad'
out_path = base + r'\translated\b0289_dialog.json'
in_path = base + r'\batches\b0289_dialog.json'

d = json.load(open(out_path, encoding='utf-8'))
src = json.load(open(in_path, encoding='utf-8'))

# source values contain literal backslash+n (two chars). Convert real newlines
# in translated values to literal backslash+n to match.
for it in d['items']:
    it['t'] = it['t'].replace('\n', '\\n')

assert len(src['items']) == len(d['items']) == 60
for a, b in zip(src['items'], d['items']):
    assert a['i'] == b['i']
    assert a['t'].count('\\n') == b['t'].count('\\n'), (a['i'], a['t'].count('\\n'), b['t'].count('\\n'))
    assert a['t'].count('<ESC>') == b['t'].count('<ESC>'), a['i']
    # no kana/kanji remaining (allow squared-CJK button tokens U+3300 block)
    for ch in b['t']:
        o = ord(ch)
        assert not (0x3040 <= o <= 0x30FF or 0x4E00 <= o <= 0x9FFF), (a['i'], ch)

json.dump(d, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print('OK', len(d['items']))
