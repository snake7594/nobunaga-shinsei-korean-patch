# -*- coding: utf-8 -*-
"""Find MSG_PK (872001 Power-Up Kit program) strings not yet covered by the base game's
translation dict (translation/source_jp + translation/korean), and split them into:
  - msgpk_to_translate.json  — real content that needs a fresh translation batch
  - msgpk_credits_passthrough.json — long staff-credit blocks, kept in Japanese (policy:
    people's names aren't translated, same as strdata section 4 in the base game)
Dummy/placeholder strings (containing "ダミー" — internal unused-slot template text, never
shown to players) are dropped from both lists; they're simply left untranslated in the
final MSG_PK build, which is safe since the font keeps every JP glyph these strings use.

Usage: PK_MSG_SRC=<real-hw dump of 872001's MSG_PK/JP> python find_puk_new_strings.py
"""
import struct, os, sys, json, re, glob
import lz4.block
sys.stdout.reconfigure(encoding='utf-8')
import apply_translations as A

def kt_dec(b):
    dec=struct.unpack_from('<Q',b,8)[0]; comp=struct.unpack_from('<Q',b,16)[0]
    return lz4.block.decompress(b[24:24+comp],uncompressed_size=dec)

PK = os.environ.get('PK_MSG_SRC') or r'D:\nsw\rom\1.1.5\Program 1\romfs\MSG_PK\JP'
SP = os.path.dirname(os.path.abspath(__file__))
TR_DIR = os.path.join(SP, '..', 'translation')

# base-game dict, same convention as build_msgpk.py's load_pair_dict
have = set()
for bf in glob.glob(os.path.join(TR_DIR, 'source_jp', '*.json')):
    name = os.path.basename(bf)
    src = {it['i']: it['t'] for it in json.load(open(bf, encoding='utf-8'))['items']}
    kf = os.path.join(TR_DIR, 'korean', name)
    if os.path.isfile(kf):
        for it in json.load(open(kf, encoding='utf-8'))['items']:
            if it['i'] in src:
                have.add(src[it['i']])
have |= set(A.SEED.keys())

KANA=re.compile(r'[ぁ-ゖゝゞァ-ヺ]'); KANJI=re.compile(r'[一-鿿々]')
CJKW=re.compile(r'[぀-ゟ゠-ヿ一-鿿々０-９Ａ-Ｚ]')

def strtable_strings(dec):
    return [s for sec in A.read_strtable_raw(dec) for s in sec]
def msggame_strings(dec):
    out=[]; B=bytes(dec); i=0
    while True:
        st=B.find(b'\x07\x07\x01',i)
        if st<0: break
        en=B.find(b'\x07\x07\x02',st+3)
        if en<0: break
        raw=B[st+3:en]
        if len(raw)%2==0: out.append(A.esc(struct.unpack_from('<%dH'%(len(raw)//2),raw)))
        i=en+3
    return out

files=[('msgdata.bin','str'),('msgev.bin','str'),('msgui.bin','str'),('msgbre.bin','str'),
       ('msgire.bin','str'),('msgstf.bin','str'),('msggame.bin','game')]
allnew=set(); grand_total=0; grand_have=0
for f,kind in files:
    dec=kt_dec(open(os.path.join(PK,f),'rb').read())
    strs = strtable_strings(dec) if kind=='str' else msggame_strings(dec)
    uniq=set(s for s in strs if s.strip())
    jp = set(s for s in uniq if KANA.search(s) or KANJI.search(s) or CJKW.search(s))
    covered = sum(1 for s in jp if s in have)
    new = [s for s in jp if s not in have]
    grand_total+=len(jp); grand_have+=covered
    allnew |= set(new)
    print('%-13s total=%5d  jp=%5d  covered=%5d  NEW=%4d'%(f,len(uniq),len(jp),covered,len(new)))
print('GRAND: jp-unique-per-file sum=%d covered=%d | UNIQUE NEW across all=%d'%(grand_total,grand_have,len(allnew)))

dummy = sorted(s for s in allnew if 'ダミー' in s)
non_dummy = [s for s in allnew if 'ダミー' not in s]

# credit blocks: long strings with many literal-\n lines + staff-roll section headers
CREDIT_KW = ['プランナー','プログラマー','監督','演奏','レコーディング','ミキシング','デザインワーク',
             'パッケージイラスト','キャラクターモデリング','サウンド','オープニングムービー',
             'QAディレクター','QA リード','制作協力','LOCALIZATION','ボイスレコーディング',
             '出演','ナレーション','作詞','作曲','編曲','背景\\n','マニュアル\\n']
def is_credit(s):
    if len(s) < 150: return False
    if s.count('\\\\n') < 6: return False   # literal 2-char "\n" escape, not a real newline
    return any(k in s for k in CREDIT_KW)

credits = sorted(s for s in non_dummy if is_credit(s))
to_translate = sorted(s for s in non_dummy if not is_credit(s))

print('dummy (untranslated, not player-facing): %d' % len(dummy))
print('credit blocks (untranslated, names kept as-is): %d' % len(credits))
print('to translate: %d  (chars: %d)' % (len(to_translate), sum(len(s) for s in to_translate)))

json.dump({'strings': to_translate}, open(os.path.join(SP,'msgpk_to_translate.json'),'w',encoding='utf-8'),
           ensure_ascii=False, indent=1)
json.dump({'strings': credits}, open(os.path.join(SP,'msgpk_credits_passthrough.json'),'w',encoding='utf-8'),
           ensure_ascii=False, indent=1)
