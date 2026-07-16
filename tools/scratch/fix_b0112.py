import json

BASE = r'C:/Users/Jay/AppData/Local/Temp/claude/D--nsw-rom---------------------/8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8/scratchpad'
OUT = BASE + '/translated/b0112_dialog.json'
SRC = BASE + '/batches/b0112_dialog.json'

BSN = chr(92) + 'n'  # backslash + n token

d = json.load(open(OUT, encoding='utf-8'))
src = json.load(open(SRC, encoding='utf-8'))

# convert any real newline chars in t to literal backslash-n token
for it in d['items']:
    it['t'] = it['t'].replace('\n', BSN)

assert len(d['items']) == len(src['items']) == 60

probs = []
for a, b in zip(src['items'], d['items']):
    assert a['i'] == b['i']
    if a['t'].count(BSN) != b['t'].count(BSN):
        probs.append(('NL', a['i'], a['t'].count(BSN), b['t'].count(BSN)))
    if a['t'].count('<ESC>') != b['t'].count('<ESC>'):
        probs.append(('ESC', a['i']))
    # no kana/kanji left
    for ch in b['t']:
        o = ord(ch)
        if 0x3040 <= o <= 0x30FF or 0x4E00 <= o <= 0x9FFF:
            probs.append(('JP', a['i'], ch))
            break

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=0)

raw = open(OUT, encoding='utf-8').read()
print('problems:', probs)
print('raw token count src vs out:',
      open(SRC, encoding='utf-8').read().count(chr(92)*2 + 'n'),
      raw.count(chr(92)*2 + 'n'))
