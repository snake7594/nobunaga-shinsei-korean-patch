# -*- coding: utf-8 -*-
import json, re, io

base = r"C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad"
src_raw = io.open(base + r"\batches\b0011_dialog.json", encoding="utf-8").read()
# Determine token form in source raw text: literal backslash-backslash-n vs backslash-n
double_form = src_raw.count("\\\\n")
single_form = src_raw.count("\\n") - 2 * double_form  # occurrences of \n not part of \\n
print("raw source: double(\\\\n)=", double_form, " single(\\n)=", single_form)

src = json.loads(src_raw)
out = json.load(io.open(base + r"\translated\b0011_dialog.json", encoding="utf-8"))

BSN = "\\n"  # literal backslash + n (2 chars)

def src_token_count(s):
    # source parsed strings: if raw had \\n, parsed contains literal \n (BSN); if raw had \n, parsed contains newline
    return s.count(BSN) + s.count("\n")

items = []
for it in out["items"]:
    t = it["t"]
    if double_form > 0:
        # target parsed strings must contain literal backslash+n
        t = t.replace("\n", BSN)
    else:
        t = t.replace(BSN, "\n")
    items.append({"i": it["i"], "t": t})

s = {it["i"]: it["t"] for it in src["items"]}
t = {it["i"]: it["t"] for it in items}
bad = []
for i in s:
    if src_token_count(s[i]) != (t[i].count(BSN) + t[i].count("\n")):
        bad.append((i, "nl", src_token_count(s[i]), t[i].count(BSN) + t[i].count("\n")))
    if len(re.findall(r"<ESC>..", s[i])) != len(re.findall(r"<ESC>..", t[i])):
        bad.append((i, "esc"))
    if re.search(u"[぀-ヿ一-鿿]", t[i]):
        bad.append((i, "jp"))

with io.open(base + r"\translated\b0011_dialog.json", "w", encoding="utf-8") as f:
    json.dump({"items": items}, f, ensure_ascii=False, indent=0)

chk = io.open(base + r"\translated\b0011_dialog.json", encoding="utf-8").read()
print("out raw double form count:", chk.count("\\\\n"))
print("count", len(items), "bad", bad)
