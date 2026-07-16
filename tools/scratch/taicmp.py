from PIL import Image
a=Image.open('loc_src/e12_t0.png').convert('RGBA'); b=Image.open('loc_out/e12/t0.png').convert('RGBA')
def pair(x0,y0,x1,y1,name,sc=3):
    ca=a.crop((x0,y0,x1,y1)); cb=b.crop((x0,y0,x1,y1)); w,h=ca.size
    out=Image.new('RGBA',(w*sc,h*2*sc+6),(40,40,40,255))
    out.paste(ca.resize((w*sc,h*sc),Image.NEAREST),(0,0)); out.paste(cb.resize((w*sc,h*sc),Image.NEAREST),(0,h*sc+6))
    out.save(f'z_{name}.png')
pair(1560,20,1780,220,'tai',3)
pair(1800,165,1935,205,'senkou1',4)
