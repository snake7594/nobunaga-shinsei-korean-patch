"""Extract all translatable strings, dedup, categorize, and write translation batches."""
import struct, sys, os, json, re
sys.stdout.reconfigure(encoding='utf-8')

SP = os.path.dirname(os.path.abspath(__file__))
BATCH_DIR = os.path.join(SP, 'batches')
OUT_DIR = os.path.join(SP, 'translated')
os.makedirs(BATCH_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

# ---------- reversible escape ----------
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

def unesc(s):
    out = []
    i = 0
    while i < len(s):
        c = s[i]
        if c == '\\' and i + 1 < len(s):
            n = s[i + 1]
            if n == 'n': out.append(0x0A); i += 2; continue
            if n == 't': out.append(0x09); i += 2; continue
            if n == '\\': out.append(0x5C); i += 2; continue
        if c == '<':
            if s[i:i+5] == '<ESC>': out.append(0x1B); i += 5; continue
            m = re.match(r'<([0-9A-F]{2})>', s[i:i+4])
            if m: out.append(int(m.group(1), 16)); i += 4; continue
        out.append(ord(c)); i += 1
    return out

# ---------- readers ----------
def read_strtable(path):
    with open(path, 'rb') as f:
        d = f.read()
    count = struct.unpack_from('<I', d, 0)[0]
    result = []
    for i in range(count):
        off, size = struct.unpack_from('<II', d, 4 + i * 8)
        n = struct.unpack_from('<I', d, off + 8)[0] & 0xFFFF
        tab = off + 0x14
        entries = struct.unpack_from(f'<{n}I', d, tab)
        strings = []
        for e in entries:
            pos = tab + e
            cus = []
            while True:
                cu = struct.unpack_from('<H', d, pos)[0]
                pos += 2
                if cu == 0:
                    break
                cus.append(cu)
            strings.append(esc(cus))
        result.append(strings)
    return result

def read_msggame(path):
    with open(path, 'rb') as f:
        d = f.read()
    count = struct.unpack_from('<I', d, 0)[0]
    result = []  # (sec, entry, run, text)
    for i in range(count):
        off, size = struct.unpack_from('<II', d, 4 + i * 8)
        n = struct.unpack_from('<I', d, off)[0]
        offs = struct.unpack_from(f'<{n}I', d, off + 4)
        ends = list(offs[1:]) + [size]
        for j in range(n):
            blob = d[off + offs[j]: off + ends[j]]
            p = 0
            run = 0
            while True:
                st = blob.find(b'\x07\x07\x01', p)
                if st < 0: break
                en = blob.find(b'\x07\x07\x02', st + 3)
                if en < 0: break
                raw = blob[st + 3:en]
                if len(raw) % 2 == 0:
                    cus = struct.unpack_from(f'<{len(raw)//2}H', raw)
                    result.append((i, j, run, esc(cus)))
                run += 1
                p = en + 3
    return result

JP = re.compile(r'[぀-ヿ一-鿿々]')  # kana/kanji/々

def translatable(s):
    return bool(JP.search(s))

# seed: keep the verified v3 menu translations
SEED = {
    '初めから': '처음부터', '続きから': '이어하기', 'チュートリアル': '튜토리얼',
    '登録武将編集': '등록무장편집', '追加コンテンツ': '추가 콘텐츠',
    '鑑賞': '감상', '設定': '설정', 'ライセンス': '라이선스',
}

# ---------- collect ----------
strdata = read_strtable(os.path.join(SP, 'msg_jp_strdata.dec'))
ev = read_strtable(os.path.join(SP, 'msg_jp_ev_strdata.dec'))
mg = read_msggame(os.path.join(SP, 'msg_jp_msggame.dec'))

unique = {}   # text -> {cat, count}
def add(text, cat):
    if text in SEED or not translatable(text):
        return
    u = unique.setdefault(text, {'cat': cat, 'n': 0})
    u['n'] += 1
    # dialogs win over names for category (longer context matters)
    order = {'name': 0, 'ui': 1, 'desc': 2, 'dialog': 3}
    if order[cat] > order[u['cat']]:
        u['cat'] = cat

for si, strings in enumerate(strdata):
    if si == 4:
        continue  # credits: keep original
    for s in strings:
        if si == 0:
            add(s, 'name' if len(s) <= 10 and '\\n' not in s else 'desc')
        elif si == 1:
            add(s, 'ui')
        else:
            add(s, 'desc')
for s in ev[0]:
    add(s, 'name' if len(s) <= 10 and '\\n' not in s and '<ESC>' not in s else 'dialog')
for _, _, _, s in mg:
    add(s, 'ui' if len(s) <= 14 and '\\n' not in s else 'dialog')

stats = {}
for t, u in unique.items():
    c = u['cat']
    st = stats.setdefault(c, [0, 0])
    st[0] += 1
    st[1] += len(t)
print('unique translatable strings by category:')
for c, (cnt, chars) in sorted(stats.items()):
    print(f'  {c:8}: {cnt:6,} strings, {chars:9,} chars')
print(f'  TOTAL   : {sum(s[0] for s in stats.values()):6,} strings, '
      f'{sum(s[1] for s in stats.values()):9,} chars')

# ---------- write batches ----------
BATCH_CHARS = {'name': 4000, 'ui': 4000, 'desc': 5000, 'dialog': 5000}
BATCH_MAX_ITEMS = {'name': 400, 'ui': 200, 'desc': 60, 'dialog': 60}

items_by_cat = {}
for t, u in sorted(unique.items()):
    items_by_cat.setdefault(u['cat'], []).append(t)

manifest = []
bid = 0
for cat, items in items_by_cat.items():
    cur, cur_chars = [], 0
    def flush():
        global bid, cur, cur_chars
        if not cur:
            return
        name = f'b{bid:04d}_{cat}.json'
        with open(os.path.join(BATCH_DIR, name), 'w', encoding='utf-8') as f:
            json.dump({'cat': cat, 'items': [{'i': k, 't': t} for k, t in enumerate(cur)]},
                      f, ensure_ascii=False, indent=0)
        manifest.append({'file': name, 'cat': cat, 'count': len(cur)})
        bid += 1
        cur, cur_chars = [], 0
    for t in items:
        cur.append(t)
        cur_chars += len(t)
        if cur_chars >= BATCH_CHARS[cat] or len(cur) >= BATCH_MAX_ITEMS[cat]:
            flush()
    flush()

with open(os.path.join(SP, 'batch_manifest.json'), 'w', encoding='utf-8') as f:
    json.dump(manifest, f, ensure_ascii=False, indent=1)
print(f'\n{len(manifest)} batches written to {BATCH_DIR}')
from collections import Counter
print(Counter(m['cat'] for m in manifest))
