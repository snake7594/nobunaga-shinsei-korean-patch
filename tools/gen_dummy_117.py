# -*- coding: utf-8 -*-
"""Auto-translate the 1,106 formulaic dummy placeholder strings using established terms,
and split out the genuinely-new content strings for manual translation."""
import json, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))
items = json.load(open(os.path.join(SP, 'trans117_input.json'), encoding='utf-8'))

# established terms: 奉行=부교, 家宰=가재, 効果=효과, 名所=명소, 防衛設備=방위 설비
RULES = [
    (re.compile(r'^効果(\d+)ダミー説明$'),                 lambda m: f'효과{m.group(1)} 더미 설명'),
    (re.compile(r'^名所(\d+)ダミールビ$'),                 lambda m: f'명소{m.group(1)} 더미 루비'),
    (re.compile(r'^名所(\d+)ダミー説明$'),                 lambda m: f'명소{m.group(1)} 더미 설명'),
    (re.compile(r'^奉行効果(\d+)ダミー説明$'),             lambda m: f'부교 효과{m.group(1)} 더미 설명'),
    (re.compile(r'^奉行(\d+)ダミールビ$'),                 lambda m: f'부교{m.group(1)} 더미 루비'),
    (re.compile(r'^奉行(\d+)ダミー説明$'),                 lambda m: f'부교{m.group(1)} 더미 설명'),
    (re.compile(r'^家宰効果(\d+)リスト用ダミー説明$'),      lambda m: f'가재 효과{m.group(1)} 리스트용 더미 설명'),
    (re.compile(r'^家宰効果(\d+)ダミー説明$'),             lambda m: f'가재 효과{m.group(1)} 더미 설명'),
    (re.compile(r'^家宰(\d+)ダミールビ$'),                 lambda m: f'가재{m.group(1)} 더미 루비'),
    (re.compile(r'^家宰(\d+)ダミー説明$'),                 lambda m: f'가재{m.group(1)} 더미 설명'),
    (re.compile(r'^防衛設備(\d+)ダミールビ$'),             lambda m: f'방위 설비{m.group(1)} 더미 루비'),
    (re.compile(r'^防衛設備(\d+)ダミー説明$'),             lambda m: f'방위 설비{m.group(1)} 더미 설명'),
]

auto, rest = {}, []
for it in items:
    jp = it['jp']
    hit = None
    for rx, fn in RULES:
        m = rx.match(jp)
        if m:
            hit = fn(m); break
    if hit:
        auto[jp] = hit
    else:
        rest.append(jp)

json.dump(auto, open(os.path.join(SP, 'auto_dummy_117.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=0)
json.dump(rest, open(os.path.join(SP, 'real_new_117.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print(f'auto-translated dummies: {len(auto)}')
print(f'genuinely-new needing manual translation: {len(rest)}')
leftover_dummy = [s for s in rest if 'ダミー' in s]
print(f'  (dummy-ish not matched by rules: {len(leftover_dummy)})')
for s in leftover_dummy[:10]:
    print('   ', s)
