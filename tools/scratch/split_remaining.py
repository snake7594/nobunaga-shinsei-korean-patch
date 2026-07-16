import os, json, sys
sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))

data = json.load(open(os.path.join(SP, 'remaining.json'), encoding='utf-8'))
items = data['items']  # each: {i, t, cat}

# small batches because these are long tutorial strings; keep char budget low
rid = 9600
manifest = []
cur, cur_chars = [], 0
CHAR_CAP = 2500
ITEM_CAP = 10

def flush():
    global rid, cur, cur_chars
    if not cur:
        return
    cat = 'desc'  # unified stricter style for hard cases
    name = f'r{rid:04d}_desc.json'
    json.dump({'cat': 'desc', 'items': [{'i': k, 't': it['t']} for k, it in enumerate(cur)]},
              open(os.path.join(SP, 'batches', name), 'w', encoding='utf-8'), ensure_ascii=False)
    manifest.append(name)
    rid += 1
    cur, cur_chars = [], 0

for it in items:
    cur.append(it)
    cur_chars += len(it['t'])
    if cur_chars >= CHAR_CAP or len(cur) >= ITEM_CAP:
        flush()
flush()

json.dump(manifest, open(os.path.join(SP, 'hard_batches.json'), 'w'), separators=(',', ':'))
print(f'{len(items)} items -> {len(manifest)} hard batches')
