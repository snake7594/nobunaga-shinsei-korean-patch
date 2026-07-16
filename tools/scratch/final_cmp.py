from PIL import Image
a=Image.open('loc_src/e12_t0.png').convert('RGBA'); b=Image.open('loc_out/e12/t0.png').convert('RGBA')
def pair(x0,y0,x1,y1,name,sc):
    ca=a.crop((x0,y0,x1,y1)); cb=b.crop((x0,y0,x1,y1)); w,h=ca.size
    out=Image.new('RGBA',(w*sc,h*2*sc+6),(50,50,50,255))
    out.paste(ca.resize((w*sc,h*sc),Image.NEAREST),(0,0)); out.paste(cb.resize((w*sc,h*sc),Image.NEAREST),(0,h*sc+6))
    out.save(f'z_{name}.png')
pair(770,128,1060,172,'btn',3)
