import json, re

base = r"C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad"
src = json.load(open(base + r"\batches\b0244_dialog.json", encoding="utf-8"))
out = json.load(open(base + r"\translated\b0244_dialog.json", encoding="utf-8"))

assert len(src["items"]) == len(out["items"]) == 60
LIT = "\\" + "n"  # literal backslash + n
for s, o in zip(src["items"], out["items"]):
    assert s["i"] == o["i"]
    o["t"] = o["t"].replace("\n", LIT)
    assert s["t"].count(LIT) == o["t"].count(LIT), (s["i"], s["t"], o["t"])
    assert re.search(r"[ぁ-ゖァ-ヺー-ヿ一-鿿]", o["t"]) is None, ("kana/kanji", s["i"], o["t"])
    for tag in re.findall(r"<ESC>..", s["t"]):
        assert tag in o["t"], (s["i"], tag)

json.dump(out, open(base + r"\translated\b0244_dialog.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("OK", len(out["items"]))
