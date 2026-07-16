# -*- coding: utf-8 -*-
import json, io, os

base = r"C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad"
out_path = os.path.join(base, "translated", "b0117_dialog.json")
src_path = os.path.join(base, "batches", "b0117_dialog.json")

BSN = "\\" + "n"  # literal backslash + n (two chars)
NL = chr(10)

with io.open(out_path, encoding="utf-8") as f:
    d = json.load(f)
with io.open(src_path, encoding="utf-8") as f:
    src = json.load(f)

# Convert real newlines in translated values to literal backslash-n tokens
for it in d["items"]:
    it["t"] = it["t"].replace(NL, BSN)

assert len(src["items"]) == len(d["items"]) == 60, (len(src["items"]), len(d["items"]))
for a, b in zip(src["items"], d["items"]):
    assert a["i"] == b["i"]
    ca, cb = a["t"].count(BSN), b["t"].count(BSN)
    assert ca == cb, (a["i"], ca, cb, b["t"])
    # no kana/kanji remaining
    for ch in b["t"]:
        o = ord(ch)
        assert not (0x3040 <= o <= 0x30FF or 0x4E00 <= o <= 0x9FFF), (b["i"], ch)

with io.open(out_path, "w", encoding="utf-8") as f:
    json.dump(d, f, ensure_ascii=False, indent=0)

print("OK", len(d["items"]))
