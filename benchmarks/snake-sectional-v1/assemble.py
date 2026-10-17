import bpy,math,os,json,random
from mathutils import Vector,Matrix
from math import sin,cos,pi
D='C:/Users/Moore/assembly-sol-op-20261017';O=D+'/delivery';bpy.ops.wm.open_mainfile(filepath=O+'/sections.blend');sc=bpy.context.scene
head=bpy.data.objects['head_budgeted'];body=bpy.data.objects['segment2_budgeted'];tail=bpy.data.objects['tail_budgeted']
assets=[]
def material(n,c,metal=.7,rough=.4,em=0):
 m=bpy.data.materials.new(n);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*c,1);b.inputs['Metallic'].default_value=metal;b.inputs['Roughness'].default_value=rough
 if em:b.inputs['Emission Color'].default_value=(*c,1);b.inputs['Emission Strength'].default_value=em
 return m
dark=material('Recessed graphite housings',(.035,.045,.047),.85,.42);silver=material('Worn machined rims',(.31,.34,.35),.88,.32);teal=material('Teal joint emitters',(.015,.75,.57),.35,.25,3);black=material('Aperture carbon',(.008,.014,.017),.5,.36);glass=material('Optical coated cover',(.025,.16,.13),.55,.14);glass.node_tree.nodes.get('Principled BSDF').inputs['Transmission Weight'].default_value=.45

def mesh(n,vs,fs,mat):
 me=bpy.data.meshes.new(n);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(n,me);bpy.context.collection.objects.link(o);o.data.materials.append(mat);return o

def annulus(n,r1,r2,depth,mat,N=32,axis='X',start=0,end=2*pi):
 vs=[];fs=[]
 for t in [-depth/2,depth/2]:
  for r in [r1,r2]:
   for i in range(N+1):
    a=start+(end-start)*i/N;p=(t,r*cos(a),r*sin(a));vs.append(p if axis=='X' else (r*cos(a),t,r*sin(a)))
 k=N+1
 for i in range(N):
  for a,b,c,d in [(i,i+1,k+i+1,k+i),(2*k+i,3*k+i,3*k+i+1,2*k+i+1),(i,2*k+i,2*k+i+1,i+1),(k+i,k+i+1,3*k+i+1,3*k+i)]:fs.append((a,b,c,d))
 if end-start<2*pi-.01:fs.extend([(0,k,3*k,2*k),(N,2*k+N,3*k+N,k+N)])
 return mesh(n,vs,fs,mat)

def join(obs,n):
 bpy.ops.object.select_all(action='DESELECT')
 for o in obs:o.select_set(True)
 bpy.context.view_layer.objects.active=obs[0];bpy.ops.object.join();o=obs[0];o.name=n;return o

def make_joint():
 housing=annulus('Housing',.425,.51,.095,dark,24);parts=[]
 for i in range(12):parts.append(annulus('Emissive bar',.505,.52,.052,teal,1,start=2*pi*i/12+.045,end=2*pi*(i+1)/12-.045))
 return housing,join(parts,'Joint segmented teal inserts')
housing,bars=make_joint();housing.data.name='Joint dark annular housing';bars.data.name='12 separated emissive bars'
# Add economical machined hex fasteners to module: four bolts, 80 triangles.
parts=[body]
for sy in [-1,1]:
 for x in [-.17,.15]:
  bpy.ops.mesh.primitive_cylinder_add(vertices=6,radius=.028,depth=.018,location=(x,sy*.455,.14),rotation=(pi/2,0,0));o=bpy.context.object;o.data.materials.append(silver);parts.append(o)
