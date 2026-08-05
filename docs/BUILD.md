# 패치 직접 만들기 (빌드 가이드)

이 저장소에는 **패치를 만드는 도구 전부와 번역 데이터 전부**가 들어 있습니다.
게임 원본 파일만 본인이 준비하면, 배포 중인 zip과 **바이트 단위로 똑같은 패치**를
직접 만들 수 있습니다.

> 저장소에는 게임 원본 데이터가 없습니다. 번역 데이터는 "몇 번째 문자열을 어떤
> 한국어로 바꿀지"만 담고 있어, 적용할 때 본인이 덤프한 게임 파일을 읽습니다.

---

## 1. 준비물

| 항목 | 설명 |
|---|---|
| **게임 덤프** | 본인이 소유한 카트리지/eShop 게임의 romfs·exefs (아래 §2) |
| **Python 3.11+** | `pip install numpy pillow lz4 opencv-python texture2ddecoder scipy` |
| **한글화된 이미지** | `res_lang*.bin` — 릴리스 zip에서 추출 (아래 §3) |
| (선택) .NET 6 SDK | 병합 romfs 추출기 `tools/extractor/` 를 쓸 때만 |
| (선택) 서울한강체 TTF | 폰트를 **처음부터 다시 만들** 때만 (§7). 서울시 무료 배포 |
| (선택) `prod.keys`/`title.keys` | 본인 콘솔에서 덤프. NCA에서 직접 추출할 때만 |

**절대 커밋 금지**: `prod.keys`, `title.keys`, 게임 원본/추출 바이너리
(`res_lang*.bin`, `MSG*/*.bin`, `main` 등).

---

## 2. 게임 파일 준비

패치는 게임 프로그램 두 개를 대상으로 합니다.

- `01007AB012872000` = **일반 게임** (추출 시 보통 `Program 0`)
- `01007AB012872001` = **파워업키트(PUK)** (추출 시 `Program 1`)

> ⚠️ **PUK(872001)는 반드시 실기에서 직접 덤프하세요.** 자체 base NCA가 없는 BKTR
> 패치라, PC에서 hactool/LibHac으로 병합 추출하면 `MSG_PK`/`RES_JP_PK`가 정확히
> 나오지 않습니다. **DBI** 또는 **nxdumptool**로 덤프하면 "Program 1"으로 보입니다.

필요한 것:

```
Program 0/romfs/MSG/JP/{strdata,ev_strdata,msggame}.bin
Program 0/romfs/RES_JP/{res_lang,res_lang_exp}.bin
Program 0/exefs/main
Program 1/romfs/MSG_PK/JP/*.bin
Program 1/romfs/DLC_PK/JP/*.n16
Program 1/romfs/RES_JP_PK/{res_lang_pk,res_lang_exp_pk}.bin
Program 1/exefs/main
(선택) 추가 시나리오 DLC: romfs_<타이틀ID>/JP/*.n16
```

NCA에서 직접 뽑고 싶다면 `tools/extractor/`(LibHac, .NET 6):

```bash
set PROD_KEYS=...\prod.keys
set TITLE_KEYS=...\title.keys
set BASE_NCA=...\base.nca
set UPDATE_NCA=...\update.nca
dotnet run -c Release -- extract /MSG     # romfs 일부만
dotnet run -c Release -- exefs            # exefs/main
```

### 기본판(872000) 텍스트에 대한 중요한 주의

`data/ko/base` 는 게임 **최초 출시(v0) 시점의 기본판 romfs**를 기준으로 만들어졌습니다
(문자열 수: `strdata` 32,201 / `ev_strdata` 17,868 / `msggame` 23,595).
1.1.4 이후 업데이트된 기본판 romfs는 문자열이 늘어나(예: `strdata` 32,311) **개수가
맞지 않으면 빌드가 오류로 중단**됩니다. 배포 중인 zip도 v0 기준으로 만들어져 있습니다.
파워업키트 플레이 시에는 872001만 실행되므로 실사용에는 영향이 없습니다.

---

## 3. 한글화된 이미지 가져오기

