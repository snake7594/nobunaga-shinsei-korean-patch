# -*- coding: utf-8 -*-
"""erase_place variant for TRANSPARENT-background assets (no fill panel to inpaint into):
clears alpha to 0 within the dilated ink mask (instead of RGB-inpainting while leaving
alpha opaque, which leaves a smudgy dark ghost -- there's nothing to blend into on a
transparent canvas), then composites the KO text render on top."""
import sys
sys.path.insert(0,'.')
import koloc
import numpy as np, cv2
from PIL import Image

def erase_place_transparent(base, mask, bbox, ko, dilate=9, **style):
    x0,y0,x1,y1 = bbox
    m = cv2.dilate(mask, np.ones((dilate,dilate), np.uint8))
    out = base.copy()
    out[:,:,3][m>0] = 0
    out[:,:,:3][m>0] = 0
    img = Image.fromarray(out, 'RGBA')
    layer, ink = koloc.render_ko_fit(ko, x1-x0+1, y1-y0+1, **style)
    if layer is not None:
        jcx=(x0+x1)/2; jcy=(y0+y1)/2
        img.alpha_composite(layer,(int(round(jcx-ink[0])),int(round(jcy-ink[1]))))
    base[:,:,:] = np.array(img)
