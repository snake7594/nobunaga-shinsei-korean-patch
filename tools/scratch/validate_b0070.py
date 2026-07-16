import io, json, re, sys

base = r"C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad"
out = json.load(io.open(base + r"\translated\b0070_dialog.json", encoding="utf-8"))
src = json.load(io.open(base + r"\batches\b0070_dialog.json", encoding="utf-8"))

assert len(out["items"]) == len(src["items"]), (len(out["items"]), len(src["items"]))
bad = []
for a, b in zip(out["items"], src["items"]):
    if a["i"] != b["i"]:
        bad.append(("i-mismatch", a["i"], b["i"]))
    if a["t"].count("\\n") != b["t"].count("\\n"):
        bad.append(("nl-count", a["i"], a["t"].count("\\n"), b["t"].count("\\n")))
    if re.search(r"[぀-ヿ一-鿿]", a["t"]):
        bad.append(("kana/kanji", a["i"], a["t"]))
if bad:
    print("BAD:", bad)
    sys.exit(1)
print("OK", len(out["items"]))
