"""F8 machined drum: explicit traces in ORIGINAL R2 clay-map (x, degrees).
Executed by build_fix.py after S0-3 is applied to source clay, before its projection.
Surface heights come from radial raycasts of the corrected clay, not a template.
"""
from mathutils.geometry import delaunay_2d_cdt
BMV=[]; BMF=[]; PARTS={}; TRACE=[]; SMOOTH_FACES=[]
bmm=bmesh.new();bmm.from_mesh(seg_master.data);sbvh=BVHTree.FromBMesh(bmm)
KAX=LOG['refines'][-1]['k']
def sampled(x,a):
 a=math.radians(a);d=Vector((0,math.cos(a),math.sin(a)))
 hit=sbvh.ray_cast(Vector((x*KAX,0,0))+1.5*d,-d)
 return math.hypot(hit[0].y,hit[0].z) if hit[0] is not None else R_RING

def radial(p,r):
 x,a=p;a=math.radians(a);return (x*KAX,r*math.cos(a),r*math.sin(a))
def add(name,vs,fs):
 if name=='B4-pistons': SMOOTH_FACES.extend(range(len(BMF),len(BMF)+len(fs)-1))
 k=len(BMV);BMV.extend(vs);BMF.extend([tuple(k+i for i in f) for f in fs]);PARTS[name]=PARTS.get(name,0)+sum(len(f)-2 for f in fs)
def inside(p,poly):
 x,y=p;v=False
 for (x1,y1),(x2,y2) in zip(poly,poly[1:]+poly[:1]):
  if (y1>y)!=(y2>y) and x<(x2-x1)*(y-y1)/(y2-y1)+x1:v=not v
 return v

def plate(name,outline,holes=(),anchors=(),offset=0):
 # Constrained triangulation: no triangles span aperture interiors.
 points=list(outline); edges=[(i,(i+1)%len(points)) for i in range(len(points))]
 for hole in holes:
  k=len(points);points+=hole;edges +=[(k+i,k+(i+1)%len(hole)) for i in range(len(hole))]
 points+=list(anchors)
 uv=[Vector((x,a*.0087)) for x,a in points]
 vv,ee,ff,*_=delaunay_2d_cdt(uv,edges,[],0,1e-6)
 rr=[];vs=[];fs=[]
 for q in vv:
  p=(q.x,q.y/.0087);r=sampled(*p);r=max(.425,min(.515,r))+offset;rr.append(r);vs.append(radial(p,r))
 for f in ff:
  p=np.mean([vv[i] for i in f],axis=0);p=(p[0],p[1]/.0087)
  if inside(p,outline) and not any(inside(p,h) for h in holes):fs.append(tuple(f))
 # Finite plate thickness: traced edges and hole walls, no underside hidden faces.
 for poly in [outline]+list(holes):
  for p,q in zip(poly,poly[1:]+poly[:1]):
   rp=max(.425,min(.515,sampled(*p)))+offset;rq=max(.425,min(.515,sampled(*q)))+offset
   k=len(vs);vs += [radial(p,rp),radial(q,rq),radial(q,rq-.025),radial(p,rp-.025)];fs.append((k,k+1,k+2,k+3))
 add(name,vs,fs);TRACE.append(dict(name=name,outline=outline,holes=holes,heights='radial ray cast corrected source; .425-.515 structural plate bounds'))

def window(name,p,slats=4):
 # Frame ring, bevel descending to inset; open slats with deep clay backing.
 pts=np.array(p,float);c=pts.mean(0);inner=c+(pts-c)*.79
 base=float(np.median([sampled(*q) for q in p]));base=max(.44,min(.515,base))
 vs=[radial(q,base+.006) for q in p]+[radial(q,base-.012) for q in inner]+[radial(q,base-.055) for q in inner]
 n=len(p);fs=[]
 for i in range(n):
  j=(i+1)%n;fs +=[(i,j,n+j,n+i),(n+i,n+j,2*n+j,2*n+i)]
 fs.append(tuple(range(2*n,3*n)))
 # straight bars along angular direction: full modeled ribbon top + side for shadow
 xmin,amin=inner.min(0);xmax,amax=inner.max(0)
 for j in range(slats):
  x=xmin+(j+1)/(slats+1)*(xmax-xmin);w=.008
  k=len(vs);q=[(x-w,amin),(x+w,amin),(x+w,amax),(x-w,amax)]
  vs +=[radial(v,base-.021) for v in q]+[radial(v,base-.032) for v in q]
  fs +=[(k,k+1,k+2,k+3),(k,k+3,k+7,k+4)]
 add(name,vs,fs);TRACE.append(dict(name=name,outline=p,radius=base,depth=.055,slats=slats))

