# 한국어 입력기 (한글 IME + 성명/독음 검증 바이패스) — 1.1.7 PUK main

## 출처
GitHub 이슈 #1(제작자 @2seunghee)에 올라온 xdelta 패치. 게임 실행파일(exefs/main)을 수정해
Switch 시스템 키보드로 **무장 신규 등록·이름 편집 시 한글 입력**을 가능하게 하고, 성명/독음의
글자 수 검증을 우회한다(기존 무장 편집 시 "이름 6자 이상"으로 저장 안 되던 버그 포함 해결).

원본 xdelta: `tools/NobunagaShinsei_PUK_1.1.7_hangul_keyboard_bypass_validation.xdelta`
- 포맷: VCDIFF(xdelta3), 2차 압축 lzma. 3 윈도우, 순증 218바이트.
- **소스 = 우리 v4.0 1.1.7 PUK main**(앱 헤더에 `snake7594_v4.0_1.1.7_PUK_extract\...\exefs\main`
  명시). 즉 우리 배포 main 위에 바로 적용되도록 제작됨.
- 편집 내용: NSO 헤더(.ro/.data 파일오프셋, .text 압축크기, .text SHA256 해시) + .text 코드
  소수 패치(검증 우회) + 말미 코드 케이브(한글 입력 처리).

## 검증
- 적용 도구: **공식 xdelta3 3.0.11**(원저자 jmacd GitHub 릴리스, choco 승인 패키지 기준
  SHA256 `ECA9…86BF` 검증 후 사용).
- 소스 main_872001 SHA256 `30c55302…` = 델타 소스와 일치(xdelta3가 adler32도 검증).
- 결과 hangul main SHA256 `c83d37fc…`, 17,569,512바이트(+218).

## 파이프라인 통합 (이후 릴리즈 자동 반영)
xdelta3 의존 없이 재현하도록, 델타를 **복사/삽입 op 리스트**로 재표현했다:
- `tools/hangul_kbd_117.patch.json` (974B): 복사는 소스 오프셋 참조, 리터럴 82바이트만 저장.
  source/target SHA256로 무결성 확인. xdelta3 출력과 **바이트 완전 일치** 검증됨.
- `tools/apply_hangul_kbd.py`: `main_872001`(소스 SHA 확인) → `main_872001_hangul` 생성.
  소스가 다르면(main 재생성 등) 명확히 실패시켜 잘못된 main 배포를 막는다.
- `make_zip_v39.py`: 패키징 전에 `apply_hangul_kbd.py`를 실행하고, 872001 `exefs/main`을
  `main_872001_hangul`에서 가져온다. → **1.1.7 릴리스(v3.9, v4.0)마다 자동 포함.**

## 범위 / 주의
- **1.1.7 PUK(872001) 전용.** 1.1.5·1.1.4는 main 바이너리가 달라 이 델타가 적용되지 않는다
  (필요 시 각 버전 main 기준으로 별도 델타 필요).
- 검증 바이패스는 게임 기본 입력 제한을 푸는 것이므로, 게임 로직상 비정상 이름 저장 가능성은
  존재. 이슈에서 제작자·사용자·소유자가 동작 확인함.
- main을 재-포팅(예: 1.1.8)하면 `main_872001`의 SHA가 바뀌어 apply가 실패한다. 그때는 새 main
  기준으로 원저자 방식(또는 동일 바이트 편집)을 재적용해 `hangul_kbd_1XX.patch.json`을 갱신할 것.
