# 빌드 가이드

이 저장소는 **패치를 만드는 도구와 번역 데이터**를 담고 있습니다.
게임 원본 파일은 포함하지 않으므로, 빌드하려면 본인이 정당하게 소유한 게임에서
직접 추출한 파일이 필요합니다.

## 필요 환경

- Python 3.11+  ·  `pip install numpy pillow lz4 opencv-python texture2ddecoder scipy`
- .NET 6 SDK (병합 romfs 추출용, `tools/extractor/`)
- 폰트: 서울한강체(SeoulHangang* TTF, 서울시 무료 배포)
- 본인 콘솔에서 덤프한 `prod.keys`, `title.keys`

## 전체 흐름

```
[게임 NCA]                                   [서울한강체 TTF]
   │  extractor (병합 romfs 추출)                  │
   ▼                                              ▼
MSG/{JP}/*.bin  ─ msg_parse ─▶ 원문 배치     res_lang 엔트리 6·7 (G1N 폰트)
   │                              │                │  g1n_extend (한글 2,404자 확장)
   │                        [번역: translation/]   │  font_tighten3 (자간 b4 조정)
   │                              │                ▼
   └── apply_translations ◀───────┘        res_lang (폰트 + 이미지 로컬라이즈)
              │                                    │  koloc / loc_atlas / e5_loc
              ▼                                    │  (숨은 엔트리 텍스처 한글화)
        MSG/JP/*.bin (한글)  ────────┬─────────────┘
                                     ▼
                          make_zip  →  NobunagaShinsei_KR/ (romfs + exefs)
```

## 단계별

1. **병합 romfs 추출** — `tools/extractor/`
   ```
   set PROD_KEYS=...\prod.keys
   set TITLE_KEYS=...\title.keys
   set BASE_NCA=...\base.nca
   set UPDATE_NCA=...\update.nca
   dotnet run -c Release -- extract /MSG        # MSG만
   dotnet run -c Release -- exefs               # main
   ```

2. **텍스트 추출·배치화** — `prep_batches.py` / `prep_merged.py`
   MSG를 파싱해 유니크 문자열을 `translation/source_jp/*.json`(원문) 형식으로 배치화.

3. **번역** — `translation/korean/*.json` 이 index로 짝지어진 한국어 번역.
   (이 저장소에 포함된 번역을 그대로 쓰거나 개선/기여)

4. **폰트 한글 확장** — `g1n_extend.py`
   res_lang 엔트리 6·7 G1N에 KS X 1001 + 실사용 한글 음절 글리프 추가(서울한강체 래스터라이즈).

5. **자간 최적화** — `font_tighten3.py` (전진폭 b4만 조정 → 두 렌더 경로 모두 안전)

6. **텍스트 재조립** — `apply_translations.py` (+ `msg_fix.py` 로 전각 정규화·줄바꿈 최적화)

7. **이미지 로컬라이즈** — `koloc.py`(공유 헬퍼) + `loc_atlas.py`/`e5_loc.py` 등으로
   res_lang 숨은 엔트리 텍스처 한글화 → `repack_all.py` 로 res_lang 재조립.

8. **exefs 패치** — `patch_main.py` (시스템 메시지 6종, 1.1.4 전용)

9. **패키징** — `make_zip.py` → `NobunagaShinsei_KR/` (romfs + exefs)

