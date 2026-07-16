# -*- coding: utf-8 -*-
import json

base = r"C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad"
out_path = base + r"\translated\b0097_dialog.json"
in_path = base + r"\batches\b0097_dialog.json"

data = json.load(open(out_path, encoding="utf-8"))
# convert real newlines in t to literal backslash+n token (as in input)
for it in data["items"]:
    it["t"] = it["t"].replace("\n", "\\n")

json.dump(data, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=0)

inp = json.load(open(in_path, encoding="utf-8"))
assert len(inp["items"]) == len(data["items"]), "count mismatch"
ok = True
for a, b in zip(inp["items"], data["items"]):
    assert a["i"] == b["i"]
    for tok in ("\\n", "<ESC>", "%s", "%d"):
        if a["t"].count(tok) != b["t"].count(tok):
            print("MISMATCH", a["i"], repr(tok), a["t"].count(tok), b["t"].count(tok))
            ok = False
    # no kana/kanji left
    for ch in b["t"]:
        o = ord(ch)
        if 0x3040 <= o <= 0x30FF or 0x4E00 <= o <= 0x9FFF:
            print("JP CHAR left in", a["i"], repr(ch))
            ok = False
print("count", len(data["items"]), "ok", ok)
