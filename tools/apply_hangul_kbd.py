# -*- coding: utf-8 -*-
"""Apply the Korean-input-method patch to the 1.1.7 PUK main (exefs/main, 872001).

Source of the patch: issue #1 (author @2seunghee), an xdelta3 delta built against our v4.0
1.1.7 PUK main. It adds a Korean IME (Switch system keyboard) and bypasses the name/reading
character-count validation so Korean names can be entered and existing generals edited.

This is a dependency-free re-expression of that delta (see hangul_kbd_117.patch.json), verified
to reproduce the official xdelta3 output byte-for-byte. Run BEFORE make_zip so the released
872001 exefs/main always carries the Korean input method.

Env: IN=<source main_872001>, OUT=<hangul main>, PATCH=<patch json>. Defaults target puk_mod_117."""
import os, sys, json, hashlib
sys.stdout.reconfigure(encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
IN = os.environ.get('IN') or r'D:\nsw\rom\nobu16_powerupkit\puk_mod_117\main_872001'
OUT = os.environ.get('OUT') or r'D:\nsw\rom\nobu16_powerupkit\puk_mod_117\main_872001_hangul'
PATCH = os.environ.get('PATCH') or os.path.join(HERE, 'hangul_kbd_117.patch.json')

p = json.load(open(PATCH, encoding='utf-8'))
src = open(IN, 'rb').read()
got = hashlib.sha256(src).hexdigest()
if got != p['source_sha256']:
    sys.exit(f'ERROR: source main mismatch.\n  {IN}\n  expected {p["source_sha256"]}\n  got      {got}\n'
             '이 main은 패치가 만들어진 v4.0 1.1.7 PUK main이 아닙니다. main을 재생성했다면 '
             'xdelta(원본)로 패치를 다시 생성해야 합니다.')

out = bytearray()
for op in p['ops']:
    if op[0] == 'C':          # copy source[off : off+len]
        out += src[op[1]:op[1]+op[2]]
    elif op[0] == 'L':        # literal bytes (hex)
        out += bytes.fromhex(op[1])
    elif op[0] == 'R':        # run: byte * len
        out += bytes([op[1]]) * op[2]
    else:
        sys.exit(f'unknown op {op!r}')
out = bytes(out)

if len(out) != p['target_size'] or hashlib.sha256(out).hexdigest() != p['target_sha256']:
    sys.exit(f'ERROR: patched output verification failed (size {len(out)} vs {p["target_size"]}).')

open(OUT, 'wb').write(out)
print(f'OK  {IN}  ->  {OUT}')
print(f'    size {len(src)} -> {len(out)} (+{len(out)-len(src)}), sha256 {p["target_sha256"][:16]}… verified')
