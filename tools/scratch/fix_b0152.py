import json

base = r"C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad"
inp = base + r"\batches\b0152_dialog.json"
out = base + r"\translated\b0152_dialog.json"

BS_N = chr(92) + "n"  # literal backslash + n
NL = chr(10)

d = json.load(open(out, encoding="utf-8"))
for it in d["items"]:
    it["t"] = it["t"].replace(NL, BS_N)
json.dump(d, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=0)

a = json.load(open(inp, encoding="utf-8"))["items"]
b = json.load(open(out, encoding="utf-8"))["items"]
assert [x["i"] for x in a] == [x["i"] for x in b], "i mismatch"
bad = [x["i"] for x, y in zip(a, b) if x["t"].count(BS_N) != y["t"].count(BS_N)]
import re
jp = [y["i"] for y in b if re.search(r"[ぁ-ゟァ-ヺ一-鿿]", y["t"])]
print("count", len(b))
print("newline-token mismatches:", bad)
print("remaining kana/kanji:", jp)
