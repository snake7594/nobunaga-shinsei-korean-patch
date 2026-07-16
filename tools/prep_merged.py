"""Rebuild pipeline for the 1.1.4 MERGED MSG. Reuse existing translations (matched by
source string); emit batches only for NEW strings."""
import struct, sys, os, json, re, glob
import lz4.block
sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))
MERGED = r'D:\nsw\merged_sel\MSG\JP'
BATCH_DIR = os.path.join(SP, 'batches')       # add new batches here (m-prefix)
OUT_DIR = os.path.join(SP, 'translated')      # existing + new outputs

def unwrap(b):
    return lz4.block.decompress(b[24:24 + struct.unpack_from('<Q', b, 16)[0]],
                                uncompressed_size=struct.unpack_from('<Q', b, 8)[0])

def esc(cus):
    s = ''
    for cu in cus:
        if cu == 0x1B: s += '<ESC>'
        elif cu == 0x0A: s += '\\n'
        elif cu == 0x09: s += '\\t'
        elif cu == 0x5C: s += '\\\\'
        elif cu < 0x20: s += f'<{cu:02X}>'
        else: s += chr(cu)
    return s

def read_strtable(path):
    d = unwrap(open(path, 'rb').read())
    count = struct.unpack_from('<I', d, 0)[0]
    res = []
    for i in range(count):
        off, size = struct.unpack_from('<II', d, 4 + i * 8)
        n = struct.unpack_from('<I', d, off + 8)[0] & 0xFFFF
        tab = off + 0x14
        entries = struct.unpack_from(f'<{n}I', d, tab)
        strs = []
        for e in entries:
            pos = tab + e; cus = []
            while True:
                cu = struct.unpack_from('<H', d, pos)[0]; pos += 2
                if cu == 0: break
                cus.append(cu)
            strs.append(esc(cus))
        res.append(strs)
    return res

def read_msggame(path):
    d = unwrap(open(path, 'rb').read())
    count = struct.unpack_from('<I', d, 0)[0]
    res = []
    for i in range(count):
        off, size = struct.unpack_from('<II', d, 4 + i * 8)
        n = struct.unpack_from('<I', d, off)[0]
        offs = struct.unpack_from(f'<{n}I', d, off + 4)
        ends = list(offs[1:]) + [size]
        for j in range(n):
            blob = d[off + offs[j]:off + ends[j]]
            p = 0
            while True:
                st = blob.find(b'\x07\x07\x01', p)
                if st < 0: break
                en = blob.find(b'\x07\x07\x02', st + 3)
                if en < 0: break
                raw = blob[st + 3:en]
                if len(raw) % 2 == 0:
                    res.append(esc(struct.unpack_from(f'<{len(raw)//2}H', raw)))
                p = en + 3
    return res

JP = re.compile(r'[぀-ヿ一-鿿々]')
def translatable(s): return bool(JP.search(s))

SEED = {'初めから','続きから','チュートリアル','登録武将編集','追加コンテンツ','鑑賞','設定','ライセンス'}

# ---- build existing orig->ko dict (validated) ----
TOKEN_RE = re.compile(r'<ESC>..|<[0-9A-F]{2}>|\\n|\\t|%[sd0-9]')
KANA_RE = re.compile(r'[ぁ-ゖゝゞァ-ヺー-ヿ]')
from collections import Counter
def nt(s): return Counter(TOKEN_RE.findall(s))
src_items = {}
for bf in glob.glob(os.path.join(BATCH_DIR, '*.json')):
    name = os.path.basename(bf)
    for it in json.load(open(bf, encoding='utf-8'))['items']:
        src_items[(name, it['i'])] = it['t']
tr = {}
for tf in glob.glob(os.path.join(OUT_DIR, '*.json')):
    name = os.path.basename(tf)
    try: data = json.load(open(tf, encoding='utf-8'))
    except Exception: continue
    for it in data.get('items', []):
        k = (name, it.get('i'))
        if k not in src_items: continue
        orig = src_items[k]; ko = it.get('t', '')
        if isinstance(ko, str) and ko.strip() and not KANA_RE.search(ko) and nt(orig) == nt(ko):
            tr[orig] = ko
print(f'existing validated translations: {len(tr)}')

# ---- collect merged translatable strings by category ----
strdata = read_strtable(os.path.join(MERGED, 'strdata.bin'))
ev = read_strtable(os.path.join(MERGED, 'ev_strdata.bin'))
mg = read_msggame(os.path.join(MERGED, 'msggame.bin'))

uniq = {}
def add(text, cat):
    if text in SEED or not translatable(text): return
    order = {'name': 0, 'ui': 1, 'desc': 2, 'dialog': 3}
    u = uniq.get(text)
    if u is None: uniq[text] = cat
    elif order[cat] > order[u]: uniq[text] = cat

for si, strings in enumerate(strdata):
    if si == 4: continue
    for s in strings:
        add(s, 'name' if (si == 0 and len(s) <= 10 and '\\n' not in s) else ('ui' if si == 1 else 'desc'))
for s in ev[0]:
    add(s, 'name' if len(s) <= 10 and '\\n' not in s and '<ESC>' not in s else 'dialog')
for s in mg:
    add(s, 'ui' if len(s) <= 14 and '\\n' not in s else 'dialog')

new = [(t, c) for t, c in uniq.items() if t not in tr]
print(f'merged unique translatable: {len(uniq)}  already covered: {len(uniq)-len(new)}  NEW: {len(new)}')

# ---- write new batches (m-prefix) ----
by_cat = {}
for t, c in sorted(new): by_cat.setdefault(c, []).append(t)
BATCH_CHARS = {'name': 4000, 'ui': 4000, 'desc': 5000, 'dialog': 5000}
BATCH_MAX = {'name': 400, 'ui': 200, 'desc': 60, 'dialog': 60}
mid = 0
manifest = []
for cat, items in by_cat.items():
    cur, cc = [], 0
    def flush():
        global mid, cur, cc
        if not cur: return
        name = f'm{mid:04d}_{cat}.json'
        json.dump({'cat': cat, 'items': [{'i': k, 't': t} for k, t in enumerate(cur)]},
                  open(os.path.join(BATCH_DIR, name), 'w', encoding='utf-8'), ensure_ascii=False)
        manifest.append(name); mid += 1; cur, cc = [], 0
    for t in items:
        cur.append(t); cc += len(t)
        if cc >= BATCH_CHARS[cat] or len(cur) >= BATCH_MAX[cat]: flush()
    flush()
json.dump(manifest, open(os.path.join(SP, 'merged_new_batches.json'), 'w'), separators=(',', ':'))
print(f'{len(manifest)} new batches written -> merged_new_batches.json')
print(Counter(m.split("_")[1].split(".")[0] for m in manifest))
