import json, io
base = r'C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad'
p = base + r'\translated\b0294_dialog.json'
d = json.load(io.open(p, encoding='utf-8'))
tok = chr(92) + 'n'  # backslash + n
for it in d['items']:
    it['t'] = it['t'].replace('\n', tok)
with io.open(p, 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=0)
print('fixed')
