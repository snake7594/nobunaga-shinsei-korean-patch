import json, re, io, sys
base = r"C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad"
src = json.load(io.open(base + r"\batches\b0020_dialog.json", encoding="utf-8"))
out = json.load(io.open(base + r"\translated\b0020_dialog.json", encoding="utf-8"))
assert [x["i"] for x in src["items"]] == [x["i"] for x in out["items"]], "i mismatch"
NL = "\\" + "n"  # literal backslash-n token in parsed string
bad = []
for s, o in zip(src["items"], out["items"]):
    if s["t"].count(NL) != o["t"].count(NL):
        bad.append((s["i"], "nl", s["t"].count(NL), o["t"].count(NL)))
    if s["t"].count("<ESC>") != o["t"].count("<ESC>"):
        bad.append((s["i"], "esc", s["t"].count("<ESC>"), o["t"].count("<ESC>")))
    if re.search(u"[぀-ヿ一-鿿]", o["t"]):
        bad.append((o["i"], "kana/kanji"))
    if "\n" in o["t"]:
        bad.append((o["i"], "real newline"))
print(len(out["items"]), bad)
