# -*- coding: utf-8 -*-
"""파워업키트 원형(방사형) 명령 메뉴 버튼 한글화 — res_lang_pk 엔트리 1.

기본 게임의 원형 메뉴(res_lang 엔트리 8)는 예전에 한글화했지만, **파워업키트가 추가한
명령 버튼은 별도 아틀라스(res_lang_pk 엔트리 1)**에 있어 일본어로 남아 있었다.
배지 78개 = 라벨 10종 × 상태 색상 변형.

각 배지에서 라벨 글자를 인페인팅으로 지우고, 원본 글자색을 그대로 뽑아 한글을 같은
자리에 렌더링한다. 완전히 같은 배지는 한 번만 처리해 결과를 복사한다.

  PK_RES_SRC : 원본 res_lang_pk (색·구조 기준)
  PK_RES_BASE: 결과를 얹을 파일(기본=SRC). 이미 한글화된 배포본을 주면 그 위에 반영
  PK_RES_OUT : 출력
  PREVIEW    : 미리보기 PNG 경로(선택)
"""
import sys, os, hashlib
import numpy as np
import cv2
sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SP)
import koloc
from PIL import Image

ENTRY = 1
SRC = os.environ.get('PK_RES_SRC') or r'D:\nsw\rom\1.1.7\extract\Program 1\romfs\RES_JP_PK\res_lang_pk.bin'
BASE = os.environ.get('PK_RES_BASE') or SRC
OUT = os.environ.get('PK_RES_OUT') or os.path.join(SP, 'res_lang_pk_wheel.bin')
PREVIEW = os.environ.get('PREVIEW')
FONT = os.environ.get('KO_FONT') or r'D:\nsw\rom\노부나가의 야망 신생_일본판\추출원본\SeoulHangangB.ttf'

# 라벨 모양 해시 -> 한국어. 해시는 라벨 밴드의 알파 실루엣이라 색 변형과 무관하다.
KO_BY_LABEL = {
    '解除': '해제', '編集': '편집', '共闘': '공투', '広域': '광역', '増援': '증원',
    '待機': '대기', '攻城戦': '공성전', '城役割': '성 역할',
    '補給拠点': '보급 거점', '防衛拠点': '방위 거점',
}
# 그룹 크기 순서(큰 것부터)로 확인한 라벨 — e01_cells 분석 결과와 일치해야 한다
GROUP_ORDER = ['解除', '編集', '共闘', '広域', '増援', '待機', '攻城戦', '城役割', '補給拠点', '防衛拠点']


