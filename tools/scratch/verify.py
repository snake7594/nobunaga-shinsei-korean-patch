# -*- coding: utf-8 -*-
import json, re, sys

base = r"C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad"
src_raw = open(base + r"\batches\b0019_dialog.json", encoding="utf-8").read()
out_raw = open(base + r"\translated\b0019_dialog.json", encoding="utf-8").read()

BSN = "\\" + "n"          # backslash + n (2 chars)
DBSN = "\\\\" + "n"        # two backslashes + n (3 chars)
print("src raw: double-bs-n =", src_raw.count(DBSN), " single-bs-n(total incl double) =", src_raw.count(BSN))
print("out raw: double-bs-n =", out_raw.count(DBSN), " single-bs-n(total incl double) =", out_raw.count(BSN))

src = json.loads(src_raw)["items"]
out = json.loads(out_raw)["items"]
print("counts:", len(src), len(out))

ok = True
for s, o in zip(src, out):
    if s["i"] != o["i"]:
        ok = False; print("idx mismatch", s["i"], o["i"])
    # decoded token comparison
    for tok in [BSN, "\n", "<ESC>", "%s", "%d"]:
        cs, co = s["t"].count(tok), o["t"].count(tok)
        if cs != co:
            ok = False; print("i=%d tok=%r src=%d out=%d" % (s["i"], tok, cs, co))
    if re.search(u"[぀-ヿ一-鿿]", o["t"]):
        ok = False; print("JP char left in i=", o["i"])
print("ALL OK" if ok else "ERRORS")