def strip(name,x0,x1,a0,a1,r,n=3):
 vs=[];fs=[]
 for a in np.linspace(a0,a1,n+1):vs.extend([radial((x0,a),r),radial((x1,a),r),radial((x0,a),r-.018),radial((x1,a),r-.018)])
 for i in range(n):
  k=i*4;fs.extend([(k,k+1,k+5,k+4),(k,k+4,k+6,k+2),(k+1,k+3,k+7,k+5)])
 add(name,vs,fs)

def ring(name,xprofile,n=20):
 vs=[];fs=[]
 for x,r in xprofile:
  for i in range(n):vs.append(radial((x,i*360/n),r))
 for j in range(len(xprofile)-1):
  for i in range(n):k=j*n+i;l=j*n+(i+1)%n;fs.append((k,l,l+n,k+n))
 add(name,vs,fs)

# Original map traces: main shield near -Y; opposite-side plate traced separately.
Gtop=[(-.295,113),(-.06,113),(-.065,125),(-.275,125)]
Gside=[(-.035,143),(.015,137),(.145,137),(.145,154),(-.035,154)]
Gback=[(-.28,35),(-.045,35),(-.045,44),(-.28,44)]
upper=[(-.485,94),(-.30,94),(-.30,111),(-.06,111),(-.06,94),(.175,94),(.175,125),(.175,156),(.01,165),(-.045,174),(-.045,165),(-.29,165),(-.32,159),(-.485,157),(-.485,125)]
plate('B2-main-shield',upper,[Gtop,Gside],[(-.40,142),(-.17,140),(.09,126)])
plate('B2-opposite-shield',[(-.485,22),(-.30,14),(-.045,14),(.175,22),(.175,54),(.175,84),(-.06,84),(-.06,94),(-.30,94),(-.30,84),(-.485,84),(-.485,54)],[Gback],[(-.39,55),(-.17,65),(.08,55)])
plate('B6-lower-plate',[(-.485,-157),(-.30,-164),(-.045,-164),(.175,-157),(.175,-125),(.175,-95),(.175,-65),(.175,-22),(-.045,-14),(-.30,-14),(-.485,-22),(-.485,-65),(-.485,-95),(-.485,-125)],[[(-.285,-145),(-.045,-145),(-.045,-129),(-.285,-129)]],[(-.39,-90),(.08,-90),(-.17,-135),(-.17,-45)])
plate('B6-recess-floor',[(-.279,-144),(-.051,-144),(-.051,-130),(-.279,-130)],offset=-.025)

for name,p,n in [('B3-upper-grille',Gtop,4),('B3-side-grille',Gside,4),('B3-opposite-grille',Gback,4),('B3-waist-grille',[(-.28,170),(-.055,170),(-.055,190),(-.28,190)],4)]:window(name,p,n)
strip('B2-tab',-.30,-.06,85,110,.525,2)
strip('B2-ledge',-.045,.175,157,162,.455,1)
strip('B4-waist-band',-.30,-.045,-14,14,.43,2)
# fitted backing and housing lips; radii measured from actual clay housing
ring('B8-core',[(TX/KAX,.34),(HX/KAX,.34)],20)
ring('B8-housing',[(TX/KAX,R_RING+.01),(TX/KAX+.012,R_RING-.015),(TX/KAX+.075,R_RING-.015),(TX/KAX+.086,R_RING+.01),(TX/KAX+.10,R_RING+.01)],16)
ring('B8-forward-lip',[(HX/KAX-.025,.40),(HX/KAX,.43)],20)
# Close only the concealed core ends, without capping the visible insert channel.
for x in [TX/KAX,HX/KAX]:
 add('B8-core-caps',[radial((x,j*18),.34) for j in range(20)],[tuple(range(20))])
