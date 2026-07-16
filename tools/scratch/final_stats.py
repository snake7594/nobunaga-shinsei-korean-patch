import struct, os, glob, json, re, sys
import lz4.block
sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))

# unique-source coverage
TOKEN_RE = re.compile(r'<ESC>..|<[0-9A-F]{2}>|\\n|\\t|%[sd0-9]')
KANA_RE = re.compile(r'[ぁ-ゖゝゞァ-ヺー-ヿ]')
from collections import Counter
def nt(s): return Counter(TOKEN_RE.findall(s))
src = {}
for bf in glob.glob(os.path.join(SP, 'batches', '*.json')):
    name = os.path.basename(bf)
    for it in json.load(open(bf, encoding='utf-8'))['items']:
        src[(name, it['i'])] = it['t']
good = set()
for tf in glob.glob(os.path.join(SP, 'translated', '*.json')):
    name = os.path.basename(tf)
    try: data = json.load(open(tf, encoding='utf-8'))
    except Exception: continue
    for it in data.get('items', []):
        k = (name, it.get('i'))
        if k not in src: continue
        orig = src[k]; ko = it.get('t', '')
        if isinstance(ko, str) and ko.strip() and not KANA_RE.search(ko) and nt(orig) == nt(ko):
            good.add(orig)
uniq = set(src.values())
print(f'unique source strings: {len(uniq):,}')
print(f'translated (valid): {len(good):,}  ({100*len(good)/len(uniq):.1f}%)')
print(f'remaining (JP fallback): {len(uniq)-len(good):,}')

# in-file Hangul coverage of the rebuilt MSG
OUT = r'D:\nsw\rom\노부나가의 야망 신생_일본판\한글패치_테스트\romfs\MSG\JP'
def unwrap(p):
    b = open(p, 'rb').read()
    return lz4.block.decompress(b[24:24+struct.unpack_from('<Q', b, 16)[0]], uncompressed_size=struct.unpack_from('<Q', b, 8)[0])
