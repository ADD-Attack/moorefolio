"""Geometry-distance weather masks; no changes to mesh/UVs. numpy/scipy/Pillow.
R = convex/boundary edge proximity; G = concave edge proximity. Not color/normal final maps.
"""
import sys,json,time
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.spatial import cKDTree
from scipy.ndimage import distance_transform_edt
T=Path(sys.argv[1]);O=T/'material/masks';O.mkdir(exist_ok=True)
def tree(edges):
 samples=[]
 for a,b in edges:
  n=max(2,int(np.linalg.norm(b-a)/.002)+2);samples.append(a+(b-a)*np.linspace(0,1,n)[:,None])
 return cKDTree(np.concatenate(samples)) if samples else None
report={}
for path in sorted((T/'material/mask-input').glob('*.npz')):
 start=time.time();d=np.load(path);V,F,U=d['V'],d['F'],d['U'];tc=tree(d['convex']);tg=tree(d['cavity']);size=4096 if path.stem=='SRC_Head' else 2048
 out=np.zeros((size,size,3),np.float32);covered=np.zeros((size,size),bool)
 for ids,uv in zip(F,U):
  p=uv*(size-1);mn=np.maximum(0,np.floor(p.min(0)).astype(int));mx=np.minimum(size-1,np.ceil(p.max(0)).astype(int))
  if np.any(mx<mn):continue
  den=(p[1,1]-p[2,1])*(p[0,0]-p[2,0])+(p[2,0]-p[1,0])*(p[0,1]-p[2,1])
  if abs(den)<1e-9:continue
  ys,xs=np.mgrid[mn[1]:mx[1]+1,mn[0]:mx[0]+1];x=xs+.5;y=ys+.5
  a=((p[1,1]-p[2,1])*(x-p[2,0])+(p[2,0]-p[1,0])*(y-p[2,1]))/den
  b=((p[2,1]-p[0,1])*(x-p[2,0])+(p[0,0]-p[2,0])*(y-p[2,1]))/den;c=1-a-b;ok=(a>=-1e-6)&(b>=-1e-6)&(c>=-1e-6)
  if not ok.any():continue
  xx=xs[ok];yy=ys[ok];points=a[ok,None]*V[ids[0]]+b[ok,None]*V[ids[1]]+c[ok,None]*V[ids[2]]
  for channel,tr,width in [(0,tc,.014),(1,tg,.032)]:
   if tr is not None:
    dd=tr.query(points)[0];f=np.clip((width-dd)/(width-.0015),0,1);out[yy,xx,channel]=f*f*(3-2*f)
  covered[yy,xx]=True
 dist,indices=distance_transform_edt(~covered,return_indices=True);pad=(~covered)&(dist<=10);out[pad]=out[indices[0][pad],indices[1][pad]]
 img=np.round(np.clip(out,0,1)*255).astype(np.uint8);Image.fromarray(img[::-1]).save(O/(path.stem+'_EdgeMask.png'))
 report[path.stem]={'size':size,'convex_edges':len(d['convex']),'concave_edges':len(d['cavity']),'covered_texels':int(covered.sum()),'seconds':round(time.time()-start,2)};print(path.stem,report[path.stem],flush=True)
(O/'mask-report.json').write_text(json.dumps(report,indent=2))
