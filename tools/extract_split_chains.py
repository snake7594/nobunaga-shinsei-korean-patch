# -*- coding: utf-8 -*-
"""Extract split-sentence chains from msggame (base + PK):
parse each blob's ordered text runs; group consecutive runs where the sentence
continues across the boundary; emit groups with JP fragments + current KO (tr dict).
Also count in-string kana-stutter candidates in table bins."""
import sys, os, struct, json, re
from collections import OrderedDict
sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import apply_translations as A

TR = json.load(open(os.path.join(SP, 'tr_all.json'), encoding='utf-8'))

def blob_runs(dec):
    """Yield lists of runs per blob: [(esc_text), ...]"""
    count = struct.unpack_from('<I', dec, 0)[0]
    for i in range(count):
        off, size = struct.unpack_from('<II', dec, 4 + i*8)
        n = struct.unpack_from('<I', dec, off)[0]
        offs = struct.unpack_from(f'<{n}I', dec, off + 4)
        ends = list(offs[1:]) + [size]
        for j in range(n):
            blob = dec[off + offs[j]: off + ends[j]]
            runs = []
            p = 0
            while True:
                st = blob.find(b'\x07\x07\x01', p)
                if st < 0:
                    break
                en = blob.find(b'\x07\x07\x02', st + 3)
                if en < 0:
                    break
                raw = blob[st+3:en]
                if len(raw) % 2 == 0 and len(raw) > 0:
                    cus = struct.unpack_from(f'<{len(raw)//2}H', raw)
                    runs.append(A.esc(cus))
                p = en + 3
            if runs:
                yield runs

# sentence-boundary heuristics on JP fragments
END_OK = re.compile(r'[。！？…♪」』）\)]\s*$|\\n$|^$')
CONT_START = re.compile(r'^(は|が|を|に|で|と|も|の|へ|や|ば|から|まで| より|ました|ます|です|でした|だ|な|ね|よ|ぞ|か[。！？]|たる|れる|られ|せる|した|して|、)')

def is_split(prev_jp, next_jp):
    if not prev_jp or not next_jp:
        return False
    if END_OK.search(prev_jp):
        return False
    return True   # any mid-sentence run boundary counts; refine via next-start too

chains = OrderedDict()   # key: tuple of JP fragments -> {'jp':[...], 'ko':[...], 'n': count}
for name, path in [('base', r'D:\nsw\merged_sel\MSG\JP\msggame.bin'),
                   ('pk', r'D:\nsw\rom\1.1.5\Program 1\romfs\MSG_PK\JP\msggame.bin')]:
    hdr, dec = A.kt_unwrap(open(path, 'rb').read())
    n_groups = 0
    for runs in blob_runs(dec):
        # group consecutive runs into chains while split continues
        cur = [runs[0]]
        for k in range(1, len(runs)):
            if is_split(runs[k-1], runs[k]):
                cur.append(runs[k])
            else:
                if len(cur) > 1:
                    key = tuple(cur)
                    if key not in chains:
                        chains[key] = {'jp': cur, 'ko': [TR.get(x) for x in cur], 'n': 0}
                    chains[key]['n'] += 1
                    n_groups += 1
                cur = [runs[k]]
        if len(cur) > 1:
            key = tuple(cur)
            if key not in chains:
                chains[key] = {'jp': cur, 'ko': [TR.get(x) for x in cur], 'n': 0}
            chains[key]['n'] += 1
            n_groups += 1
    print(f'{name}: split groups found so far (cumulative unique): {len(chains)}')

# keep only chains where every fragment has a KO translation and at least one fragment is
# JP-translated text (skip pure-numeric/format chains)
JPCH = re.compile(r'[ぁ-ゖァ-ヺ一-鿿]')
final = []
for key, v in chains.items():
    if any(k is None for k in v['ko']):
        continue
    if not any(JPCH.search(x) for x in v['jp']):
        continue
    final.append(v)
print('usable unique chains:', len(final))
lens = {}
for v in final:
    lens[len(v['jp'])] = lens.get(len(v['jp']), 0) + 1
print('chain length histogram:', dict(sorted(lens.items())))
json.dump(final, open(os.path.join(SP, 'split_chains.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('sample chains:')
for v in final[:6]:
    print('  JP:', [x[:26] for x in v['jp']])
    print('  KO:', [x[:26] for x in v['ko']])
