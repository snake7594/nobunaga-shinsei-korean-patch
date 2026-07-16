# -*- coding: utf-8 -*-
import json

base = r"C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad"
out_path = base + r"\translated\b0111_dialog.json"
src_path = base + r"\batches\b0111_dialog.json"

raw = open(out_path, encoding="utf-8").read()
# file currently has single backslash+n inside JSON strings -> double it
raw = raw.replace("\\n", "\\\\n")
d = json.loads(raw)
src = json.load(open(src_path, encoding="utf-8"))

assert len(d["items"]) == len(src["items"]) == 60, (len(d["items"]), len(src["items"]))
for a, b in zip(src["items"], d["items"]):
    assert a["i"] == b["i"]
    assert a["t"].count("\\n") == b["t"].count("\\n"), (a["i"], a["t"], b["t"])
    assert a["t"].count("<ESC>") == b["t"].count("<ESC>"), a["i"]

with open(out_path, "w", encoding="utf-8") as f:
    json.dump(d, f, ensure_ascii=False, indent=0)
print("ok", len(d["items"]))
