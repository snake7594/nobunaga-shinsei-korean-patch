# -*- coding: utf-8 -*-
import json

base = r"C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad"
p = base + r"\translated\b0019_dialog.json"
data = json.load(open(p, encoding="utf-8"))
BSN = "\\" + "n"
for it in data["items"]:
    it["t"] = it["t"].replace("\n", BSN)
with open(p, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=1)
print("fixed", len(data["items"]))
