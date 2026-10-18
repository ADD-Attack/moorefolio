"""R8-R13: repair the actual formed clay; incise, never loft/rebuild the head.
Requires head-volume.npz generated from the R1-R5 master by repair_volume.py.
"""
from mathutils.geometry import convex_hull_2d
CACHE=os.path.join(WORK,'head-reduced.npz')
if os.path.exists(CACHE):
 D=np.load(CACHE);me=bpy.data.meshes.new('reduced-formed-clay');me.from_pydata(D['v'].tolist(),[],D['f'].tolist());me.update();h.data=me
else:
 D=np.load(os.path.join(WORK,'head-volume.npz')); me=bpy.data.meshes.new('repaired-clay-head');me.from_pydata(D['v'].tolist(),[],D['f'][:,::-1].tolist());me.update();h.data=me
 # Move only existing fin vertices, with a blend into their original roots.
 V=verts(h);P=np.array([Mh.inverted()@Vector(v) for v in V]);w=np.clip((P[:,2]-.735)/.06,0,1)
 fin=(P[:,0]>-.55)&(P[:,0]<-.12);w*=fin
 cent=np.where(P[:,1]<-.08,-.19,np.where(P[:,1]>.08,.185,-.004))
 P[:,0]-=.28*cent*w
 P[:,1]+=(.22*(P[:,1]-cent)+np.sign(cent)*.022)*w
 V=np.array([Mh@Vector(p) for p in P]);setv(h,V)
 bpy.context.view_layer.objects.active=h
 m=h.modifiers.new('reduce repaired clay','DECIMATE');m.ratio=9100/tris(h);m.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=m.name)
 m=h.modifiers.new('remove voxel stair steps','SMOOTH');m.factor=.28;m.iterations=2;bpy.ops.object.modifier_apply(modifier=m.name)
 h.data.calc_loop_triangles();np.savez(os.path.join(WORK,'head-reduced.npz'),v=verts(h),f=np.array([q.vertices[:] for q in h.data.loop_triangles]))
LOG['refines'].append({'id':'R8-shell-repair','source':'R1-R5 actual master triangles','method':'.006 surface voxelization; one-cell gap close; fill enclosed sections; outer isosurface; collapse; 2 mild smoothing iterations','not_a_primitive':True})
LOG['refines'].append({'id':'R9-fin-separation','region':'clay z>.735, x between -.55 and -.12','axial_stagger':'.28 * lateral centre, smooth root blend','thickness_scale':1.22,'lateral_spread':.022})
# Flatten the existing machined blade faces locally; retain their formed x/z outlines and blended roots.
V=verts(h);P=np.array([Mh.inverted()@Vector(v) for v in V]);w=np.clip((P[:,2]-.77)/.04,0,1)*((P[:,0]>-.60)&(P[:,0]<-.10))
cent=np.where(P[:,1]<-.08,-.212,np.where(P[:,1]>.08,.207,-.004));target=cent+np.where(P[:,1]<cent,-.015,.015)
w*=.65;P[:,1]=P[:,1]*(1-w)+target*w;setv(h,np.array([Mh@Vector(p) for p in P]))
# Frozen BVH of repaired shell for fitting cuts and machined hardware.
bm=bmesh.new();bm.from_mesh(h.data);hbvh=BVHTree.FromBMesh(bm);EXTRA=[]
def pform(p):
 p=Vector(p)
 if p.x<X0:p.x=X0+(p.x-X0)*K_SN
 return Mh@p

def surface(x,z,side=-1):
 # Given raw clay x,z, locate the actual outer clay surface on the relevant flank.
 q=pform((x,0,z));hit=hbvh.ray_cast(q+Vector((0,-side*3,0)),Vector((0,side,0)))
 if hit[0] is None:raise RuntimeError(('head surface miss',x,z,side))
 return hit[0],Vector((0,-side,0))
def cut_mesh(vs,fs,name):
 before_n=tris(h)
 cutter=mesh_from(name,vs,fs)
 b=bmesh.new();b.from_mesh(cutter.data);bmesh.ops.recalc_face_normals(b,faces=b.faces);b.to_mesh(cutter.data);b.free()
 bpy.context.view_layer.objects.active=h
 mod=h.modifiers.new(name,'BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
 bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter)
 print('CUT',name,before_n,tris(h),flush=True)
 assert tris(h)>.5*before_n,('REJECT destructive boolean',name,before_n,tris(h))
