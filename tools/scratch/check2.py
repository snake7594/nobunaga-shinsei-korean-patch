# -*- coding: utf-8 -*-
import json, re
base = r"C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad"
src = json.load(open(base + r"\batches\b0119_dialog.json", encoding="utf-8"))
out = json.load(open(base + r"\translated\b0119_dialog.json", encoding="utf-8"))
assert [x["i"] for x in src["items"]] == [x["i"] for x in out["items"]], "i mismatch"
BS_N = "\\" + "n"  # literal backslash + n
ok = True
for s, o in zip(src["items"], out["items"]):
    if s["t"].count(BS_N) != o["t"].count(BS_N):
        print("NL", s["i"], s["t"].count(BS_N), o["t"].count(BS_N)); ok = False
    if s["t"].count("<ESC>") != o["t"].count("<ESC>"):
        print("ESC", s["i"]); ok = False
    jp = re.findall(u"[ぁ-ゖァ-ヺ一-鿿]", o["t"])
    if jp:
        print("JP", o["i"], "".join(jp)); ok = False
print("items", len(out["items"]), "OK" if ok else "FAIL")
