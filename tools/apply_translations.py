"""Apply translated batches to MSG files: validate, rebuild strdata/ev_strdata/msggame.

Usage: python apply_translations.py <out_dir> [--report-only]
Also writes used_chars.txt (Hangul beyond base charset) and translation_report.txt.
"""
import struct, sys, os, json, re, glob
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))
SRC = r'D:\nsw\rom\노부나가의 야망 신생_일본판\추출원본'

# ---------- escape helpers (same as prep_batches) ----------
def esc(cus):
    s = ''
    for cu in cus:
        if cu == 0x1B: s += '<ESC>'
        elif cu == 0x0A: s += '\\n'
        elif cu == 0x09: s += '\\t'
        elif cu == 0x5C: s += '\\\\'
        elif cu < 0x20: s += f'<{cu:02X}>'
        else: s += chr(cu)
    return s

def unesc(s):
    out = []
    i = 0
    while i < len(s):
        c = s[i]
        if c == '\\' and i + 1 < len(s):
            n = s[i + 1]
            if n == 'n': out.append(0x0A); i += 2; continue
            if n == 't': out.append(0x09); i += 2; continue
            if n == '\\': out.append(0x5C); i += 2; continue
        if c == '<':
            if s[i:i+5] == '<ESC>': out.append(0x1B); i += 5; continue
            m = re.match(r'<([0-9A-F]{2})>', s[i:i+4])
            if m: out.append(int(m.group(1), 16)); i += 4; continue
        if c == '\n': out.append(0x0A); i += 1; continue
        if c == '\t': out.append(0x09); i += 1; continue
        out.append(ord(c)); i += 1
    return out

TOKEN_RE = re.compile(r'<ESC>..|<[0-9A-F]{2}>|\\n|\\t|%[sd0-9]|\n|\t')
# real hiragana/katakana letters only — EXCLUDE U+30FB (・ middle-dot separator),
# punctuation legitimately kept in translations and present in the game font.
KANA_RE = re.compile(r'[ぁ-ゖゝゞァ-ヺー-ヿ]')
KANJI_RE = re.compile(r'[一-鿿々]')

def norm_tokens(s):
    toks = TOKEN_RE.findall(s)
    return Counter(t.replace('\n', '\\n').replace('\t', '\\t') for t in toks)

# ---------- load and validate translations ----------
def load_translations():
    src_items = {}   # text -> cat (from batch files)
    for bf in glob.glob(os.path.join(SP, 'batches', '*.json')):
        data = json.load(open(bf, encoding='utf-8'))
        name = os.path.basename(bf)
        for it in data['items']:
            src_items[(name, it['i'])] = it['t']
    tr = {}          # original -> korean
    stats = Counter()
    fails = []
    for tf in glob.glob(os.path.join(SP, 'translated', '*.json')):
        name = os.path.basename(tf)
        try:
            data = json.load(open(tf, encoding='utf-8'))
        except Exception as e:
            fails.append((name, '*', f'json error: {e}'))
            stats['bad_file'] += 1
            continue
        for it in data.get('items', []):
            key = (name, it.get('i'))
            if key not in src_items:
                stats['unknown_idx'] += 1
                continue
            orig = src_items[key]
            ko = it.get('t', '')
            if not isinstance(ko, str) or not ko.strip():
                stats['empty'] += 1
                fails.append((name, it.get('i'), 'empty'))
                continue
            if KANA_RE.search(ko):
                stats['kana'] += 1
                fails.append((name, it.get('i'), 'kana remains'))
                continue
            if norm_tokens(orig) != norm_tokens(ko):
                stats['token_mismatch'] += 1
                fails.append((name, it.get('i'), 'token mismatch'))
                continue
            if KANJI_RE.search(ko):
                stats['kanji_warn'] += 1  # accept but count
            tr[orig] = ko
            stats['ok'] += 1
    # untranslated originals
    missing = [t for k, t in src_items.items() if t not in tr]
    return tr, stats, fails, src_items, missing

# same seed as prep
SEED = {
    '初めから': '처음부터', '続きから': '이어하기', 'チュートリアル': '튜토리얼',
    '登録武将編集': '등록무장편집', '追加コンテンツ': '추가 콘텐츠',
    '鑑賞': '감상', '設定': '설정', 'ライセンス': '라이선스',
}