def groove(path,width=.004,depth=.008,side=-1,name='panel-seam'):
 dense=[]
 for a,b in zip(path[:-1],path[1:]):
  for u in np.linspace(0,1,max(2,int(np.linalg.norm(np.array(b)-a)/.016)),endpoint=False):dense.append(tuple(np.array(a)*(1-u)+np.array(b)*u))
 dense.append(path[-1]);path=dense
 pts=[];ns=[]
 for x,z in path:
  q,n=surface(x,z,side);pts.append(q);ns.append(n)
 vs=[];fs=[]
 for i,(q,n) in enumerate(zip(pts,ns)):
  tangent=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized();ac=n.cross(tangent).normalized()*width*S_HEAD/2
  vs.extend([q-ac+n*.008,q+ac+n*.008,q+ac-n*depth*S_HEAD,q-ac-n*depth*S_HEAD])
 for i in range(len(pts)-1):
  for j in range(4):fs.append((i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j))
 fs +=[(3,2,1,0),tuple(range(len(vs)-4,len(vs)))]
 cut_mesh(vs,fs,name)

def inset(poly,depth,side,name):
 pts=[surface(x,z,side)[0] for x,z in poly];n=Vector((0,-side,0));N=len(pts)
 vs=[p+n*.04 for p in pts]+[p-n*depth*S_HEAD for p in pts]
 fs=[tuple(range(N-1,-1,-1)),tuple(range(N,2*N))]+[(i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N)]
 cut_mesh(vs,fs,name)

def rod(name,a,b,r,n=8):
 d=b-a;M=Matrix.Translation(a)@d.to_track_quat('Z','Y').to_matrix().to_4x4()
 vs,fs=lathe_ring([(r,0),(r,d.length)],n,M);fs +=[tuple(range(0,2*n,2)),tuple(range(1,2*n,2))]
 EXTRA.append(mesh_from(name,vs,fs))

# Paths traced along the surviving clay plate boundaries (raw clay coordinate convention).
paths=[ [(-.97,.39),(-.90,.42),(-.84,.47)],
 [(-.86,.49),(-.82,.57),(-.75,.61)],
 [(-.78,.62),(-.70,.65),(-.60,.65),(-.53,.61)],
 [(-.86,.39),(-.82,.34),(-.80,.29)],
 [(-.73,.38),(-.70,.33),(-.68,.285)],
 [(-.59,.40),(-.57,.345),(-.54,.30)],
 [(-.47,.40),(-.45,.345),(-.43,.29)],
 [(-.49,.61),(-.43,.66),(-.35,.685)],
 [(-.41,.69),(-.40,.62),(-.37,.59)],
 [(-.13,.64),(-.10,.60),(-.09,.55)],
 [(-.85,.23),(-.84,.28)], [(-.67,.225),(-.65,.28)], [(-.48,.23),(-.47,.29)] ]
for side in [-1,1]:
 for i,p in enumerate(paths):groove(p,side=side,name='H2-cut-%s-%d'%(side,i))
 groove([(-.958,.295),(-.93,.28),(-.84,.278),(-.74,.286),(-.62,.30),(-.50,.315),(-.39,.33)],.009,.021,side,'H3-mouth-volume')
 inset([(-.962,.385),(-.935,.407),(-.904,.415),(-.902,.401),(-.93,.38),(-.956,.371)],.022,side,'H4-nostril-recess')
 inset([(-.375,.63),(-.24,.63),(-.24,.67),(-.375,.67)],.012,side,'H9-upper-inset')
 inset([(-.35,.30),(-.21,.31),(-.21,.345),(-.35,.335)],.013,side,'H9-lower-inset')
 inset([(-.405,.426),(-.255,.426),(-.255,.54),(-.405,.54)],.026,side,'H7-vent-recess')
 for x in np.linspace(-.395,-.265,7):
  a,n=surface(x,.434,side);b,_=surface(x,.533,side);a-=n*.012;b-=n*.012;rod('H7-vertical-slat',a,b,.0035*S_HEAD,4)
 for z in [.40,.51]:
  a,n=surface(-.18,z,side);b,_=surface(.04,z,side);a+=n*.01;b+=n*.01
  rod('H8-piston-barrel',a,a+(b-a)*.58,.025*S_HEAD,12);rod('H8-piston-rod',a+(b-a)*.58,b,.014*S_HEAD,12)
