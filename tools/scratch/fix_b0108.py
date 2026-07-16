import json, re, io

base = r"C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad"
a = json.load(open(base + r"\batches\b0108_dialog.json", encoding="utf-8"))
b = json.load(open(base + r"\translated\b0108_dialog.json", encoding="utf-8"))

BSN = chr(92) + "n"  # literal backslash + n
NL = chr(10)

for y in b["items"]:
    if NL in y["t"] and BSN not in y["t"]:
        y["t"] = y["t"].replace(NL, BSN)

with io.open(base + r"\translated\b0108_dialog.json", "w", encoding="utf-8") as f:
    json.dump({"items": b["items"]}, f, ensure_ascii=False, indent=0)

b = json.load(open(base + r"\translated\b0108_dialog.json", encoding="utf-8"))
assert [x["i"] for x in a["items"]] == [x["i"] for x in b["items"]], "i mismatch"
ok = True
for x, y in zip(a["items"], b["items"]):
    for tok in ["<ESC>CA", "<ESC>CB", "<ESC>CC", "<ESC>CZ", BSN, "%s", "%d"]:
        if x["t"].count(tok) != y["t"].count(tok):
            print("MISMATCH", repr(tok), x["i"], x["t"].count(tok), y["t"].count(tok))
            ok = False
    if re.search(u"[぀-ヿ一-鿿]", y["t"]):
        print("JP left", x["i"], y["t"])
        ok = False
print("count", len(b["items"]), "OK" if ok else "FAIL")