위 단계는 **일반 게임 프로그램(872000)** 빌드입니다. **파워업키트(872001)**는
텍스트·폰트가 별도 파일 세트라 아래 추가 단계가 필요합니다 — 배경은
[docs/FORMATS.md §7](FORMATS.md#7-파워업키트872001-이중-프로그램-구조) 참고.

## 파워업키트(872001) 빌드

### ⚠️ 소스 파일은 실기에서 직접 덤프
872001은 자체 base NCA가 없는 BKTR 패치라, PC의 hactool/LibHac 병합 추출로는
`MSG_PK`/`RES_JP_PK`가 정확히 안 나옵니다. **DBI나 nxdumptool로 실기에서 직접
덤프**하세요 — "Program 1"으로 표시되는 항목이 872001입니다. 필요한 것:
```
Program 1/romfs/MSG_PK/JP/*.bin          (7개 파일)
Program 1/romfs/RES_JP_PK/res_lang_pk.bin
Program 1/exefs/main
```

### 단계별

1. **신규 문자열 탐지** — `find_puk_new_strings.py` (env: `PK_MSG_SRC`)
   MSG_PK가 일반 게임 MSG와 공유하는 문자열은 기존 번역 사전으로 자동 커버됨.
   실제 신규 번역이 필요한 것만 추려 `msgpk_to_translate.json`에 기록
   (더미 placeholder·크레딧 블록은 자동 분리·제외).

2. **배치화** — `prep_puk_batches.py` → `translation/source_jp_puk/pkNNN.json`

3. **번역** — 각 배치를 `translation/korean_puk/pkNNN.json`(동일 `i` 인덱스)으로 번역.
   서식 토큰(`\n \t <ESC>C? %d %s`) 보존 필수. `merge_puk_translations.py`로 검증.

4. **MSG_PK 재조립** — `build_msgpk.py` (env: `PK_MSG_SRC`, `PK_MSG_OUT`)
   일반 게임 사전(`translation/source_jp`+`korean`) + PUK 신규 사전
   (`source_jp_puk`+`korean_puk`)을 원문-키로 병합해 번역 주입.

5. **정규화** — `msgpk_normalize.py` (env: `PK_MSG_OUT`) 전각→반각 변환.

6. **폰트 한글 삽입** — `g1n_inplace_korean.py`
   (env: `PK_MSG_SRC`, `BASE_MSG_SRC`, `MAIN_872001`, `PK_MSG_OUT`, `PK_RES_SRC`, `PK_RES_OUT`)
   **주의**: 반드시 이 스크립트를 써야 함. §5 방식(폰트 통째로 큰 걸로 교체)은
   압축 해제 크기가 커져서 872001이 **부팅 전에 크래시**합니다. 이 스크립트는
   미사용 전각 글자 자리에 한글을 제자리로 넣어 크기를 원본과 완전히 같게 유지합니다.

7. **PUK 폰트 자간 최적화** — `puk_font_tighten.py` (env: `PK_RES_OUT`)
   6단계에서 넣은 한글 글리프는 미사용 전각 슬롯의 메트릭(자간=48, 안 조여짐)을
   그대로 물려받아 일반 게임보다 훨씬 넓게 렌더링됩니다 — 이대로 두면 대사가 3줄
   박스를 넘겨 잘립니다. `font_tighten3.py`와 동일한 알고리즘(잉크 폭 기반 자간
   축소, byte4만 변경)을 res_lang_pk에 적용. **byte4만 바꾸므로 압축 해제 크기는
   불변**이지만, 압축 크기는 늘 수 있어 물리 슬롯(다음 엔트리 오프셋까지 남은
   공간) 기준으로 여유를 확인합니다 — 이전 6단계에서 이미 슬롯에 여유가 생겼으므로
   안전합니다.

8. **대사 줄바꿈 오버플로 제거** — `puk_msgev_fix.py` (env: `PK_RES_OUT`, `PK_MSG_OUT`)
   `msg_fix.py`가 일반 게임 ev_strdata.bin에 하던 것과 동일하게, PUK 대사
   (`msgev.bin`)에서 박스 폭을 넘는 세그먼트의 수동 줄바꿈을 제거해 엔진이
   자동으로 재배치하게 함. 7단계에서 조인 폰트의 자간표를 사용하므로 반드시
   그 다음에 실행.

9. **PUK 전용 이미지 한글화** — `loc_e18_labels.py`(정책/시설 라벨 43종),
   `loc_e21_badges.py`(특성/가보 이름 배지 33종, env 둘 다: `PK_RES_SRC`)
   → 각각 `e18_new_link.bin`/`e21_new_link.bin` 생성 → `assemble_res_lang_pk_puk.py`
   (env: `PK_RES_OUT`)로 res_lang_pk에 병합. 투명 배경 텍스트 지우기는
   `erase_place_transparent.py` 사용 — `koloc.erase_place`는 RGB만 인페인팅하고
   알파는 그대로 둬서 불투명 잔상이 남으므로 투명 배경 자산에는 부적합함.

9-1. **DLC_PK 크로스오버 콘텐츠 번역** (env: `DLC_PK_SRC`, `DLC_PK_OUT`) —
   `apply_dlc_translations.py`가 `dlc_translations.py`의 번역 데이터를
   `evm_/gm_/scem_/tom_*.n16`에 적용, 토큰(`<ESC>C?`/`\n`) 검증 후 재조립.
   신규 한글이 추가되므로 **6단계(폰트 삽입)부터 다시 실행해야 함** —
   `g1n_inplace_korean.py`가 MSG_PK뿐 아니라 `DLC_PK_OUT`도 필요-한글 스캔
   대상에 포함하므로, 이 파일들을 만든 뒤에(또는 만들면서) 6→7→8단계를
   다시 돌려야 새 글자가 폰트에 반영됨.

10. **exefs 패치** — `patch_main.py` (env: `SRC_MAIN`=872001의 main,
    `OUT_MAIN`, `NSO_UNCOMPRESSED=1`)

11. **패키징** — 872000 빌드 결과 + 위 872001 빌드 결과를
    `atmosphere/contents/01007ab012872000/`, `…872001/` 두 폴더로 각각 배치.

## 설치

zip 속 `atmosphere` 폴더를 SD카드 루트에 통째로 복사(클린 설치 권장) — 실기용.
에뮬레이터는 `atmosphere/contents/<타이틀ID>/` 안의 내용을 각 게임의 모드 폴더로.

## 주의

- `exefs/main`은 **게임 버전 1.1.5(파워업키트) 전용**. 부팅 문제 시 해당 프로그램의
  exefs 폴더만 삭제.
- 절대 커밋 금지: `prod.keys`, `title.keys`, 게임 원본/추출 바이너리
  (`res_lang*.bin`, `MSG_PK/*.bin` 등 실기 덤프 파일 포함).
