import json, re
base = r"C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad"
a = json.load(open(base + r"\batches\b0296_dialog.json", encoding="utf-8"))
b = json.load(open(base + r"\translated\b0296_dialog.json", encoding="utf-8"))
assert [x["i"] for x in a["items"]] == [x["i"] for x in b["items"]], "i mismatch"
ok = True
for x, y in zip(a["items"], b["items"]):
    if x["t"].count("\\n") != y["t"].count("\\n"):
        print("NL mismatch", x["i"], x["t"].count("\\n"), y["t"].count("\\n")); ok = False
    ta = re.findall(r"<ESC>C[A-Z]|\[bm\d+\]", x["t"]); tb = re.findall(r"<ESC>C[A-Z]|\[bm\d+\]", y["t"])
    if ta != tb:
        print("tag mismatch", x["i"]); ok = False
    if re.search(u"[ぁ-ゖァ-ヺ一-鿿]", y["t"]):
        print("kana/kanji left", x["i"]); ok = False
print("count", len(b["items"]), "OK" if ok else "FAIL")
