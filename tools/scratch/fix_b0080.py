import json
p = r"C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad"
f = p + r"\translated\b0080_dialog.json"
out = json.load(open(f, encoding="utf-8"))
BSN = "\\" + "n"
NL = chr(10)
items = [{"i": o["i"], "t": o["t"].replace(NL, BSN)} for o in out["items"]]
json.dump({"items": items}, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("fixed", len(items))
