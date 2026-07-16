import json, re
base = r"C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad"
src = json.load(open(base + r"\batches\b0253_dialog.json", encoding="utf-8"))
out = json.load(open(base + r"\translated\b0253_dialog.json", encoding="utf-8"))

BSN = chr(92) + "n"  # literal backslash + n (2 chars)
NL = chr(10)
fixed = []
issues = []
for s, o in zip(src["items"], out["items"]):
    t = o["t"].replace(NL, BSN)
    if s["i"] != o["i"]:
        issues.append(("i mismatch", s["i"], o["i"]))
    if s["t"].count(BSN) != t.count(BSN):
        issues.append(("linebreak", s["i"], s["t"].count(BSN), t.count(BSN)))
    if s["t"].count("<ESC>") != t.count("<ESC>"):
        issues.append(("esc", s["i"]))
    if re.search(u"[぀-ヿ一-鿿]", t):
        issues.append(("kana/kanji", s["i"]))
    fixed.append({"i": o["i"], "t": t})

assert len(fixed) == len(src["items"]) == 60
with open(base + r"\translated\b0253_dialog.json", "w", encoding="utf-8") as f:
    json.dump({"items": fixed}, f, ensure_ascii=False, indent=1)

with open(base + r"\fixreport.txt", "w", encoding="utf-8") as report:
    if issues:
        for x in issues:
            report.write(repr(x) + "\n")
    else:
        report.write("ALL OK 60\n")