# ---------- rebuild: strdata / ev_strdata ----------
def read_strtable_raw(dec):
    count = struct.unpack_from('<I', dec, 0)[0]
    sections = []
    for i in range(count):
        off, size = struct.unpack_from('<II', dec, 4 + i * 8)
        n = struct.unpack_from('<I', dec, off + 8)[0] & 0xFFFF
        tab = off + 0x14
        entries = struct.unpack_from(f'<{n}I', dec, tab)
        strings = []
        for e in entries:
            pos = tab + e
            cus = []
            while True:
                cu = struct.unpack_from('<H', dec, pos)[0]
                pos += 2
                if cu == 0:
                    break
                cus.append(cu)
            strings.append(esc(cus))
        sections.append(strings)
    return sections

def build_strtable(sections):
    blobs = []
    for strings in sections:
        n = len(strings)
        table = bytearray()
        pool = bytearray()
        base = 4 * n
        for s in strings:
            table += struct.pack('<I', base + len(pool))
            cus = unesc(s)
            pool += struct.pack(f'<{len(cus)}H', *cus) if cus else b''
            pool += b'\x00\x00'
        body = bytes(table) + bytes(pool)
        size = 0x14 + len(body)
        hdr = struct.pack('<IIIII', 0x134C58, 0x10000 | (size & 0xFFFF),
                          0x40000 | n, 0x14, 0xFFFFFF00)
        blobs.append(hdr + body)
    out = bytearray()
    out += struct.pack('<I', len(blobs))
    toc_pos = len(out)
    out += b'\x00' * (8 * len(blobs))
    for i, b in enumerate(blobs):
        while len(out) % 4:
            out += b'\x00'
        struct.pack_into('<II', out, toc_pos + i * 8, len(out), len(b))
        out += b
    return bytes(out)

def translate_str(s, tr, used):
    if s in SEED:
        used[0] += 1
        return SEED[s]
    if s in tr:
        used[0] += 1
        return tr[s]
    return s

# ---------- rebuild: msggame ----------
def rebuild_msggame(dec, tr, used):
    count = struct.unpack_from('<I', dec, 0)[0]
    new_secs = []
    for i in range(count):
        off, size = struct.unpack_from('<II', dec, 4 + i * 8)
        n = struct.unpack_from('<I', dec, off)[0]
        offs = struct.unpack_from(f'<{n}I', dec, off + 4)
        ends = list(offs[1:]) + [size]
        blobs = []
        for j in range(n):
            blob = dec[off + offs[j]: off + ends[j]]
            out = bytearray()
            p = 0
            while True:
                st = blob.find(b'\x07\x07\x01', p)
                if st < 0:
                    out += blob[p:]
                    break
                en = blob.find(b'\x07\x07\x02', st + 3)
                if en < 0:
                    out += blob[p:]
                    break
                out += blob[p:st + 3]
                raw = blob[st + 3:en]
                if len(raw) % 2 == 0:
                    cus = struct.unpack_from(f'<{len(raw)//2}H', raw)
                    s = esc(cus)
                    s2 = translate_str(s, tr, used)
                    if s2 is not s:
                        cus2 = unesc(s2)
                        out += struct.pack(f'<{len(cus2)}H', *cus2)
                    else:
                        out += raw
                else:
                    out += raw
                out += b'\x07\x07\x02'
                p = en + 3
            blobs.append(bytes(out))
        # rebuild section
        sec = bytearray(struct.pack('<I', n))
        pos = 4 + 4 * n
        offs2 = []
        for b in blobs:
            offs2.append(pos)
            pos += len(b)
        sec += struct.pack(f'<{n}I', *offs2)
        for b in blobs:
            sec += b
        new_secs.append(bytes(sec))
    out = bytearray(struct.pack('<I', count))
    toc_pos = len(out)
    out += b'\x00' * (8 * count)
    for i, b in enumerate(new_secs):
        while len(out) % 4:
            out += b'\x00'
        struct.pack_into('<II', out, toc_pos + i * 8, len(out), len(b))
        out += b
    return bytes(out)

# ---------- KT wrapper ----------
import lz4.block
def kt_unwrap(blob):
    dec_size = struct.unpack_from('<Q', blob, 8)[0]
    comp_size = struct.unpack_from('<Q', blob, 16)[0]
    return blob[:24], lz4.block.decompress(blob[24:24 + comp_size], uncompressed_size=dec_size)

