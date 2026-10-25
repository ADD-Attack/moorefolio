import sys
from PIL import Image
m,ref,cap,out=sys.argv[1:5]; h=720
M=Image.open(m).convert('RGB'); R=Image.open(ref).convert('RGB'); C=Image.open(cap).convert('RGB').crop((250,150,950,1000))
ims=[x.resize((int(x.width*h/x.height),h)) for x in (M,R,C)]
o=Image.new('RGB',(sum(i.width for i in ims),h),(220,210,202)); x=0
for i in ims: o.paste(i,(x,0)); x+=i.width
o.save(out)