`res_lang*.bin`(폰트 + 화면 이미지)은 게임 원본 텍스처가 통째로 들어간 80MB급
파일이라 저장소에 넣지 않습니다. 이미 공개 배포 중인 **릴리스 zip에서 꺼내 씁니다.**
이미지는 게임 버전이 올라가도 거의 바뀌지 않아, 새 버전 패치를 만들 때도 그대로
재사용하는 것이 정상 절차입니다.

```bash
# 이미 받아둔 zip에서
python tools/fetch_release_images.py --zip NobunagaShinsei_KR_for_1.1.7_PUK.zip --out images/

# 또는 GitHub 릴리스에서 바로 (gh CLI 필요)
python tools/fetch_release_images.py --release v4.0 \
    --asset NobunagaShinsei_KR_for_1.1.7_PUK.zip --out images/
```

폰트·이미지를 **처음부터 직접 만들고 싶다면** §7을 보세요.

---

## 4. 빌드 (한 방에)

```bash
python tools/build_patch.py --version 1.1.7 \
  --romfs-base "<...>/Program 0/romfs" \
  --romfs-puk  "<...>/Program 1/romfs" \
  --main-base  "<...>/Program 0/exefs/main" \
  --main-puk   "<...>/Program 1/exefs/main" \
  --aoc        "<...>/aoc_extract" \
  --images     images/ \
  --out build/1.1.7 \
  --zip NobunagaShinsei_KR_for_1.1.7_PUK.zip
```

`--version` 은 `1.1.7` / `1.1.5` / `1.1.4` 중 하나입니다.
없는 것은 인자를 빼면 그 단계만 건너뜁니다(`--skip-aoc` 등으로 명시적으로 끌 수도 있음).

빌더가 하는 일:

| 단계 | 내용 | 사용 데이터 |
|---|---|---|
| MSG / MSG_PK | 게임 텍스트 한글화 | `data/ko/base`, `data/ko/puk_117`\|`puk_115` |
| DLC_PK | 크로스오버 무장·시나리오 | `tools/dlc_translations.py` |
| AOC | 추가 시나리오 DLC | `tools/aoc_translations.py` |
| exefs | 시스템 메시지 6종 한글화 | `tools/patch_main.py` |
| exefs (1.1.7) | **한국어 입력기** | `tools/hangul_kbd_117.patch.json` |
| 이미지 | 한글 폰트·화면 이미지 배치 | `--images` 폴더 |
| 패키징 | zip 생성(설치 안내 동봉) | `docs/INSTALL.md` |

### ⚠️ 폰트 글리프 감사 (릴리스 전 필수)

한글 폰트는 **"게임이 안 쓰는 일본어 글리프" 자리를 한글로 재활용**해 만듭니다. 그 판단을
**옛 게임 버전 텍스트**로 하면, 새 버전에서 추가된 문구가 쓰는 글자를 덮어써 화면에서 깨집니다.
실제로 1.1.5 기준으로 만든 폰트를 1.1.7에 그대로 쓰다가 **Joy-Con 2 버튼 아이콘(μ ν ξ ο)·
PlayStation®의 ®·따옴표·크레딧 한자**가 깨진 적이 있습니다.

```bash
python tools/audit_glyphs.py \
  --res build/1.1.7/contents/01007ab012872001/romfs/RES_JP_PK/res_lang_pk.bin --entry 16 \
  --msg build/1.1.7/contents/01007ab012872001/romfs/MSG_PK/JP
```

`✅ 깨지는 문자 없음` 이 나와야 합니다. 깨진 문자가 나오면 §7의 폰트 재생성을
**해당 게임 버전 텍스트 기준**으로 다시 하세요(`g1n_inplace_korean.py` 의 `PK_MSG_SRC` 등).

### 결과 검증

배포본과 같은지 확인하려면 릴리스 zip과 파일별 해시를 비교하세요.

