from PIL import Image
b=Image.open('loc_out/e12/t0.png').convert('RGBA')
b.crop((1805,166,1935,202)).resize((130*5,36*5),Image.NEAREST).save('z_s1only.png')
