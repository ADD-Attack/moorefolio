import sys
from PIL import Image
ref,out=sys.argv[1],sys.argv[2]
im=Image.open(ref).convert('RGB')
bg=im.getpixel((1800,40)); print('bg',bg)
def sq(box,name):
    c=im.crop(box); w,h=c.size; s=int(max(w,h)*1.12)
    o=Image.new('RGB',(s,s),bg); o.paste(c,((s-w)//2,(s-h)//2)); o.resize((1024,1024),Image.LANCZOS).save(out+'\\'+name)
sq((0,20,1420,1168),'c1-wholebody.png')
sq((1060,250,1420,950),'c2-mouth.png')
sq((0,600,262,900),'c3-tail.png')
sq((880,180,1440,1010),'c2b-mouth.png')
