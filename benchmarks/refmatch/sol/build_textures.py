"""Deterministic worn-gunmetal trim atlas; Python3 + numpy + Pillow."""
from PIL import Image,ImageDraw,ImageFilter
import numpy as np,random,os
OUT=os.path.join(os.path.dirname(__file__),'textures');os.makedirs(OUT,exist_ok=True)
def make(name,seed):
 r=random.Random(seed); N=2048; S=512
 alb=Image.new('RGB',(N,N)); rough=Image.new('L',(N,N)); height=Image.new('L',(N,N),128); ao=Image.new('L',(N,N),255); metal=Image.new('L',(N,N),235)
 for t in range(16):
  ox=(t%4)*S;oy=(t//4)*S
  tone=r.randint(94,150); tint=r.choice([(0,3,6),(6,3,-2),(-3,0,3)])
  p=Image.new('RGB',(S,S),tuple(tone+c for c in tint));d=ImageDraw.Draw(p)
  h=Image.new('L',(S,S),128);hd=ImageDraw.Draw(h)
  a=Image.new('L',(S,S),255);ad=ImageDraw.Draw(a)
  ro=Image.new('L',(S,S),r.randint(95,151));rd=ImageDraw.Draw(ro)
  for j in range(170):
   x=r.randrange(S);y=r.randrange(S);w=r.randrange(8,95);hh=r.randrange(2,36)
   delta=r.randint(-23,12);col=tuple(max(0,min(255,tone+c+delta)) for c in tint)
   d.ellipse((x,y,x+w,y+hh),fill=col);rd.ellipse((x,y,x+w,y+hh),fill=r.randint(118,184))
  p=p.filter(ImageFilter.GaussianBlur(5));d=ImageDraw.Draw(p)
  d.rounded_rectangle((19,19,493,493),radius=29,outline=(48,48,44),width=5)
  ad.rounded_rectangle((18,18,494,494),radius=29,outline=150,width=12)
  for j in range(160):
   side=r.randrange(4);q=r.randrange(32,480);ln=r.randrange(2,35)
   if side==0: xy=(q,23,min(486,q+ln),25)
   elif side==1:xy=(q,487,min(486,q+ln),490)
   elif side==2:xy=(23,q,25,min(486,q+ln))
   else:xy=(487,q,490,min(486,q+ln))
   d.rectangle(xy,fill=(194,199,198));hd.rectangle(xy,fill=100);rd.rectangle(xy,fill=65)
  for j in range(210):
   x=r.randint(30,480);y=r.randint(30,480);ln=r.randint(2,65);dy=r.randint(-9,9)
   col=r.choice([(175,182,183),(63,65,63),(139,146,148)])
   d.line((x,y,min(488,x+ln),max(24,min(488,y+dy))),fill=col,width=r.choice([1,1,2]));hd.line((x,y,min(488,x+ln),max(24,min(488,y+dy))),fill=r.choice([110,145]),width=1)
  # Inset engraved dogleg plate seams and chipped machined witness lines.
  d.line([(350,52),(350,104),(420,104),(420,175)],fill=(43,46,44),width=4)
  d.line([(353,52),(353,101),(423,101),(423,175)],fill=(170,175,172),width=2)
  hd.line([(350,52),(350,104),(420,104),(420,175)],fill=100,width=4)
  d.text((54,441),'A'+str(seed)+' / '+str(t).zfill(2),fill=(48,52,51))
  for k in range(4): d.line((57+k*8,420,57+k*8,430),fill=(182,184,177),width=2)
  alb.paste(p,(ox,oy));rough.paste(ro.filter(ImageFilter.GaussianBlur(8)),(ox,oy));height.paste(h,(ox,oy));ao.paste(a,(ox,oy))
 ar=np.array(alb).astype(float);rng=np.random.default_rng(seed);ar=np.clip(ar+rng.normal(0,1.8,(N,N,1)),0,255).astype('uint8')
 h=np.array(height).astype(float); gy,gx=np.gradient(h);nn=np.stack((-gx*.018,gy*.018,np.ones_like(h)),axis=-1);nn/=np.linalg.norm(nn,axis=-1,keepdims=True)
 Image.fromarray(ar).save(OUT+'/'+name+'_albedo.png');Image.fromarray(((nn*.5+.5)*255).astype('uint8')).save(OUT+'/'+name+'_normal.png')
 Image.merge('RGB',(ao,rough,metal)).save(OUT+'/'+name+'_orm.png')
make('head',171);make('body',417)
Image.new('RGB',(64,64),(16,255,213)).save(OUT+'/cyan_emission.png')

# Fine woven stainless grille: real OpenGL relief normals + ORM, not a flat black vent.
N=512
y,x=np.mgrid[0:N,0:N].astype(float)
f1=np.abs(((x+y)%32)-16);f2=np.abs(((x-y)%32)-16)
wire=np.minimum(f1,f2);height=np.clip((3-wire)/3,0,1)
col=np.zeros((N,N,3));col[:]=[15,19,20];col+=height[:,:,None]*np.array([82,85,83])
gy,gx=np.gradient(height);normal=np.stack((-gx*2,gy*2,np.ones_like(gx)),axis=-1);normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
Image.fromarray(col.astype('uint8')).save(OUT+'/grille_albedo.png')
Image.fromarray(((normal*.5+.5)*255).astype('uint8')).save(OUT+'/grille_normal.png')
orm=np.stack((.4+.6*height,.55-.18*height,.9*np.ones_like(height)),axis=-1)
Image.fromarray((orm*255).astype('uint8')).save(OUT+'/grille_orm.png')