LOG['refines'].append({'id':'R10-cut-in-head-detail','H2_paths_raw_clay':paths,'H3_mouth_depth_clay':.021,'H4_nostril_depth_clay':.022,'H9_inset_depth_clay':.012,'H7_slats_per_side':7,'H8':'two fitted barrel/rod units per flank'})
# Cut an inset into each EXISTING planarized blade face; its original perimeter becomes the raised border.
P=np.array([Mh.inverted()@v.co for v in h.data.vertices])
for k,(lo,hi,cy) in enumerate([(-1,-.08,-.212),(-.08,.08,-.004),(.08,1,.207)]):
 q=P[(P[:,1]>lo)&(P[:,1]<hi)&(P[:,2]>.785)&(P[:,0]>-.60)&(P[:,0]<-.10)]
 if not len(q):continue
 hull=convex_hull_2d([Vector((p[0],p[2])) for p in q]);outline=q[hull][:,[0,2]];centre=outline.mean(0);inner=centre+(outline-centre)*.79
 for side in [-1,1]:
  N=len(inner);vs=[Mh@Vector((p[0],cy+side*y,p[1])) for y in [.032,.007] for p in inner]
  fs=[tuple(range(N-1,-1,-1)),tuple(range(N,2*N))]+[(i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N)]
  cut_mesh(vs,fs,'H5-inset-existing-blade')
LOG['refines'].append({'id':'R11-fin-borders','method':'local planar refinement of existing blade faces, preserved formed x/z silhouette; inset face cut leaves perimeter as raised border'})
# Forehead plate seams follow the actual top surface with dense samples, never an added cap.
def topgroove(path):
 dense=[]
 for a,b in zip(path[:-1],path[1:]):
  for u in np.linspace(0,1,max(2,int(np.linalg.norm(np.array(b)-a)/.014)),endpoint=False):dense.append(tuple(np.array(a)*(1-u)+np.array(b)*u))
 dense.append(path[-1]);pts=[];n=Vector((0,0,1))
 for x,y in dense:
  q=pform((x,y,0));hit=hbvh.ray_cast(Vector((q.x,q.y,3)),Vector((0,0,-1)))
  if hit[0] is None:raise RuntimeError(('forehead seam miss',x,y))
  pts.append(hit[0])
 vs=[];fs=[]
 for i,q in enumerate(pts):
  tangent=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized();ac=n.cross(tangent).normalized()*.002*S_HEAD
  vs.extend([q-ac+n*.012,q+ac+n*.012,q+ac-n*.012*S_HEAD,q-ac-n*.012*S_HEAD])
 for i in range(len(pts)-1):
  for j in range(4):fs.append((i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j))
 fs +=[(3,2,1,0),tuple(range(len(vs)-4,len(vs)))];cut_mesh(vs,fs,'H2-forehead-seam')
for side in [-1,1]:topgroove([(-.95,side*.04),(-.86,side*.06),(-.72,side*.08),(-.55,side*.10)])
for x,half in [(-.89,.10),(-.77,.15),(-.55,.19)]:topgroove([(x,-half),(x,0),(x,half)])
bm.free()
# Protect hardware separately; only collapse repaired clay if Boolean cuts exceed its allocation.
extra_tris=sum(tris(o) for o in EXTRA);cap=14000-1104-extra_tris
if tris(h)>cap:
 bpy.context.view_layer.objects.active=h;m=h.modifiers.new('head surface budget','DECIMATE');m.ratio=(cap-16)/tris(h);m.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=m.name)
LOG['head_repaired_surface_tris']=tris(h);LOG['head_fitted_hardware_tris']=extra_tris
h=join([h]+EXTRA,'HEAD_repaired')
