# 파일 포맷 분석 (Nobunaga's Ambition: Shinsei, Switch)

이 문서는 한글 패치를 만들며 리버스 엔지니어링한 게임 파일 포맷을 정리한 것입니다.
게임 원본 데이터는 포함하지 않습니다. 아래 도구들은 모두 `tools/`에 있습니다.

- 타이틀 ID: `01007AB012872000` (일본 일반판)
- 대상 버전: **1.1.4** (베이스 + 업데이트 BKTR 병합본)

---

## 0. 게임 실행 데이터 = 베이스 + 1.1.4 업데이트 병합

게임은 베이스 NCA에 1.1.4 업데이트 NCA를 BKTR 델타 패치로 얹어 실행합니다.
따라서 베이스만 추출하면 안 되고 **병합 RomFS**를 봐야 합니다.
`tools/extractor/`(LibHac 0.17.0, .NET 6)가 prod.keys + title.keys로 두 NCA를
복호화·병합해 추출합니다. (키는 저장소에 없음 — 본인 콘솔 덤프 사용)

병합 romfs 파일 수 208개. 언어별 로컬라이즈 대상은 `MSG/{JP,SC,TC}/*`와
`RES_{JP,SC,TC}/res_lang.bin` 둘뿐입니다.

---

## 1. KOEI LINKDATA 아카이브

```
'LINK' (4)
u32 count
u32 toc_offset        ← 목차 시작 오프셋 (외부 컨테이너=0x10, 내부=0x20 인 경우 있음)
u32 ...
[toc_offset] : (u32 entry_offset, u32 entry_size) × count   ← 엔트리 기준 상대
```

- **주의**: `toc_offset`을 헤더의 offset 0x08에서 읽어야 함(하드코딩 금지).
  외부 res_lang 컨테이너는 TOC가 0x10, 내부 엔트리들은 0x20에 있어 파서가 흔히 어긋남.
- **⚠️ 내부(중첩) LINKDATA의 데이터 서브엔트리 오프셋은 블롭 기준 16바이트 정렬 필수.**
  정렬이 깨지면 게임 로더가 텍스처 로드에 실패하고 4×4 평균색 플레이스홀더(검은 화면)로 폴백함.
- 파서: `tools/linkdata.py`, `tools/koloc.py`(link_children)

## 2. KT 압축 래퍼

```
01 01 (2) + 해시/플래그 (6) + u64 dec_size + u64 comp_size + LZ4 단일 블록
```
- 헤더 24바이트, 이후 raw LZ4 블록. `lz4.block.decompress(data, uncompressed_size=dec_size)`
- 재압축 시 헤더 0~7바이트(매직+해시) 보존, dec/comp 크기 갱신.
- 파서: `tools/kt_unwrap.py`

## 3. NSO0 실행파일 (exefs/main)

- 세그먼트 3개(.text/.rodata/.data)가 각각 LZ4 압축(flags 0x3f), 세그먼트별 SHA256.
- 패치 절차: 압축 해제 → .rodata 문자열 교체(원본 UTF-16 바이트 길이 이내, 널 패딩)
  → 세그먼트별 SHA256 재계산 → LZ4 재압축 → NSO0 헤더 재작성.
- 도구: `tools/nso_decompress.py`, `tools/patch_main.py`

---

## 4. MSG 텍스트 (`MSG/{lang}/`)

3파일 모두 KT 래퍼 → 오프셋 테이블 컨테이너.

### strdata.bin / ev_strdata.bin — 오프셋 테이블 문자열
```
컨테이너: u32 count + (u32 off, u32 size) × count
각 섹션: 헤더(0x14B) + u32 offset[n](테이블 기준 상대) + null 종료 UTF-16LE 풀
```
- 섹션 헤더 = `u32 0x134C58` + `u16 크기하위16, u16 1` + `u16 문자열수 n, u16 4` + `u32 0x14` + `u32 0xFFFFFF00`
- 컬러 태그: `<ESC>C?` (U+001B + 'C' + 한 글자, Z=리셋)
- strdata 섹션: 0=성씨/이름/관직, 1=UI, 2=무장열전, 3=명품해설, 4=크레딧

### msggame.bin — 바이트코드
- 18섹션, `u32 n + u32 offset[n]` + 바이트코드 엔트리
- 텍스트는 `07 07 01` ~ `07 07 02` 사이 UTF-16LE 런(홀수 오프셋 가능, 정렬 없음)
- 기타 옵코드: `01 4A`+u32=ID참조, `02`+ASCII/`04 3D`+숫자=조건, `06 7C`='|', `1B 43 xx`=컬러, `05 05 05`=종결
- JP/SC/TC 섹션·문자열 개수 1:1 → 슬롯 단위 교체 가능
- 도구: `tools/msg_parse.py`, `tools/msg_export.py`, `tools/apply_translations.py`, `tools/msg_verify.py`

---

## 5. G1N 비트맵 폰트 (`RES_JP/res_lang.bin` 엔트리 6·7)

