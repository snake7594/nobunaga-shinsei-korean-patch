# -*- coding: utf-8 -*-
"""Full hash-based diff of 1.1.5 vs 1.1.7 extracted romfs, per program.
Report: added / removed / changed files, grouped by top-level dir."""
import os, sys, hashlib, json
from collections import defaultdict
sys.stdout.reconfigure(encoding='utf-8')

BASE = {
    'P0': (r'D:\nsw\rom\1.1.5\Program 0\romfs', r'D:\nsw\rom\1.1.7\extract\Program 0\romfs'),
    'P1': (r'D:\nsw\rom\1.1.5\Program 1\romfs', r'D:\nsw\rom\1.1.7\extract\Program 1\romfs'),
}

def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()

def tree(root):
    out = {}
    for dp, _, fs in os.walk(root):
        for f in fs:
            full = os.path.join(dp, f)
            rel = os.path.relpath(full, root).replace(os.sep, '/')
            out[rel] = (os.path.getsize(full), full)
    return out

report = {}
for prog, (r5, r7) in BASE.items():
    t5, t7 = tree(r5), tree(r7)
    added = sorted(set(t7) - set(t5))
    removed = sorted(set(t5) - set(t7))
    common = sorted(set(t5) & set(t7))
    changed = []
    for rel in common:
        if t5[rel][0] != t7[rel][0] or sha(t5[rel][1]) != sha(t7[rel][1]):
            changed.append((rel, t5[rel][0], t7[rel][0]))
    report[prog] = {'added': added, 'removed': removed, 'changed': changed}
    print(f'== {prog}: +{len(added)} added, -{len(removed)} removed, ~{len(changed)} changed ==')
    def topdir(p): return p.split('/')[0]
    for label, items in [('ADDED', added), ('REMOVED', removed)]:
        by = defaultdict(list)
        for x in items:
            by[topdir(x)].append(x)
        for d, xs in sorted(by.items()):
            print(f'  {label} {d}/: {len(xs)}')
            for x in xs[:40]:
                print(f'      {x}')
    if changed:
        by = defaultdict(list)
        for rel, s5, s7 in changed:
            by[topdir(rel)].append((rel, s5, s7))
        for d, xs in sorted(by.items()):
            print(f'  CHANGED {d}/: {len(xs)}')
            for rel, s5, s7 in xs[:40]:
                print(f'      {rel}  {s5:,} -> {s7:,}')

SP = os.path.dirname(os.path.abspath(__file__))
json.dump(report, open(os.path.join(SP, 'diff_115_117.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('\nsaved diff_115_117.json')
