import json, re

base = r"C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad"
src = json.load(open(base + r"\batches\b0007_dialog.json", encoding="utf-8"))
out = json.load(open(base + r"\translated\b0007_dialog.json", encoding="utf-8"))

BSN = "\\" + "n"  # literal backslash + n

items = []
for it in out["items"]:
    items.append({"i": it["i"], "t": it["t"].replace("\n", BSN)})

assert len(items) == len(src["items"])
for s, o in zip(src["items"], items):
    assert s["i"] == o["i"]
    assert s["t"].count(BSN) == o["t"].count(BSN), (s["i"], s["t"].count(BSN), o["t"].count(BSN))
    assert s["t"].count("<ESC>") == o["t"].count("<ESC>"), s["i"]
    assert re.findall(r"<ESC>C[A-Z]", s["t"]) == re.findall(r"<ESC>C[A-Z]", o["t"]), s["i"]
    assert not re.search(r"[぀-ヿ一-鿿]", o["t"]), (s["i"], o["t"])
    # bracket tokens like [b754] preserved
    assert sorted(re.findall(r"\[b[m0-9]+\]", s["t"])) == sorted(re.findall(r"\[b[m0-9]+\]", o["t"])), s["i"]

json.dump({"items": items}, open(base + r"\translated\b0007_dialog.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("OK", len(items))