```bash
python - <<'EOF'
import zipfile, hashlib, os
BUILD, ZIP = 'build/1.1.7', 'NobunagaShinsei_KR_for_1.1.7_PUK.zip'
zh = {i.filename: hashlib.sha256(zipfile.ZipFile(ZIP).read(i)).hexdigest()
      for i in zipfile.ZipFile(ZIP).infolist() if not i.is_dir()}
bad = 0
for root, _, fs in os.walk(BUILD):
    for f in fs:
        p = os.path.join(root, f)
        arc = 'atmosphere/' + os.path.relpath(p, BUILD).replace('\\', '/')
        h = hashlib.sha256(open(p, 'rb').read()).hexdigest()
        if zh.get(arc) != h:
            print('DIFF', arc); bad += 1
print('불일치', bad)
EOF
```

> 이 저장소의 데이터로 1.1.7 패치를 다시 빌드해 **65개 파일 전부 배포본과 바이트
> 일치**함을 확인했습니다(exefs·한국어 입력기·AOC DLC 포함).

---

## 5. 번역 수정하기

번역 데이터는 두 곳에 있습니다.

**`data/ko/<버전>/<파일>.bin.json`** — 실제 빌드에 쓰이는 데이터.
인덱스 순서대로 한국어가 들어 있고, 번역하지 않은 항목은 `null`(원문 유지)입니다.

```json
{"file": "msgev.bin", "kind": "strtable", "sections": [17916], "count": 17916,
 "ko": [null, "고호쿠의 다이묘 아자이 나가마사는…", null, ...]}
```

고치는 법: 해당 인덱스의 문자열을 바꾸고 다시 빌드하면 끝입니다.
어떤 인덱스가 어떤 문장인지 보려면 원본과 나란히 출력하세요.

```bash
python - <<'EOF'
import sys, json; sys.path.insert(0, 'tools')
import ko_tables as K
jp = r'<...>/Program 1/romfs/MSG_PK/JP/msgev.bin'
d = json.load(open('data/ko/puk_117/msgev.bin.json', encoding='utf-8'))
_, _, s, _, _ = K.read_file(jp)
for i in range(3200, 3210):
    print(i, '|', s[i][:60], '=>', d['ko'][i])
EOF
```

**`translation/{source_jp,korean}`** — 사람이 읽고 고치기 좋은 원문/번역 배치.
초기 번역 작업에 쓰인 형식이며, PR로 기여할 때 쓰기 좋습니다.

**서식 토큰은 반드시 보존하세요**: `%s` `%d` `\n` `\t` `[bNNN]`(이름 치환),
`<ESC>C?`(색 지정). 깨지면 게임에서 글자가 깨지거나 멈출 수 있습니다.

### 대사 줄바꿈 규칙 (중요)

- **`msgev`**(시나리오 상황 설명·컷신) = 전체폭 박스, **자동 줄바꿈**.
  수동 줄바꿈 `\n`을 빼면 엔진이 알아서 줄을 나눕니다.
- **`msggame`**(초상화·이름표가 붙는 캐릭터 대사) = **한 줄을 폭에 맞춰 글자를 축소**.
  `\n`을 빼면 글자가 지나치게 작아집니다. **건드리지 마세요.**

자세한 근거와 예외 처리는 [`tools/NOTE_dialogue_linebreak.md`](../tools/NOTE_dialogue_linebreak.md).

---

## 6. 새 게임 버전이 나왔을 때

1. 새 버전을 덤프하고, 이전 버전과 파일 단위로 비교합니다 — `tools/diff_115_117.py` 참고.
2. 문자열 개수가 그대로면 기존 `data/ko/<버전>` 을 그대로 쓸 수 있습니다.
   달라졌다면 새 폴더를 만들어야 합니다.
3. 이전 번역을 새 버전으로 옮기려면 **원문 텍스트를 키로** 매칭합니다.
   `tools/build_msgpk_117.py`·`merge_117.py`·`gen_dummy_117.py` 가 1.1.5→1.1.7 때
   쓴 방식입니다(원문-키 사전 → 신규 문자열만 추려 번역 → 병합).
4. 신규 문자열만 번역한 뒤, 한글화된 결과에서 데이터를 다시 뽑아 커밋합니다.

```bash
python tools/ko_tables.py export --jp <새버전 원본폴더> --ko <한글화된 폴더> --out data/ko/<새이름>
```

