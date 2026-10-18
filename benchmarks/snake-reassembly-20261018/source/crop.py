# blender -b -P crop.py -- in.png out.png x0 y0 x1 y1 [scale]  (top-left pixel coords)
import bpy,sys,numpy as np
a=sys.argv[sys.argv.index("--")+1:];src,dst=a[0],a[1];x0,y0,x1,y1=map(int,a[2:6]);s=float(a[6]) if len(a)>6 else 1
im=bpy.data.images.load(src);w,h=im.size;p=np.array(im.pixels[:],np.float32).reshape(h,w,im.channels)
c=p[h-y1:h-y0,x0:x1].copy();o=bpy.data.images.new("c",x1-x0,y1-y0,alpha=True);o.pixels=c.ravel() if c.shape[2]==4 else np.concatenate([c,np.ones(c.shape[:2]+(1,),np.float32)],2).ravel()
if s!=1:o.scale(int((x1-x0)*s),int((y1-y0)*s))
o.filepath_raw=dst;o.file_format='PNG';o.save()
