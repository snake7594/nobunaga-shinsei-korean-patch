# -*- coding: utf-8 -*-
import json, re, sys
BASE = r"C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad"
src = BASE + r"\batches\b0149_dialog.json"
dst = BASE + r"\translated\b0149_dialog.json"
LIT = "\\" + "n"   # literal backslash + n (2 chars)
NL = chr(10)       # real newline

s = json.load(open(src, encoding="utf-8"))
d = json.load(open(dst, encoding="utf-8"))

bad = []
for a, b in zip(s["items"], d["items"]):
    src_lit = a["t"].count(LIT)
    src_real = a["t"].count(NL)
    t = b["t"]
    if src_lit > 0 and src_real == 0:
        # source uses literal backslash-n tokens; convert any real newlines in dst
        t = t.replace(NL, LIT)
    elif src_real > 0 and src_lit == 0:
        t = t.replace(LIT, NL)
    b["t"] = t
    if a["i"] != b["i"] or t.count(LIT) != src_lit or t.count(NL) != src_real:
        bad.append((a["i"], src_lit, src_real, t.count(LIT), t.count(NL)))
    if re.search(u"[぀-ヿ一-鿿]", t):
        bad.append((a["i"], "kana/kanji remains"))

with open(dst, "w", encoding="utf-8") as f:
    json.dump({"cat": "dialog", "items": d["items"]}, f, ensure_ascii=False, indent=0)

print("items:", len(d["items"]))
print("bad:", bad)
print("src0 lit/real:", s["items"][0]["t"].count(LIT), s["items"][0]["t"].count(NL))
print("dst0 lit/real:", d["items"][0]["t"].count(LIT), d["items"][0]["t"].count(NL))
