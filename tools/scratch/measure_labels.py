import os, sys
import numpy as np
from PIL import Image
sys.stdout.reconfigure(encoding='utf-8')
D = r'D:\nsw\rom\노부나가의 야망 신생_일본판\이미지한글화\png_jp'

for name in ['03_006_0', '03_014_0', '03_045_0', '03_101_0']:
    img = np.array(Image.open(os.path.join(D, name + '.png')))
    a = img[:, :, 3]
    ys, xs = np.nonzero(a > 30)
    print(f'{name}: size={img.shape[1]}x{img.shape[0]} ink x[{xs.min()}..{xs.max()}] y[{ys.min()}..{ys.max()}]')
    # fill color: pixels with high alpha and high luminance
    solid = img[(a > 240)]
    if len(solid):
        lum = solid[:, :3].astype(int).sum(1)
        bright = solid[lum > lum.max() - 90]
        dark = solid[lum < lum.min() + 90]
        print(f'  fill RGB ~{bright[:, :3].mean(0).round().astype(int)}  outline RGB ~{dark[:, :3].mean(0).round().astype(int)}')
    # column profile of first vs later chars: find char extents via column-gap segmentation
    colink = (a > 30).sum(0)
    on = colink > 0
    segs = []
    st = None
    for x, v in enumerate(on):
        if v and st is None: st = x
        if not v and st is not None:
            if x - st > 6: segs.append((st, x))
            st = None
    if st is not None: segs.append((st, len(on)))
    heights = []
    for s, e in segs[:4]:
        sub = a[:, s:e]
        yy, _ = np.nonzero(sub > 30)
        heights.append((e - s, yy.max() - yy.min() + 1))
    print(f'  first chars (w,h): {heights}')
