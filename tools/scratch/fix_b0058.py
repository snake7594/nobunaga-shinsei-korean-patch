import json, re

base = r"C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad"
out_path = base + r"\translated\b0058_dialog.json"
src_path = base + r"\batches\b0058_dialog.json"

NL_TOKEN = "\\" + "n"  # literal backslash + n

d = json.load(open(out_path, encoding="utf-8"))
for it in d["items"]:
    # normalize: real newlines -> literal backslash-n token
    it["t"] = it["t"].replace("\n", NL_TOKEN)

with open(out_path, "w", encoding="utf-8") as f:
    json.dump(d, f, ensure_ascii=False, indent=0)

src = json.load(open(src_path, encoding="utf-8"))
assert len(d["items"]) == len(src["items"]) == 60, len(d["items"])
problems = []
for a, b in zip(src["items"], d["items"]):
    if a["i"] != b["i"]:
        problems.append(("i-mismatch", a["i"], b["i"]))
    if a["t"].count(NL_TOKEN) != b["t"].count(NL_TOKEN):
        problems.append(("nl", a["i"], a["t"].count(NL_TOKEN), b["t"].count(NL_TOKEN)))
    if len(re.findall(r"<ESC>..", a["t"])) != len(re.findall(r"<ESC>..", b["t"])):
        problems.append(("esc", a["i"]))
    if re.search(r"[぀-ヿ一-鿿]", b["t"]):
        problems.append(("kana/kanji", b["i"]))
if problems:
    print("PROBLEMS:", problems)
else:
    print("OK", len(d["items"]))
