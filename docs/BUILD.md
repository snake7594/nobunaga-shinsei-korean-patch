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

## 설치

zip 속 `NobunagaShinsei_KR` 폴더를 모드 폴더에 복사(클린 설치 권장).
- Ryujinx: 게임 우클릭 → Open Mods Directory
- Atmosphère 실기: `atmosphere/contents/01007AB012872000/`

## 주의

- `exefs/main`은 **게임 버전 1.1.4 전용**. 부팅 문제 시 exefs 폴더만 삭제.
- 절대 커밋 금지: `prod.keys`, `title.keys`, 게임 원본/추출 바이너리.
