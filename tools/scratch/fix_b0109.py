# -*- coding: utf-8 -*-
import json, re
base = r"C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad"
src = json.load(open(base + r"\batches\b0109_dialog.json", encoding="utf-8"))
raw = open(base + r"\translated\b0109_dialog.json", encoding="utf-8").read()
# translated file currently has raw "\n" (single backslash) which decodes to newline;
# input uses "\\n" (literal backslash+n token). Double them if needed.
if "\\\\n" not in raw:
    raw = raw.replace("\\n", "\\\\n")
out = json.loads(raw)
with open(base + r"\translated\b0109_dialog.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=0)
a = {x["i"]: x["t"] for x in src["items"]}
b = {x["i"]: x["t"] for x in out["items"]}
assert set(a) == set(b), "index mismatch"
for i in a:
    assert a[i].count("\\n") == b[i].count("\\n"), ("newline count", i)
    assert len(re.findall(r"<ESC>..", a[i])) == len(re.findall(r"<ESC>..", b[i])), ("esc count", i)
    assert not re.search(u"[ぁ-ヿ一-鿿]", b[i]), ("kana/hanja remains", i)
print("OK", len(b))