body=join(parts,'Segment_Module');body.data.name='Hero segment shared mesh'
# Camera-lens assemblies seated in the existing circular head formations.
eyeobs=[]
for sy in [-1,1]:
 center=Vector((-.94,sy*.395,.065))
 for j,(a,b,d,mat,off) in enumerate([(.165,.215,.065,dark,0),(.155,.185,.045,silver,.038),(.125,.153,.035,black,.062),(.108,.125,.018,teal,.072),(.055,.108,.014,dark,.079),(.025,.055,.014,teal,.086)]):
  o=annulus('Lens_%s_ring_%d'%(sy,j),a,b,d,mat,48,axis='Y');o.location=center+Vector((0,sy*off,0));eyeobs.append(o)
 # Eight actual overlapping aperture vanes.
 for i in range(8):
  a=i*2*pi/8;vs=[]
  for r,t in [(.105,a),(.10,a+.58),(.032,a+.88),(.04,a+.27)]:vs.append((center.x+r*cos(t),center.y+sy*.088,center.z+r*sin(t)))
  o=mesh('Aperture blade',vs,[(0,1,2,3)],silver if i%2 else black);eyeobs.append(o)
 bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=12,radius=1,location=center+Vector((0,sy*.09,0)));o=bpy.context.object;o.name='Curved optical cover';o.scale=(.106,.023,.106);o.data.materials.append(glass);eyeobs.append(o)
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=8,radius=.026,location=center+Vector((0,sy*.108,0)));o=bpy.context.object;o.name='Lens emissive core';o.scale.y=.3;o.data.materials.append(teal);eyeobs.append(o)
for o in eyeobs:o.parent=head
head.name='Head';tail.name='Tail'
# Master spline, sampled at equal arc lengths for all 28 rigid nodes.
controls=[(-1.55,.25,3.85),(-.25,.25,3.82),(.45,.25,3.25),(.37,.22,2.35),(-.35,.15,1.25),(-1.4,-.15,.56),(-2.45,-.8,.56),(-2.35,-1.9,.56),(-.95,-2.55,.56),(.8,-2.5,.56),(2.12,-1.65,.56),(2.3,-.2,.56),(1.35,.95,.56),(-.15,1.15,.56),(-1.35,.85,.56),(-1.45,1.95,.56),(.0,2.28,.56),(1.85,2.10,.56),(3.2,1.2,.56),(3.8,-.2,.54),(3.75,-1.45,.48)]
controls=[Vector(p) for p in controls]
pts=[]
for i in range(len(controls)-1):
 p0=controls[max(i-1,0)];p1=controls[i];p2=controls[i+1];p3=controls[min(i+2,len(controls)-1)]
 for j in range(80):
  t=j/80;pts.append((2*p1+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t)*.5)
pts.append(controls[-1]);dist=[0]
for a,b in zip(pts,pts[1:]):dist.append(dist[-1]+(b-a).length)
L=dist[-1];pitch=L/28
print('PATH_LENGTH',L,'PITCH',pitch,flush=True)
import bisect
def sample(d):
 d=max(0,min(L,d));i=max(0,min(len(pts)-2,bisect.bisect_right(dist,d)-1));t=(d-dist[i])/max(1e-6,dist[i+1]-dist[i]);return pts[i].lerp(pts[i+1],t)
def frame(d):
 x=(sample(d+.03)-sample(d-.03)).normalized();up=Vector((0,0,1));y=up.cross(x).normalized();z=x.cross(y).normalized();return Matrix((x,y,z)).transposed().to_4x4()
head.location=sample(0);head.rotation_euler=frame(0).to_euler();assets=[head,tail]+eyeobs
# Bake module length into mesh rather than introducing nonunit scales.
for v in body.data.vertices:v.co.x*=pitch/.76
for i in range(28):
 o=body if i==0 else bpy.data.objects.new('Segment_%02d'%i,body.data)
 if i:bpy.context.collection.objects.link(o)
 o.name='Segment_%02d'%i;o.matrix_world=frame((i+.5)*pitch);o.location=sample((i+.5)*pitch);assets.append(o)
 for proto,label in [(housing,'Housing'),(bars,'GlowBars')]:
  r=proto.copy();r.data=proto.data;bpy.context.collection.objects.link(r);r.name='Joint_%02d_%s'%(i,label);r.parent=o;r.location=(-pitch/2,0,0);r.rotation_euler=(0,0,0);assets.append(r)
