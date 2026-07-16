from PIL import Image, ImageDraw
im=Image.open('loc_src/e12_t0.png').convert('RGBA')
crop=im.crop((1790,0,1960,210)).resize((170*3,210*3),Image.NEAREST)
d=ImageDraw.Draw(crop)
for y in range(0,210,10):
    py=y*3; d.line([(0,py),(crop.width,py)],fill=(0,255,255,255))
    if y%20==0: d.text((1,py),str(y),fill=(0,255,255,255))
for x in range(1790,1960,20):
    px=(x-1790)*3; d.line([(px,0),(px,crop.height)],fill=(255,0,255,255)); d.text((px+1,1),str(x),fill=(255,0,255,255))
crop.save('z_col.png')
