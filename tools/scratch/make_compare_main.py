# -*- coding: utf-8 -*-
import io, os, sys
from PIL import Image, ImageDraw, ImageFont
sys.stdout.reconfigure(encoding='utf-8')
SP = os.path.dirname(os.path.abspath(__file__))

def font(p, s):
    return ImageFont.truetype(io.BytesIO(open(p, 'rb').read()), s)

jp_path = r'C:\Windows\Fonts\meiryo.ttc'
jp_f = font(jp_path, 24) if os.path.exists(jp_path) else font(r'C:\Windows\Fonts\malgun.ttf', 24)
ko_f = font(r'C:\Windows\Fonts\malgun.ttf', 24)
h_f = font(r'C:\Windows\Fonts\malgunbd.ttf', 26)

rows = [
    ('チュートリアルを行いますか?', '튜토리얼을 진행할까요?'),
    ('セーブデータが壊れています', '세이브 데이터가 손상됨'),
    ('ダウンロードコンテンツが見つかりません', '다운로드 콘텐츠를 찾을 수 없음'),
    ('グラフィックライブラリ初期化エラー2', '그래픽 라이브러리 초기화 오류2'),
    ('マイドキュメントの取得に失敗', '내 문서 폴더 접근 실패'),
    ("イベントデータが不正です：'%04d.bin'", "이벤트 데이터 오류：'%04d.bin'"),
]
W, RH = 1180, 64
img = Image.new('RGB', (W, len(rows) * RH + 100), (26, 26, 40))
dr = ImageDraw.Draw(img)
dr.text((30, 18), 'exefs/main 하드코딩 일본어 → 한글 (v1.4)', font=h_f, fill=(150, 220, 150))
dr.text((300, 60), '원본 (일본어)', font=ko_f, fill=(230, 200, 140))
dr.text((820, 60), '한글화', font=ko_f, fill=(150, 220, 150))
for i, (jp, ko) in enumerate(rows):
    y = 100 + i * RH
    dr.text((30, y), jp, font=jp_f, fill=(210, 210, 215))
    dr.text((610, y), '→', font=ko_f, fill=(120, 120, 150))
    dr.text((670, y), ko, font=ko_f, fill=(235, 235, 180))
out = os.path.join(SP, 'compare_main_v14.png')
img.save(out)
print('saved', img.size)