tail.matrix_world=frame(L);tail.location=sample(L)
for proto,label in [(housing,'Housing'),(bars,'GlowBars')]:
 r=proto.copy();r.data=proto.data;bpy.context.collection.objects.link(r);r.name='TailJoint_'+label;r.parent=tail;r.location=(0,0,0);assets.append(r)
for o in [housing,bars]:bpy.data.objects.remove(o,do_unlink=True)
# Master curve retained in .blend, never exported as geometry.
cu=bpy.data.curves.new('Master curve','CURVE');cu.dimensions='3D';sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
for p,v in zip(sp.points,pts):p.co=(*v,1)
co=bpy.data.objects.new('MasterCurve',cu);bpy.context.collection.objects.link(co)
json.dump({'points':[list(p) for p in pts[::8]]+[list(pts[-1])],'length':L,'pitch':pitch,'count':28},open(O+'/path.json','w'),indent=2)
# Explicit triangulation and UVs for every insert / lens primitive.
for o in assets:
 if o.type!='MESH':continue
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 if not o.data.uv_layers:
  bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.02);bpy.ops.object.mode_set(mode='OBJECT')
 if not any(m.type=='TRIANGULATE' for m in o.modifiers):o.modifiers.new('Delivery triangulation','TRIANGULATE')
# Plain neutral staging; no floor, environment geometry, or labels.
sc.render.engine='CYCLES';sc.cycles.samples=32;sc.cycles.use_denoising=True
sc.world.use_nodes=True;sc.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.22,.22,.22,1);sc.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.6
sc.view_settings.view_transform='AgX';sc.render.resolution_x=1920;sc.render.resolution_y=1080;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG'
def area(n,p,power,size,color):
 bpy.ops.object.light_add(type='AREA',location=p);o=bpy.context.object;o.name=n;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.data.color=color;o.rotation_euler=(Vector((0,0,1.5))-o.location).to_track_quat('-Z','Y').to_euler()
area('Large neutral key',(-4,-6,9),1600,6,(1,.96,.91));area('Soft fill',(5,-2,6),1100,5,(.85,.93,1));area('Rim',(1,5,8),1900,5,(1,1,1))
bpy.ops.object.camera_add();cam=bpy.context.object;sc.camera=cam;cam.data.type='ORTHO'
def shot(n,loc,target,scale):
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;sc.render.filepath=O+'/captures/'+n+'.png';bpy.ops.render.render(write_still=True)
# Exports: rigid body nodes and separate attached inserts, no skins/compression.
def export(path,obs):
 bpy.ops.object.select_all(action='DESELECT')
 for o in obs:o.select_set(True)
 bpy.ops.export_scene.gltf(filepath=path,export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_texcoords=True,export_normals=True,export_tangents=True,export_draco_mesh_compression_enable=False,export_materials='EXPORT')
export(O+'/snake-sectional.glb',assets);export(O+'/head.glb',[head]+eyeobs)
# Count evaluated assembled instances, not unique mesh datablocks.
dg=bpy.context.evaluated_depsgraph_get();counts={}
for o in assets:
 me=o.evaluated_get(dg).to_mesh();me.calc_loop_triangles();counts[o.name]=len(me.loop_triangles);o.evaluated_get(dg).to_mesh_clear()
json.dump({'objects':counts,'total':sum(counts.values()),'head':sum(counts[o.name] for o in [head]+eyeobs),'segment':counts['Segment_00'],'joint':counts['Joint_00_Housing']+counts['Joint_00_GlowBars'],'tail':counts['Tail']},open(O+'/counts.json','w'),indent=2)
shot('wip-full-body',(-7,-12,7),(0.5,0,1.9),9.2);shot('wip-head',(-4,-7,5.2),(-2.2,.25,4.0),3.6)
cam.location=(-7,-12,7);cam.rotation_euler=(Vector((.5,0,1.9))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=9.2
bpy.ops.wm.save_as_mainfile(filepath=O+'/snake-sectional.blend');print('ASSEMBLY_READY',counts,flush=True)