def kt_wrap(header24, data):
    comp = lz4.block.compress(data, mode='high_compression', compression=12, store_size=False)
    hdr = bytearray(header24)
    struct.pack_into('<Q', hdr, 8, len(data))
    struct.pack_into('<Q', hdr, 16, len(comp))
    return bytes(hdr) + comp

# ---------- main ----------
def main():
    out_dir = sys.argv[1]
    report_only = '--report-only' in sys.argv
    tr, stats, fails, src_items, missing = load_translations()
    print('validation stats:', dict(stats))
    print(f'usable translations: {len(tr):,} / unique sources: {len(set(src_items.values())):,}')
    with open(os.path.join(SP, 'translation_report.txt'), 'w', encoding='utf-8') as f:
        f.write(f'stats: {dict(stats)}\n\nFAILS ({len(fails)}):\n')
        for name, i, why in fails[:2000]:
            f.write(f'{name}\t{i}\t{why}\n')
        f.write(f'\nMISSING ({len(missing)}):\n')
        for t in missing[:2000]:
            f.write(t[:120] + '\n')
    if report_only:
        return

    os.makedirs(os.path.join(out_dir, r'romfs\MSG\JP'), exist_ok=True)
    used = [0]
    all_ko_text = []

    # MSG source: use MERGED (1.1.4) MSG if present, else base 추출원본
    MSG_SRC = r'D:\nsw\merged_sel\MSG\JP'
    if not os.path.isdir(MSG_SRC):
        MSG_SRC = os.path.join(SRC, r'romfs\MSG\JP')
    print(f'MSG source: {MSG_SRC}')

    # strdata (sec4 = credits passthrough)
    with open(os.path.join(MSG_SRC, 'strdata.bin'), 'rb') as f:
        hdr, dec = kt_unwrap(f.read())
    sections = read_strtable_raw(dec)
    for si, strings in enumerate(sections):
        if si == 4:
            continue
        sections[si] = [translate_str(s, tr, used) for s in strings]
        all_ko_text += sections[si]
    dec2 = build_strtable(sections)
    with open(os.path.join(out_dir, r'romfs\MSG\JP\strdata.bin'), 'wb') as f:
        f.write(kt_wrap(hdr, dec2))
    print(f'strdata rebuilt ({len(dec):,} -> {len(dec2):,})')

    # ev_strdata
    with open(os.path.join(MSG_SRC, 'ev_strdata.bin'), 'rb') as f:
        hdr, dec = kt_unwrap(f.read())
    sections = read_strtable_raw(dec)
    sections = [[translate_str(s, tr, used) for s in strings] for strings in sections]
    for strings in sections:
        all_ko_text += strings
    dec2 = build_strtable(sections)
    with open(os.path.join(out_dir, r'romfs\MSG\JP\ev_strdata.bin'), 'wb') as f:
        f.write(kt_wrap(hdr, dec2))
    print(f'ev_strdata rebuilt ({len(dec):,} -> {len(dec2):,})')

    # msggame
    with open(os.path.join(MSG_SRC, 'msggame.bin'), 'rb') as f:
        hdr, dec = kt_unwrap(f.read())
    dec2 = rebuild_msggame(dec, tr, used)
    with open(os.path.join(out_dir, r'romfs\MSG\JP\msggame.bin'), 'wb') as f:
        f.write(kt_wrap(hdr, dec2))
    print(f'msggame rebuilt ({len(dec):,} -> {len(dec2):,})')
    print(f'strings translated in-place: {used[0]:,}')

    # used chars beyond base charset
    base = set(open(os.path.join(SP, 'charset_base.txt'), encoding='utf-8').read())
    used_chars = set()
    for s in all_ko_text + list(tr.values()):
        for c in s:
            if 0xAC00 <= ord(c) <= 0xD7A3 or 0x3130 <= ord(c) <= 0x318F:
                if c not in base:
                    used_chars.add(c)
    with open(os.path.join(SP, 'charset_extra.txt'), 'w', encoding='utf-8') as f:
        f.write(''.join(sorted(used_chars)))
    print(f'extra chars beyond base: {len(used_chars)}')

if __name__ == '__main__':
    main()
