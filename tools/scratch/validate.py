import json, re, sys
p = r"C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad"
src = json.load(open(p + r"\batches\b0080_dialog.json", encoding="utf-8"))
out = json.load(open(p + r"\translated\b0080_dialog.json", encoding="utf-8"))
BSN = "\\" + "n"   # literal backslash + n
NL = chr(10)
ok = True
assert len(src["items"]) == len(out["items"])
for s, o in zip(src["items"], out["items"]):
    st, ot = s["t"], o["t"]
    if s["i"] != o["i"]:
        print("I MISMATCH", s["i"], o["i"]); ok = False
    if st.count(BSN) != ot.count(BSN):
        print("BSN", s["i"], st.count(BSN), ot.count(BSN)); ok = False
    if st.count(NL) != ot.count(NL):
        print("NL", s["i"], st.count(NL), ot.count(NL)); ok = False
    for tag in set(re.findall(r"<ESC>C[A-Z]|<[0-9A-F]{2}>|%[sd]", st)):
        if st.count(tag) != ot.count(tag):
            print("TAG", s["i"], tag); ok = False
    if re.search(r"[぀-ヿ一-鿿]", ot):
        print("JP", s["i"]); ok = False
print("items", len(out["items"]), "ok", ok)
