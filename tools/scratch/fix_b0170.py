import json, re, os
base = r"C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad"
bs = chr(92)
nl = chr(10)
TOK = bs + "n"

src = json.load(open(os.path.join(base, "batches", "b0170_dialog.json"), encoding="utf-8"))
out_path = os.path.join(base, "translated", "b0170_dialog.json")
out = json.load(open(out_path, encoding="utf-8"))

for it in out["items"]:
    it["t"] = it["t"].replace(nl, TOK)

with open(out_path, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

assert len(src["items"]) == len(out["items"]) == 60
ok = True
for a, b in zip(src["items"], out["items"]):
    assert a["i"] == b["i"]
    for tok in ["<ESC>CA", "<ESC>CB", "<ESC>CC", "<ESC>CZ", TOK, "%s", "%d"]:
        if a["t"].count(tok) != b["t"].count(tok):
            print("MISMATCH", a["i"], repr(tok), a["t"].count(tok), b["t"].count(tok))
            ok = False
    if nl in b["t"]:
        print("REAL NEWLINE", b["i"])
        ok = False
    if re.search(u"[ぁ-ヿ一-鿿]", b["t"]):
        print("JP CHARS", b["i"], b["t"])
        ok = False
print("OK" if ok else "ISSUES", len(out["items"]))
