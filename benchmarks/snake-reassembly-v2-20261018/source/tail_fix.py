"""Clay-derived repaired tail with fitted/cut-in T5 grilles; S0-4 precedes repair."""
d=np.load(os.path.join(WORK,'tail-volume.npz'));me=bpy.data.meshes.new('tail-repaired-clay');me.from_pydata(d['v'].tolist(),[],d['f'][:,::-1].tolist());me.update();t.data=me
bpy.context.view_layer.objects.active=t;m=t.modifiers.new('tail surface reduction','DECIMATE');m.ratio=1450/tris(t);m.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=m.name)
m=t.modifiers.new('tail voxel smoothing','SMOOTH');m.factor=.2;m.iterations=2;bpy.ops.object.modifier_apply(modifier=m.name)
# R31: refine the existing torpedo shoulder and blunt tip, preserving fins and apertures.
V=verts(t);rad=np.hypot(V[:,1],V[:,2]);w=bump(V[:,0]+.70,.42)*(rad<.22)
V[:,1]*=1+.06*w;V[:,2]*=1+.06*w
setv(t,V)
LOG['refines'].append({'id':'R31-P8-tail-shoulder','method':'local radial refinement of existing terminal vertices; fin envelope excluded'})
bm=bmesh.new();bm.from_mesh(t.data);tbvh=BVHTree.FromBMesh(bm);tailparts=[]
for axis,side,x0,x1,v0,v1 in [(1,-1,-1.12,-.86,-.08,.035),(1,1,-1.12,-.86,-.08,.035),(2,1,-.82,-.48,-.10,.10)]:
 n=Vector((0,side,0) if axis==1 else (0,0,side));q2=Vector((0,0,1) if axis==1 else (0,1,0))
 def hit(x,z):
  q=Vector((x,0,0))+q2*z;r=tbvh.ray_cast(q+n*2,-n)
  if r[0] is None:raise RuntimeError(('tail vent miss',axis,x,z))
  return r[0]
 poly=[hit(x0,v0),hit(x1,v0),hit(x1,v1),hit(x0,v1)];vs=[q+n*.06 for q in poly]+[q-n*.04 for q in poly];fs=[(3,2,1,0),(4,5,6,7)]+[(i,(i+1)%4,(i+1)%4+4,i+4) for i in range(4)]
 cut=mesh_from('T5-vent-cut',vs,fs);bb=bmesh.new();bb.from_mesh(cut.data);bmesh.ops.recalc_face_normals(bb,faces=bb.faces);bb.to_mesh(cut.data);bb.free()
 bpy.context.view_layer.objects.active=t;m=t.modifiers.new('T5 recessed vent','BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=cut;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(cut)
 # border stays on actual surface points; four slats are raised above the recess floor.
 vs=[];fs=[]
 slat_count=7 if axis==2 else 5
 for j in range(slat_count):
  x=x0+(j+1)/(slat_count+1)*(x1-x0);a=hit(x,v0+.008)-n*.012;b=hit(x,v1-.008)-n*.012;u=Vector((.006,0,0));k=len(vs)
  vs +=[a-u,a+u,b+u,b-u,a-u-n*.012,a+u-n*.012,b+u-n*.012,b-u-n*.012]
  fs +=[(k,k+1,k+2,k+3),(k,k+3,k+7,k+4)]
 tailparts.append(mesh_from('T5-fitted-slats',vs,fs))
# R33: cut plate boundaries into the existing torpedo shell with flared seam walls.
for path in [[(-1.22,-.055),(-1.05,-.07),(-.91,-.075)],[(-1.22,.055),(-1.05,.07),(-.91,.075)],[(-1.04,-.10),(-1.04,0),(-1.04,.10)],[(-.43,-.13),(-.43,0),(-.43,.13)]]:
 pts=[]
 for a,b in zip(path[:-1],path[1:]):
  for u in np.linspace(0,1,8,endpoint=False):
   x,y=np.array(a)*(1-u)+np.array(b)*u;hit=tbvh.ray_cast(Vector((x,y,2)),Vector((0,0,-1)))
   if hit[0] is not None:pts.append(hit[0])
 if len(pts)<3:continue
 vs=[];fs=[];normal=Vector((0,0,1))
 for i,q in enumerate(pts):
  tan=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized();ac=normal.cross(tan).normalized()*.005
  vs.extend([q-ac+normal*.02,q+ac+normal*.02,q+ac*.35-normal*.012,q-ac*.35-normal*.012])
 for i in range(len(pts)-1):
  for j in range(4):fs.append((i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j))
 fs.extend([(3,2,1,0),tuple(range(len(vs)-4,len(vs)))])
 cut=mesh_from('T2 plate seam cutter',vs,fs);bb=bmesh.new();bb.from_mesh(cut.data);bmesh.ops.recalc_face_normals(bb,faces=bb.faces);bb.to_mesh(cut.data);bb.free()
 bpy.context.view_layer.objects.active=t;mod=t.modifiers.new('T2 formed plate boundary','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut)
LOG['refines'].append({'id':'R33-P8-terminal-plate-seams','method':'surface-raycast flared seams cut into existing formed terminal'})
# Cut the nozzle into the existing blunt clay nose, along its axis.
nh=tbvh.ray_cast(Vector((-3,0,0)),Vector((1,0,0)))
if nh[0] is not None:
 q=nh[0];bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=.027,depth=.12,location=q+Vector((.025,0,0)),rotation=(0,math.pi/2,0));c=bpy.context.object
 bpy.context.view_layer.objects.active=t;m=t.modifiers.new('T2 inset nose nozzle','BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=c;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(c)
LOG['refines'].append({'id':'R19-tail-nozzle-and-upper-slats','method':'nozzle bored into formed nose; upper vent seven modeled slats, side vents five each'})
bm.free();nt=sum(tris(o) for o in tailparts);cap=1860-nt
if tris(t)>cap:
 bpy.context.view_layer.objects.active=t;m=t.modifiers.new('tail budget','DECIMATE');m.ratio=(cap-4)/tris(t);m.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=m.name)
t=join([t]+tailparts,'TailTip')
LOG['refines'].append({'id':'R13-tail-surface-and-vents','method':'surface-derived volume repair; three recessed T5 vents with 5 actual slats each','vent_depth':.04,'tail_tip_tris':tris(t)})