def badges(rgba):
    """알파 연결 성분으로 배지 bbox 목록을 찾는다."""
    m = (rgba[:, :, 3] > 25).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    out = []
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if 40 <= w <= 90 and 40 <= h <= 80:
            out.append((int(x), int(y), int(w), int(h)))
    out.sort(key=lambda c: (c[1] // 20, c[0]))
    return out


def label_key(rgba, box):
    x, y, w, h = box
    band = rgba[y + int(h * 0.60):y + h, x:x + w]
    sil = (band[:, :, 3] > 60).astype(np.uint8)
    return hashlib.md5(sil.tobytes() + bytes([w, h, sil.shape[0]])).hexdigest()[:10]


def main():
    src = open(SRC, 'rb').read()
    _, _, _, g = koloc.entry_gt1g(src, ENTRY)
    texs = koloc.g1t_textures(g)
    tex = texs[0]
    rgba = tex['rgba'].copy()
    boxes = badges(rgba)
    print(f'배지 {len(boxes)}개')

    # 라벨 그룹 만들기 → 개수 많은 순으로 GROUP_ORDER 매칭
    groups = {}
    for b in boxes:
        groups.setdefault(label_key(rgba, b), []).append(b)
    ordered = sorted(groups.items(), key=lambda kv: -len(kv[1]))
    if len(ordered) != len(GROUP_ORDER):
        sys.exit(f'라벨 그룹 수가 예상과 다릅니다: {len(ordered)} != {len(GROUP_ORDER)}')
    key2ko = {}
    for (k, v), jp in zip(ordered, GROUP_ORDER):
        key2ko[k] = KO_BY_LABEL[jp]
        print(f'  {jp:5s} -> {KO_BY_LABEL[jp]:7s} {len(v):3d}개')

    fb = open(FONT, 'rb').read()
    # 완전히 같은 배지는 한 번만 처리
    cache = {}
    done = 0
    for (x, y, w, h) in boxes:
        crop = rgba[y:y + h, x:x + w]
        ch = hashlib.md5(crop.tobytes()).hexdigest()
        if ch in cache:
            rgba[y:y + h, x:x + w] = cache[ch]
            continue
        patch = localize_badge(crop.copy(), key2ko[label_key(rgba, (x, y, w, h))], fb)
        cache[ch] = patch
        rgba[y:y + h, x:x + w] = patch
        done += 1
    print(f'고유 배지 {done}개 처리 (전체 {len(boxes)}개)')

    if PREVIEW:
        im = Image.fromarray(rgba, 'RGBA')
        bg = Image.new('RGBA', im.size, (25, 25, 30, 255))
        Image.alpha_composite(bg, im).convert('RGB').save(PREVIEW)
        print('미리보기 ->', PREVIEW)

    # 엔트리 재조립 후 바탕 파일에 반영
    base = open(BASE, 'rb').read()
    newres = koloc.rebuild_reslang(BASE, OUT, {ENTRY: {0: rgba}})
    print('저장 ->', OUT)


def localize_badge(crop, ko, font_bytes):
    """배지 하나: 라벨 글자를 지우고 같은 색으로 한글을 렌더."""
    h, w = crop.shape[:2]
    y0 = 36                     # 라벨 글자는 항상 이 아래(판 밑 빛무리 위)에 있다
    band = crop[y0:h]
    rgb = band[:, :, :3].astype(int); al = band[:, :, 3]
    lum = rgb.mean(axis=2)
    # 글자 획은 '고주파', 빛무리·판은 '저주파'. 흐린 판과의 차이로 획만 골라낸다.
    blur = cv2.GaussianBlur(lum.astype(np.float32), (0, 0), 2.4)
    vis = al > 40
    mask = ((np.abs(lum - blur) > 16) & vis).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    nlab, lab2, st2, _ = cv2.connectedComponentsWithStats(mask, 8)
    keep = np.zeros_like(mask)
    for i in range(1, nlab):
        if st2[i, cv2.CC_STAT_AREA] >= 8:
            keep[lab2 == i] = 1
    mask = keep
    if mask.sum() < 20:
        return crop
    inner = vis
    ys, xs = np.nonzero(mask)
    bx0, bx1, by0, by1 = xs.min(), xs.max(), ys.min(), ys.max()
    # 판 아래 테두리가 마스크에 섞여 글자 상자가 아래로 늘어나면 글자가 배지 밖으로 잘린다.
    # 라벨이 실제로 앉는 구간(배지 좌표 38~52행)으로 제한한다.
    by0 = max(int(by0), 38 - y0)
    by1 = min(int(by1), 52 - y0)
    if by1 - by0 < 5:
        by0, by1 = 38 - y0, 52 - y0
    core = mask.astype(bool)
    # 글자색은 '획에서 가장 진한/가장 밝은 쪽'을 쓴다. 중앙값을 쓰면 배경과 섞여 흐려진다.
    halo = cv2.dilate(mask, np.ones((7, 7), np.uint8), 2).astype(bool) & ~core & inner
    halo_lum = float(np.median(lum[halo])) if halo.sum() > 10 else float(np.median(lum[inner]))
    glyph_lum = lum[core]
    dark_text = float(np.median(glyph_lum)) < halo_lum       # 밝은 바탕 위 어두운 글자?
    q = 12 if dark_text else 88
    thr = np.percentile(glyph_lum, q)
    pick = core & ((lum <= thr) if dark_text else (lum >= thr))
    if pick.sum() < 6:
        pick = core
    text_rgb = tuple(int(v) for v in np.median(rgb[pick], axis=0))
    # 테두리·빛무리는 글자 주변 색(원본 느낌 유지) — 대비가 모자라면 흑/백으로 보정
    stroke_rgb = tuple(int(v) for v in np.median(rgb[halo], axis=0)) if halo.sum() > 10 else (250, 250, 250)
    if abs(sum(text_rgb) - sum(stroke_rgb)) < 150:
        stroke_rgb = (250, 250, 250) if dark_text else (20, 24, 38)

    # --- 글자 지우기: 획 자리를 '흐린 판(빛무리)' 색으로 되돌린다 ---
    # 빛무리는 저주파라 흐린 영상이 곧 배경이다. 획만 정확히 걷히고 빛무리는 남는다.
    md = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=1).astype(bool)
    bg_rgb = np.dstack([cv2.GaussianBlur(band[:, :, c].astype(np.float32), (0, 0), 2.6)
                        for c in range(3)])
    band[:, :, :3][md] = np.clip(bg_rgb[md], 0, 255).astype(np.uint8)

    # --- 한글 얹기 (원본 글자 자리에 맞춰) ---
    layer, ink = koloc.render_ko_fit(
        ko, int(bx1 - bx0 + 1), int(by1 - by0 + 1),
        font_bytes=font_bytes, text_rgb=text_rgb, stroke_rgb=stroke_rgb,
        glow_rgb=stroke_rgb, glow_a=210, glow_stroke=1.4, glow_blur=0.9,
        fill=1.0, stroke_ratio=1.15)
    if layer is not None:
        img = Image.fromarray(crop, 'RGBA')
        cx = (bx0 + bx1) / 2
        cy = y0 + (by0 + by1) / 2
        img.alpha_composite(layer, (int(round(cx - ink[0])), int(round(cy - ink[1]))))
        crop[:, :, :] = np.array(img)
    return crop


if __name__ == '__main__':
    main()
