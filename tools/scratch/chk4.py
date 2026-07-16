import json, re, sys
sys.stdout.reconfigure(encoding='utf-8')
base = r'C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad'
out = json.load(open(base + r'\translated\b0227_dialog.json', encoding='utf-8'))
for i in (16, 54):
    t = out['items'][i]['t']
    hits = set(re.findall('[぀-ヿ一-鿿]', t))
    print(i, [hex(ord(c)) for c in hits])
