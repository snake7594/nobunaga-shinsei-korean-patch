# -*- coding: utf-8 -*-
"""공개 릴리스 zip에서 한글화된 res_lang 계열(폰트+이미지) 파일을 꺼낸다.

이 저장소에는 res_lang*.bin 이 들어 있지 않다 — 게임 원본 텍스처/폰트가 통째로 들어간
80MB급 파일이라 게임 데이터를 재배포하는 셈이 되기 때문이다. 대신 이미 공개 배포 중인
릴리스 zip에서 꺼내 쓴다. 이미지는 게임 버전이 올라가도 거의 바뀌지 않아, 새 버전
패치를 만들 때도 그대로 재사용하는 것이 정상 절차다.

  # 로컬 zip에서
  python tools/fetch_release_images.py --zip NobunagaShinsei_KR_for_1.1.7_PUK.zip --out images/

  # GitHub 릴리스에서 바로 (gh CLI 필요)
  python tools/fetch_release_images.py --release v4.0 --asset NobunagaShinsei_KR_for_1.1.7_PUK.zip --out images/
"""
import os, sys, zipfile, argparse, subprocess, tempfile, hashlib
sys.stdout.reconfigure(encoding='utf-8')

WANTED = ('res_lang.bin', 'res_lang_exp.bin', 'res_lang_pk.bin', 'res_lang_exp_pk.bin')
REPO = 'snake7594/nobunaga-shinsei-korean-patch'


def extract(zip_path, out):
    os.makedirs(out, exist_ok=True)
    got = {}
    with zipfile.ZipFile(zip_path) as z:
        for info in z.infolist():
            base = os.path.basename(info.filename)
            if base in WANTED and base not in got:
                data = z.read(info)
                dst = os.path.join(out, base)
                open(dst, 'wb').write(data)
                got[base] = (len(data), hashlib.sha256(data).hexdigest()[:16])
    if not got:
        sys.exit('zip 안에서 res_lang 계열 파일을 찾지 못했습니다.')
    for k, (n, h) in sorted(got.items()):
        print(f'  {k:22s} {n:>12,} B  sha256 {h}…')
    print(f'-> {out}')
    missing = [w for w in WANTED if w not in got]
    if missing:
        print(f'참고: 이 zip에 없는 파일 {missing} (해당 게임 버전에서 쓰지 않으면 정상)')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--zip', help='로컬 릴리스 zip 경로')
    ap.add_argument('--release', help='GitHub 릴리스 태그 (예: v4.0)')
    ap.add_argument('--asset', help='릴리스 자산 파일명')
    ap.add_argument('--repo', default=REPO)
    ap.add_argument('--out', required=True, help='추출할 폴더')
    a = ap.parse_args()

    if a.zip:
        extract(a.zip, a.out); return
    if not (a.release and a.asset):
        sys.exit('--zip 또는 (--release 와 --asset) 중 하나가 필요합니다.')
    with tempfile.TemporaryDirectory() as td:
        print(f'릴리스 {a.release} 에서 {a.asset} 내려받는 중…')
        r = subprocess.run(['gh', 'release', 'download', a.release, '--repo', a.repo,
                            '--pattern', a.asset, '--dir', td])
        if r.returncode != 0:
            sys.exit('gh release download 실패 — gh CLI 로그인 상태를 확인하세요.')
        extract(os.path.join(td, a.asset), a.out)


if __name__ == '__main__':
    main()
