# -*- coding: utf-8 -*-
"""한글패치 통합 빌더 — 본인이 덤프한 게임 romfs/exefs + 이 저장소의 데이터만으로
배포용 패치 폴더(및 zip)를 만든다.

  python tools/build_patch.py --version 1.1.7 \
      --romfs-base "<...>/Program 0/romfs" --romfs-puk "<...>/Program 1/romfs" \
      --main-base  "<...>/Program 0/exefs/main" --main-puk "<...>/Program 1/exefs/main" \
      --images <한글화된 res_lang*.bin 이 있는 폴더> \
      --out build/1.1.7 --zip NobunagaShinsei_KR_for_1.1.7_PUK.zip

각 단계는 --skip-* 로 끌 수 있다. 이미지(res_lang 계열)는 게임 원본 아트가 포함된
대용량 파일이라 저장소에 없으며, 아래 중 하나로 준비한다(docs/BUILD.md 참고):
  * tools/fetch_release_images.py 로 공개 릴리스 zip에서 추출 (권장)
  * 직접 렌더 파이프라인으로 재생성

주의: MSG 텍스트 데이터(data/ko/*)는 **인덱스 기준**이라 게임 버전이 맞아야 한다.
문자열 개수가 다르면 명확한 오류로 중단된다.
"""
import os, sys, json, shutil, argparse, subprocess, hashlib, zipfile
sys.stdout.reconfigure(encoding='utf-8')

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
DATA = os.path.join(ROOT, 'data')
sys.path.insert(0, TOOLS)

TID_BASE = '01007ab012872000'
TID_PUK = '01007ab012872001'

# 게임 버전별 설정: MSG 데이터 위치와 PUK 적용 여부
VERSIONS = {
    '1.1.7': dict(puk=True,  ko_puk='puk_117', hangul_kbd=True),
    '1.1.5': dict(puk=True,  ko_puk='puk_115', hangul_kbd=False),
    '1.1.4': dict(puk=False, ko_puk=None,      hangul_kbd=False),
}
KO_BASE = 'base'          # 872000 (기본판) MSG — 게임 최초 출시(v0) romfs 기준


def run(cmd, env=None, cwd=None):
    e = dict(os.environ); e.update(env or {})
    r = subprocess.run(cmd, env=e, cwd=cwd or ROOT)
    if r.returncode != 0:
        sys.exit(f'실패: {" ".join(cmd)}')


def step_msg(args, cfg, out):
    """MSG / MSG_PK 텍스트 한글화 (data/ko 인덱스 테이블 적용)."""
    if args.romfs_base:
        jp = os.path.join(args.romfs_base, 'MSG', 'JP')
        dst = os.path.join(out, 'contents', TID_BASE, 'romfs', 'MSG', 'JP')
        print(f'[MSG] 기본판 텍스트 -> {dst}')
        run([sys.executable, os.path.join(TOOLS, 'ko_tables.py'), 'apply',
             '--jp', jp, '--data', os.path.join(DATA, 'ko', KO_BASE), '--out', dst])
    if cfg['puk'] and args.romfs_puk:
        jp = os.path.join(args.romfs_puk, 'MSG_PK', 'JP')
        dst = os.path.join(out, 'contents', TID_PUK, 'romfs', 'MSG_PK', 'JP')
        print(f'[MSG_PK] 파워업키트 텍스트 -> {dst}')
        run([sys.executable, os.path.join(TOOLS, 'ko_tables.py'), 'apply',
             '--jp', jp, '--data', os.path.join(DATA, 'ko', cfg['ko_puk']),
             '--out', dst, '--copy-rest'])


def step_dlc(args, cfg, out):
    """DLC_PK(크로스오버 콘텐츠) .n16 한글화."""
    if not (cfg['puk'] and args.romfs_puk):
        return
    src = os.path.join(args.romfs_puk, 'DLC_PK', 'JP')
    if not os.path.isdir(src):
        print('[DLC_PK] 원본 없음 — 건너뜀'); return
    dst = os.path.join(out, 'contents', TID_PUK, 'romfs', 'DLC_PK', 'JP')
    print(f'[DLC_PK] -> {dst}')
    run([sys.executable, os.path.join(TOOLS, 'apply_dlc_translations.py')],
        env={'DLC_PK_SRC': src, 'DLC_PK_OUT': dst}, cwd=TOOLS)


def step_aoc(args, cfg, out):
    """추가 시나리오 DLC(AddOnContent) 한글화 — DLC를 가진 사람만 해당."""
    if not args.aoc:
        print('[AOC] --aoc 미지정 — 건너뜀 (추가 시나리오 DLC 미보유면 정상)')
        return
    dst = os.path.join(out, 'contents')
    print(f'[AOC] {args.aoc} -> {dst}')
    run([sys.executable, os.path.join(TOOLS, 'apply_aoc_translations.py')],
        env={'AOC_SRC': args.aoc, 'AOC_OUT': dst}, cwd=TOOLS)


