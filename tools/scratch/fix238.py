import json, re, sys
base = r"C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad"
inp = json.load(open(base + r"\batches\b0238_dialog.json", encoding="utf-8"))
out = json.load(open(base + r"\translated\b0238_dialog.json", encoding="utf-8"))

NL = "\n"        # real newline
LIT = "\\n"      # backslash + n (literal token, as in input)

for it in out["items"]:
    if NL in it["t"]:
        it["t"] = it["t"].replace(NL, LIT)

assert len(inp["items"]) == len(out["items"]) == 60
for a, b in zip(inp["items"], out["items"]):
    assert a["i"] == b["i"]
    assert a["t"].count(LIT) == b["t"].count(LIT), (a["i"], a["t"].count(LIT), b["t"].count(LIT))
    assert re.findall(r"<ESC>[A-Z]{2}", a["t"]) == re.findall(r"<ESC>[A-Z]{2}", b["t"]), a["i"]
    assert re.findall(r"\[b?m?\d+\]", a["t"]) == re.findall(r"\[b?m?\d+\]", b["t"]), a["i"]
    assert not re.search(u"[぀-゚ァ-ヺ一-鿿]", b["t"]), (a["i"], ascii(b["t"]))

with open(base + r"\translated\b0238_dialog.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=0)
print("OK", len(out["items"]))
