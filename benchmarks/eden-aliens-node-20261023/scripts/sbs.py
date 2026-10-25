import sys
from PIL import Image
ref,cap,out=sys.argv[1:4]
r=Image.open(ref).convert('RGB'); c=Image.open(cap).convert('RGB')
c=c.crop((250,150,950,1000)); h=720
r=r.resize((int(r.width*h/r.height),h)); c=c.resize((int(c.width*h/c.height),h))
o=Image.new('RGB',(r.width+c.width,h),(220,210,202)); o.paste(r,(0,0)); o.paste(c,(r.width,0)); o.save(out)