# The reference waist pistons run axially. Clay centres are near angle 180/0.
for ang in [0,180]:
 for x0,x1 in [(-.48,-.30),(-.045,.175)]:
  rr=sampled((x0+x1)/2,ang)
  axis=Vector((1,0,0));a=math.radians(ang);ct=Vector((0,rr*math.cos(a),rr*math.sin(a)))
  profile=[(x0,.045),(x0+.025,.055),(x1-.04,.055),(x1-.04,.035),(x1,.035)]
  vs=[];fs=[]
  for x,r in profile:
   for j in range(6):
    t=j*math.tau/6;vs.append(tuple(ct+Vector((x*KAX,r*math.cos(t),r*math.sin(t)))))
  for k in range(len(profile)-1):
   for j in range(6):fs.append((k*6+j,k*6+(j+1)%6,(k+1)*6+(j+1)%6,(k+1)*6+j))
  fs.append(tuple(range(24,30)))
  add('B4-pistons',vs,fs)
  bx=-.345 if x0<-.3 else -.045
  strip('B5-bracket',bx,bx+.045,ang-12,ang+12,rr+.04,2)
  # Narrow machined end collar, fitted to this piston axis.
  cv=[];cf=[]
  for x in [x1-.065,x1-.045]:
   for j in range(6):
    t=j*math.tau/6;cv.append(tuple(ct+Vector((x*KAX,.064*math.cos(t),.064*math.sin(t)))))
  for j in range(6):cf.append((j,(j+1)%6,(j+1)%6+6,j+6))
  add('B4-end-collars',cv,cf)
# Hexagonal heads fitted against the FINISHED traced panel, not the pre-panel source.
finished_bvh=BVHTree.FromPolygons([Vector(v) for v in BMV],BMF)
for x,a in [(-.43,130),(-.40,151),(.11,127),(-.25,159),(-.43,32),(.12,30),(-.40,72),(.1,75),(-.40,-143),(.11,-145)]:
 r=max(.425,min(.515,sampled(x,a)));n=Vector((0,math.cos(math.radians(a)),math.sin(math.radians(a))));hit=finished_bvh.ray_cast(Vector((x*KAX,0,0))+n*2,-n)
 assert hit[0] is not None,('fastener seat miss',x,a)
 c=hit[0];nh=hit[1].normalized();n=nh if nh.dot(n)>0 else -nh;u=Vector((1,0,0));u=(u-n*u.dot(n)).normalized();v=n.cross(u);vs=[];fs=[]
 for rad,height in [(.025,.002),(.025,.012),(.009,.007)]:
  for j in range(8):
   t=j*math.tau/8;vs.append(tuple(c+n*height+rad*(math.cos(t)*u+math.sin(t)*v)))
 for k in range(2):
  for j in range(8):fs.append((k*8+j,k*8+(j+1)%8,(k+1)*8+(j+1)%8,(k+1)*8+j))
 fs.append(tuple(range(16,24)))
 add('B7-fasteners',vs,fs)
bmm.free()
s=mesh_from('SegmentHero',BMV,BMF);s.data['smooth_hardware_faces']=SMOOTH_FACES
LOG['body_feature_tris']=PARTS;LOG['body_traces']=TRACE
LOG['refines'].append({'id':'R7-F8-machined-panels','source':'R2 radius map; vertices raycast from S0-3 corrected clay','feature_tris':PARTS})
LOG['refines'].append({'id':'R16-module-notch-brackets-fasteners','method':'diagonal traced side-window corner; wider raised brackets; eight-sided round bolt heads; two hidden underside fasteners removed to fund visible forms'})
print('BODY_PARTS',PARTS,'TOTAL',tris(s),flush=True)
assert tris(s)+120 <=1450, ('F8_STOP_BUDGET',tris(s)+120)
