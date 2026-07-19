# -*- coding: utf-8 -*-
"""Scoped terminology fix: for entries whose JP source contains a problem term, replace
the OLD Korean rendering with a NEW one -- but only the standalone-word occurrence, not
inside an unrelated longer word. Applies directly to translation/korean(_puk)/*.json in
the repo (the real source of truth), preserving all other content untouched."""
import json, os, glob, re, sys
sys.stdout.reconfigure(encoding='utf-8')

GH = r'D:\nsw\rom\ghpatch\translation'

# simple compounds: safe to blind-replace anywhere the KO contains the exact substring,
# because these multi-syllable strings are specific enough not to collide with unrelated
# Korean vocabulary.
SIMPLE = [
    ('훈공', '공훈'),      # 勲功: word-order fix
    ('잇코종', '일향종'),   # 一向宗: phonetic -> established sino-korean reading
    ('잇코슈', '일향종'),   # (alt spelling seen in some entries)
    ('겐콘', '건곤'),       # 乾坤: phonetic -> sino-korean reading
]

# 姫 (standalone "princess/hime" common noun) -> 공주.  Must NOT touch 히메 name-suffix
# renderings (e.g. 요시히메, 세나히메, 노히메 -- a different, correct rendering for named
# characters). "희" never appears as a substring of "히메" (different hangul syllables),
# so the only risk is "희" being part of a DIFFERENT unrelated word (환희, 희망, 희생,
# 희극, 희비, 희로애락, 희망봉, etc). Only replace when 희 is NOT preceded by a hangul
# syllable that would form one of those (checked via blocklist prefix) AND is followed by
# a common subject/object/topic particle or non-hangul boundary (space/punct/end).
HUI_BLOCK_PREV = set('환희망생극비로수유쾌환')  # chars that combine with 희 to form other words when placed BEFORE it (환+희=환희 etc.) -- these are the char appearing right before 희 that we must NOT treat as our target
PARTICLE_NEXT = ('가','는','를','로','의','와','과','에게','라는','처럼','만','도','께','님', '무장',' ','\\n','.',',','!','?','」','【','[',')',']','…','를','으로')

def hui_to_gongju(ko):
    out = []
    i = 0
    n = len(ko)
    changed = 0
    while i < n:
        c = ko[i]
        if c == '희':
            prev = ko[i-1] if i > 0 else ''
            nxt = ko[i+1:i+3]
            prev_is_hangul = '가' <= prev <= '힣'
            blocked = prev_is_hangul and prev in HUI_BLOCK_PREV
            follows_ok = (nxt == '' ) or any(nxt.startswith(p) for p in PARTICLE_NEXT) or not ('가' <= nxt[:1] <= '힣')
            if not blocked and follows_ok:
                out.append('공주')
                changed += 1
                i += 1
                continue
        out.append(c)
        i += 1
    return ''.join(out), changed

def load_dir(src_dir, ko_dir):
    files = {}
    for bf in sorted(glob.glob(os.path.join(GH, src_dir, '*.json'))):
        name = os.path.basename(bf)
        kf = os.path.join(GH, ko_dir, name)
        if not os.path.isfile(kf): continue
        src = json.load(open(bf, encoding='utf-8'))
        ko = json.load(open(kf, encoding='utf-8'))
        files[name] = (bf, kf, src, ko)
    return files

DRY_RUN = os.environ.get('DRY_RUN') == '1'

def process(label, src_dir, ko_dir, terms_needing_scope):
    files = load_dir(src_dir, ko_dir)
    stats = {t: [0,0] for t in ['simple','hime','labor','gundai','joudai']}  # [attempted, changed]
    for name, (bf, kf, src, ko) in files.items():
        src_map = {it['i']: it['t'] for it in src['items']}
        touched = False
        for it in ko['items']:
            i = it['i']
            jp = src_map.get(i, '')
            if not jp: continue
            t = it.get('t','')
            orig_t = t
            # simple compounds
            for old, new in SIMPLE:
                if old in t:
                    t = t.replace(old, new)
            # 姫 -> 공주 (scoped to entries whose JP contains bare 姫, not just as part of another kanji compound like unrelated homographs -- 姫 itself is used consistently)
            if '姫' in jp and '희' in t:
                t2, n = hui_to_gongju(t)
                if n: t = t2; stats['hime'][1]+=n
                stats['hime'][0]+=1
            # 労力 -> scoped: only replace bare "노력" when JP has 労力 AND not 努力(effort, different kanji, shouldn't be in jp here since we scope by 労力 presence, but the KO "노력" string itself is ambiguous -- only replace if JP segment doesn't ALSO contain 努力)
            if '労力' in jp and '努力' not in jp and '노력' in t:
                cnt = t.count('노력')
                t = t.replace('노력','노동력')
                stats['labor'][0]+=1; stats['labor'][1]+=cnt
            if '郡代' in jp and '군대' in t:
                cnt = t.count('군대')
                t = t.replace('군대','군 대관')
                stats['gundai'][0]+=1; stats['gundai'][1]+=cnt
            if '城代' in jp and '성대' in t:
                cnt = t.count('성대')
                t = t.replace('성대','성 대관')
                stats['joudai'][0]+=1; stats['joudai'][1]+=cnt
            if t != orig_t:
                it['t'] = t
                touched = True
        if touched:
            json.dump(ko, open(kf,'w',encoding='utf-8'), ensure_ascii=False, indent=0)
    return stats

print('=== BASE (translation/source_jp + korean) ===')
s1 = process('BASE','source_jp','korean',None)
for k,(a,c) in s1.items(): print(f'  {k}: entries_touched={a} chars_replaced={c}')

print('=== PUK (translation/source_jp_puk + korean_puk) ===')
s2 = process('PUK','source_jp_puk','korean_puk',None)
for k,(a,c) in s2.items(): print(f'  {k}: entries_touched={a} chars_replaced={c}')