README_SRC = os.path.join(ROOT, 'docs', 'INSTALL.md')


def step_exefs(args, cfg, out):
    """exefs/main 시스템 메시지 한글화 (+1.1.7 PUK은 한국어 입력기)."""
    for main_in, tid in ((args.main_base, TID_BASE), (args.main_puk, TID_PUK)):
        if not main_in:
            continue
        if tid == TID_PUK and not cfg['puk']:
            continue
        dst = os.path.join(out, 'contents', tid, 'exefs', 'main')
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        print(f'[exefs] {tid} <- {main_in}')
        run([sys.executable, os.path.join(TOOLS, 'patch_main.py')],
            env={'SRC_MAIN': main_in, 'OUT_MAIN': dst}, cwd=TOOLS)
        if tid == TID_PUK and cfg['hangul_kbd'] and not args.skip_hangul_kbd:
            print('[exefs] 한국어 입력기 적용')
            tmp = dst + '.kbd'
            run([sys.executable, os.path.join(TOOLS, 'apply_hangul_kbd.py')],
                env={'IN': dst, 'OUT': tmp}, cwd=TOOLS)
            os.replace(tmp, dst)


def step_images(args, cfg, out):
    """한글화된 res_lang 계열(폰트+이미지) 복사."""
    if not args.images:
        print('[이미지] --images 미지정 — 건너뜀 (텍스트는 한글, 폰트/이미지는 원본 유지)')
        return
    placement = {
        'res_lang.bin':        [(TID_BASE, 'RES_JP'), (TID_PUK, 'RES_JP')],
        'res_lang_exp.bin':    [(TID_BASE, 'RES_JP'), (TID_PUK, 'RES_JP')],
        'res_lang_pk.bin':     [(TID_PUK, 'RES_JP_PK')],
        'res_lang_exp_pk.bin': [(TID_PUK, 'RES_JP_PK')],
    }
    for name, targets in placement.items():
        src = os.path.join(args.images, name)
        if not os.path.exists(src):
            continue
        for tid, sub in targets:
            if tid == TID_PUK and not cfg['puk']:
                continue
            dst = os.path.join(out, 'contents', tid, 'romfs', sub, name)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            print(f'[이미지] {name} -> {tid}/{sub}')


def step_zip(args, out):
    zf = args.zip
    if not zf:
        return
    print(f'[패키징] {zf}')
    if os.path.exists(zf):
        os.remove(zf)
    n = 0
    with zipfile.ZipFile(zf, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for root, _, files in os.walk(out):
            for f in sorted(files):
                p = os.path.join(root, f)
                arc = 'atmosphere/' + os.path.relpath(p, out).replace('\\', '/')
                z.write(p, arc); n += 1
        if os.path.exists(README_SRC):          # 설치 안내를 zip 루트에 동봉
            z.write(README_SRC, 'README.md'); n += 1
    print(f'  {n}개 파일, {os.path.getsize(zf):,} bytes')


def main():
    ap = argparse.ArgumentParser(description='노부나가의 야망 신생 한글패치 빌더')
    ap.add_argument('--version', required=True, choices=sorted(VERSIONS))
    ap.add_argument('--romfs-base', help='기본판(872000) romfs 폴더')
    ap.add_argument('--romfs-puk', help='파워업키트(872001) romfs 폴더')
    ap.add_argument('--main-base', help='기본판 exefs/main')
    ap.add_argument('--main-puk', help='파워업키트 exefs/main')
    ap.add_argument('--images', help='한글화된 res_lang*.bin 폴더')
    ap.add_argument('--aoc', help='추가 시나리오 DLC 추출 폴더 (romfs_<tid>/JP/*.n16)')
    ap.add_argument('--out', required=True, help='출력 폴더(= zip 속 atmosphere/)')
    ap.add_argument('--zip', help='만들 zip 경로')
    for s in ('msg', 'dlc', 'aoc', 'exefs', 'images', 'hangul-kbd'):
        ap.add_argument(f'--skip-{s}', action='store_true')
    args = ap.parse_args()

    cfg = VERSIONS[args.version]
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    print(f'=== 게임 {args.version} 패치 빌드 -> {out} ===')

    if not args.skip_msg:    step_msg(args, cfg, out)
    if not args.skip_dlc:    step_dlc(args, cfg, out)
    if not args.skip_aoc:    step_aoc(args, cfg, out)
    if not args.skip_exefs:  step_exefs(args, cfg, out)
    if not args.skip_images: step_images(args, cfg, out)
    step_zip(args, out)
    print('=== 완료 ===')


if __name__ == '__main__':
    main()