5. `tools/build_patch.py` 의 `VERSIONS` 에 새 버전 항목을 추가합니다.
6. **exefs/main 은 버전 전용**이라 새 실행파일에 다시 패치해야 합니다.
   한국어 입력기도 새 main 기준으로 다시 만들어야 합니다
   ([`tools/NOTE_hangul_keyboard.md`](../tools/NOTE_hangul_keyboard.md)).

---

## 7. (고급) 폰트·이미지를 처음부터 다시 만들기

§3처럼 릴리스에서 가져오면 대부분 충분합니다. 아래는 **폰트/이미지를 직접 다시
만들 때**의 원래 제작 과정입니다. 스크립트마다 입력 경로를 환경변수나 상단 상수로
지정하며, 일부는 제작 당시 경로가 하드코딩되어 있어 손봐야 합니다.

### 일반 게임(872000)

1. **폰트 한글 확장** — `g1n_extend.py <charset.txt> <out res_lang.bin>`
   `res_lang` 엔트리 6·7의 G1N 비트맵 폰트에 한글 글리프를 추가합니다
   (서울한강체 래스터라이즈, 문자 목록은 `tools/charset_final.txt`).
2. **자간 최적화** — `font_tighten3.py` (전진폭 byte4만 조정 → 렌더 경로 양쪽 안전)
3. **이미지 한글화** — `koloc.py`(공용 헬퍼) + `loc_atlas.py`(원형 명령 메뉴),
   `e5_loc.py`(시스템 버튼), `render_labels.py`(화면 제목), `render_warning.py`
   → `repack_all.py` 로 `res_lang.bin` 재조립
4. **확장 리소스** — 1.1.5부터 내비 버튼이 `res_lang_exp.bin`에서 로드됩니다.
   `build_v37_images.py` → `rebuild_v37_files.py` (내부 LINK 자식 단위 재조립)

### 파워업키트(872001)

> ⚠️ **폰트를 통째로 큰 것으로 교체하면 872001은 부팅 전에 죽습니다.**
> 폰트 로더가 원본과 정확히 같은 압축 해제 크기를 요구합니다.

1. **폰트 제자리 삽입** — `g1n_inplace_korean.py`
   미사용 전각 글자 슬롯에 한글을 **같은 크기로** 덮어써 파일 크기를 유지합니다.
2. **PUK 폰트 자간** — `puk_font_tighten.py` (byte4만 변경 → 해제 크기 불변)
3. **PUK 전용 이미지** — `loc_e18_labels.py`(정책/시설 라벨),
   `loc_e21_badges.py`(특성/가보 배지) → `assemble_res_lang_pk_puk.py` 로 병합.
   투명 배경 텍스처는 `erase_place_transparent.py` 를 쓰세요
   (`koloc.erase_place`는 알파를 남겨 잔상이 생깁니다).

포맷 자체(LINKDATA/KT/NSO/MSG/G1N/G1T, 이중 프로그램 구조)는
[FORMATS.md](FORMATS.md)에 정리되어 있습니다.

---

## 8. 자주 겪는 문제

| 증상 | 원인/해결 |
|---|---|
| `문자열 개수 불일치 … 게임 버전이 다릅니다` | `data/ko/<버전>` 과 게임 덤프 버전이 다릅니다. §2·§6 참고 |
| PUK 텍스트가 일본어 | 872001을 PC 병합 추출로 뽑았을 가능성. 실기 덤프 필요(§2) |
| 게임이 부팅 전에 죽음 | 폰트 크기를 키웠거나 exefs 버전이 안 맞습니다. `exefs` 폴더만 지워 확인 |
| 버튼 이미지만 일본어 | `res_lang_exp*.bin` 이 빠졌습니다(§3에서 4개 모두 추출) |
| 추가 시나리오만 일본어 | AOC(`01007ab0128730xx`) 폴더가 빠졌습니다. `--aoc` 지정 |
| 캐릭터 대사 글자가 작아짐 | `msggame`에서 `\n`을 지웠기 때문입니다(§5) |
