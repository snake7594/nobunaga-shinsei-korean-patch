import json, re, sys
base = r"C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad"
src = json.load(open(base + r"\batches\b0267_dialog.json", encoding="utf-8"))
out = json.load(open(base + r"\translated\b0267_dialog.json", encoding="utf-8"))
BSN = chr(92) + "n"  # literal backslash + n
NL = chr(10)
items = []
for s, o in zip(src["items"], out["items"]):
    assert s["i"] == o["i"]
    t = o["t"]
    # normalize: output may contain real newlines; source uses literal \n tokens
    t = t.replace(NL, BSN)
    if t.count(BSN) != s["t"].count(BSN):
        print("LINEBREAK MISMATCH", s["i"], t.count(BSN), s["t"].count(BSN))
        sys.exit(1)
    if len(re.findall("<ESC>", t)) != len(re.findall("<ESC>", s["t"])):
        print("ESC MISMATCH", s["i"])
        sys.exit(1)
    items.append({"i": o["i"], "t": t})
assert len(items) == len(src["items"])
with open(base + r"\translated\b0267_dialog.json", "w", encoding="utf-8") as f:
    json.dump({"items": items}, f, ensure_ascii=False, indent=0)
print("OK", len(items))
