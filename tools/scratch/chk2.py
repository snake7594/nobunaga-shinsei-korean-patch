import json
base = r'C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad'
src = json.load(open(base + r'\batches\b0227_dialog.json', encoding='utf-8'))
out = json.load(open(base + r'\translated\b0227_dialog.json', encoding='utf-8'))
print('SRC0:', repr(src['items'][0]['t'][:60]))
print('OUT0:', repr(out['items'][0]['t'][:60]))
raw = open(base + r'\translated\b0227_dialog.json', encoding='utf-8').read()
i = raw.find('n허') if False else raw.find('허')