매직 `_N1G0000`. 엔트리 6 = 메인 48px, 엔트리 7 = 보조 24px.

```
헤더: +0x08 총크기, +0x0C 첫섹션오프셋, +0x10 팔레트당 엔트리수(16),
      +0x14 비트맵풀 시작오프셋, +0x18 팔레트 개수, +0x1C 섹션 수,
      +0x20 섹션 오프셋 u32×N, 이후 RGBA 팔레트(64B)×팔레트개수
섹션(=스트라이크): charmap u16[0x10000] (문자→글리프ID, 0=없음)
      + 글리프 레코드 12B × (maxID+1)
글리프 레코드 12B: 8바이트 메트릭 + u32 비트맵오프셋(풀 기준 상대)
```

### 메트릭 8바이트
`[b0=논리폭/전진폭, b1=48, b2=0, b3=48, b4=전진폭(=b0), b5=-(저장폭/2) 부호화, b6=0, b7=48]`
- **b5 = 256 - (저장셀폭/2)**. 232→48폭 저장, 244→24폭 저장.
- 섹션2(가변폭 라틴/가나 378자)가 b0(논리폭)만 15~47로 다르게 동작함을 실증.

### 비트맵
- 4bpp 팔레트 인덱스, **행 피치 = ceil(b0/2) 바이트** (⚠️ 폭 바꾸면 반드시 행 재패킹)
- **니블 순서: 짝수 픽셀 = 상위 니블**. 반대로 쓰면 인게임에서 획에 1px 틈+가로 점선.
- 48×48 셀 = 0x480 바이트.
- charmap이 BMP(u16)라 한글 음절(U+AC00–D7A3) 표현 가능.

### 자간 조정 (중요)
게임 텍스트 렌더 경로가 2개:
1. **가변폭**(대사창 등): 글리프 쿼드=b0폭 1:1, 펜 전진=b4
2. **고정칸**(일부 창): b0폭 텍스처를 고정 48px 칸에 스트레치

→ 자간을 안전하게 줄이려면 **b4(전진폭)만** 변경. b0/비트맵을 줄이면
①행 피치 재패킹 필요 + ②고정칸에서 글자가 가로로 늘어남(이중 함정).
- 도구: `tools/g1n_analyze.py`, `tools/g1n_render.py`, `tools/g1n_extend.py`(한글 확장), `tools/font_tighten3.py`(b4만 조정)

---

## 6. G1T 텍스처 (Switch)

매직 `GT1G` ver0600. res_lang·res_grp 등 아카이브 내부에 다수.

```
헤더: +0x0C 텍스처테이블오프셋, +0x10 텍스처수, 테이블=u32 offset×n
텍스처 헤더: +1 = 포맷, +2 = packed 치수, +8 u32 확장헤더크기 후 데이터
```
- 포맷: `0x59`=BC1, `0x5B`=BC3, `0x5C`=BC4, `0x5F`=BC7, `0x01`=BGRA8
- packed 치수: **하위 니블 = 폭 log2, 상위 니블 = 높이 log2**
- **스위즐 없음(리니어)** — Tegra 디스위즐 불필요.
- 디코드: BC1/3은 DDS 래핑→Pillow, BC4/7은 texture2ddecoder. 인코드(BC3): 자작 `tools/bc_encode.py`(Pillow는 BC 인코딩 불가).
- **로컬라이즈된 UI가 들어있는 res_lang 숨은 엔트리**(내부 LINK TOC를 0x20에서 읽어야 나옴):
  - e5 = 시스템/내비 버튼 아틀라스, e8 = 원형 명령 버튼, e12 = 전투 군평정,
    e13 = 합전 배너, e16 = 튜토리얼 다이어그램, e24 = 타이틀
- 도구: `tools/g1t_decode.py`, `tools/catalog_all_g1t.py`, `tools/extract_hidden.py`,
  `tools/koloc.py`(디코드+한글 fit 렌더+BC3 재인코드+재조립), `tools/loc_atlas.py`, `tools/e5_loc.py`

---

## 대사 줄바꿈 / 자간 최적화

한글 번역이 일본어보다 길어 대사가 3줄을 넘겨 잘리던 문제의 3중 원인·해법:
1. JP 원문의 수동 `\n` 위치를 물려받아 세그먼트가 박스 폭(~1056유닛=22전각) 초과 → 엔진 추가 줄바꿈
2. 전각 문자(（１５６０）？！) 잔존으로 폭 낭비
3. 한글 전진폭 48 고정(잉크 평균 34)

해법: ① b4 전진폭을 잉크폭+4로 축소(폰트), ② 전각→반각 정규화 + 글리프 없는 ·/？/— 치환,
③ 폭 초과 세그먼트의 수동 `\n`을 제거해 엔진 자동 줄바꿈. 모두 UTF-16 길이 보존 in-place.
- 도구: `tools/font_tighten3.py`, `tools/msg_fix.py`
