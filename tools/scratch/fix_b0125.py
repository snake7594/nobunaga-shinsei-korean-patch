import json, re, io, os

base = r"C:\Users\Jay\AppData\Local\Temp\claude\D--nsw-rom---------------------\8a0c5376-c8d9-41e4-a808-9c4db5b9c1a8\scratchpad"
src = json.load(open(os.path.join(base, "batches", "b0125_dialog.json"), encoding="utf-8"))
dst_path = os.path.join(base, "translated", "b0125_dialog.json")
dst = json.load(open(dst_path, encoding="utf-8-sig"))

BS_N = "\\" + "n"  # literal backslash + n

items = []
for x, y in zip(src["items"], dst["items"]):
    assert x["i"] == y["i"]
    t = y["t"]
    # convert any real newlines back to literal backslash-n token
    t = t.replace("\r\n", BS_N).replace("\n", BS_N)
    # counts must match input's literal \n tokens
    assert x["t"].count(BS_N) == t.count(BS_N), (x["i"], x["t"], t)
    # no kana/kanji remain
    assert not re.search(r"[぀-ヿ一-鿿]", t), (x["i"], t)
    items.append({"i": y["i"], "t": t})

assert len(items) == len(src["items"]) == 60
with open(dst_path, "w", encoding="utf-8") as f:
    json.dump({"items": items}, f, ensure_ascii=False, indent=1)
print("ok", len(items))
