import json, re
base = r"C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad"
bs, nl = chr(92), chr(10)
out_path = base + r"\translated\b0088_dialog.json"
data = json.load(open(out_path, encoding="utf-8"))
for it in data["items"]:
    it["t"] = it["t"].replace(nl, bs + "n")
src = json.load(open(base + r"\batches\b0088_dialog.json", encoding="utf-8"))
assert len(src["items"]) == len(data["items"]), len(data["items"])
tokens = ["<ESC>CA", "<ESC>CB", "<ESC>CC", "<ESC>CZ", bs + "n"]
ok = True
for a, b in zip(src["items"], data["items"]):
    assert a["i"] == b["i"]
    for tok in tokens:
        if a["t"].count(tok) != b["t"].count(tok):
            print("MISMATCH", a["i"], repr(tok), a["t"].count(tok), b["t"].count(tok))
            ok = False
    if re.search(u"[ぁ-ヿ一-鿿]", b["t"]):
        print("JP CHARS", b["i"])
        ok = False
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=1)
print("OK" if ok else "ISSUES", len(data["items"]))
