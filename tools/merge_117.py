# -*- coding: utf-8 -*-
"""Merge all 1.1.7 translations (auto dummies + manual A/B/C/D) into tr_all_117.json,
validating token preservation against each JP source string."""
import json, os, re, sys, importlib.util
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))

def load(mod):
    spec = importlib.util.spec_from_file_location(mod, os.path.join(SP, mod + '.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

real = json.load(open(os.path.join(SP, 'real_new_117.json'), encoding='utf-8'))
new = {}
for mod in ['tr117_manual_a', 'tr117_manual_b', 'tr117_manual_c']:
    new.update(load(mod).TR)
byidx = load('tr117_manual_d').BY_INDEX
for i, ko in byidx.items():
    new[real[i]] = ko
auto = json.load(open(os.path.join(SP, 'auto_dummy_117.json'), encoding='utf-8'))
new.update(auto)

# coverage
allneed = json.load(open(os.path.join(SP, 'need117_final.json'), encoding='utf-8'))
missing = [s for s in allneed if s not in new]
print(f'new translations: {len(new)}  | need: {len(allneed)} | missing: {len(missing)}')
for s in missing[:10]:
    print('  MISSING:', repr(s[:60]))

# token validation
TOK = re.compile(r'<ESC>..|<[0-9A-F]{2}>|\\n|\\t|%[sd0-9]')
def toks(s): return Counter(TOK.findall(s))
bad = [(j, k) for j, k in new.items() if toks(j) != toks(k)]
print(f'token mismatches: {len(bad)}')
for j, k in bad[:12]:
    print('  JP:', repr(j[:60]), dict(toks(j)))
    print('  KO:', repr(k[:60]), dict(toks(k)))

# kana leftovers in KO (should be none except intentional yomigana keys)
KANA = re.compile(r'[ぁ-ゖァ-ヺ]')
kana_ko = [(j, k) for j, k in new.items() if KANA.search(k)]
print(f'KO values containing kana (intentional yomigana expected): {len(kana_ko)}')
for j, k in kana_ko[:8]:
    print('   ', repr(j[:34]), '->', repr(k[:34]))

# build merged dict for the 1.1.7 build
BIG = json.load(open(os.path.join(SP, 'big_dict.json'), encoding='utf-8'))
merged = dict(BIG)
merged.update(new)
json.dump(merged, open(os.path.join(SP, 'tr_all_117.json'), 'w', encoding='utf-8'), ensure_ascii=False)
json.dump(new, open(os.path.join(SP, 'new117_translations.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print(f'\ntr_all_117.json written: {len(merged)} entries (base {len(BIG)} + new {len(new)})')
