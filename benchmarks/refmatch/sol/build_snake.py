"""Reference-match mechanical serpent. Blender 4.5, deterministic mesh authoring.
Run blender -b --factory-startup --python build_snake.py. Textures beside script.
Geometry authored +X, converted to -Y before export. Rigid segment joint origins.
"""
import bpy, math, os, random, json
from mathutils import Vector, Matrix
from math import sin,cos,pi
ROOT=os.path.dirname(os.path.abspath(__file__))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
random.seed(417)
def material(name,color,metal=.8,rough=.4,tex=None,emit=False):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.use_backface_culling=True
 n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 if tex:
  for suffix,space in [('albedo','sRGB'),('normal','Non-Color'),('orm','Non-Color')]:
   t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(os.path.join(ROOT,'textures',tex+'_'+suffix+'.png'));t.image.colorspace_settings.name=space
   if suffix=='albedo':l.new(t.outputs['Color'],p.inputs['Base Color'])
   elif suffix=='normal':
    nm=n.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.55;l.new(t.outputs['Color'],nm.inputs['Color']);l.new(nm.outputs['Normal'],p.inputs['Normal'])
   else:
    sep=n.new('ShaderNodeSeparateColor');l.new(t.outputs['Color'],sep.inputs[0]);l.new(sep.outputs['Green'],p.inputs['Roughness']);l.new(sep.outputs['Blue'],p.inputs['Metallic'])
    group=bpy.data.node_groups.get('glTF Material Output')
    if not group:
     group=bpy.data.node_groups.new('glTF Material Output','ShaderNodeTree');group.interface.new_socket(name='Occlusion',in_out='INPUT',socket_type='NodeSocketFloat')
    gn=n.new('ShaderNodeGroup');gn.node_tree=group;l.new(sep.outputs['Red'],gn.inputs['Occlusion'])
 if emit:
  t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(os.path.join(ROOT,'textures','cyan_emission.png'));l.new(t.outputs['Color'],p.inputs['Emission Color']);p.inputs['Emission Color'].default_value=(1,1,1,1);p.inputs['Emission Strength'].default_value=3.5
 return m
M=[material('Head_Worn_Gunmetal',(.3,.32,.33),tex='head'),material('Body_Worn_Gunmetal',(.3,.32,.33),tex='body'),material('Recess_Blackened_Steel',(.018,.023,.025),.85,.53),material('Edge_Exposed_Alloy',(.42,.46,.47),.95,.28),material('Cyan_Emitter',(.006,.09,.065),.15,.25,emit=True),material('Optical_Black_Glass',(.008,.029,.032),.7,.09),material('Fastener_Titanium',(.20,.23,.23),.95,.32),material('Woven_Steel_Vent_Mesh',(.08,.09,.09),tex='grille')]
# A curved optical cover, in front of the modeled iris. Standard glTF alpha.
glass=material('Optical_Lens_Cover',(.018,.08,.065),.25,.065)
glass.node_tree.nodes.get('Principled BSDF').inputs['Alpha'].default_value=.18
glass.surface_render_method='DITHERED';glass.use_backface_culling=False
M.append(glass)
crest_mat=material('Crest_Worn_Gunmetal',(.3,.32,.33),tex='head')
crest_p=crest_mat.node_tree.nodes.get('Principled BSDF')
for link in list(crest_p.inputs['Normal'].links):crest_mat.node_tree.links.remove(link)
M.append(crest_mat)
class Mesh:
 def __init__(self):self.v=[];self.f=[];self.mi=[];self.uv=[];self.smooth=[]
 def face(self,pts,mat=0,uv=None,smooth=False):
  k=len(self.v);self.v.extend([tuple(p) for p in pts]);self.f.append(tuple(range(k,k+len(pts))));self.mi.append(mat);self.smooth.append(smooth)
  if uv is None:uv=[(.03,.03),(.22,.03),(.22,.22),(.03,.22)][:len(pts)] if len(pts)<=4 else [( .12+.09*cos(i*2*pi/len(pts)),.12+.09*sin(i*2*pi/len(pts))) for i in range(len(pts))]
  self.uv.extend(uv)
 def quad(self,a,b,c,d,mat=0,uv=None,smooth=False):self.face([a,b,c,d],mat,uv,smooth)
 def object(self,name):
  me=bpy.data.meshes.new(name);me.from_pydata(self.v,[],self.f);me.update()
  for m in M:me.materials.append(m)
  for p,mi,sm in zip(me.polygons,self.mi,self.smooth):p.material_index=mi;p.use_smooth=sm
  uv=me.uv_layers.new(name='UVMap')
  for loop in me.loops:uv.data[loop.index].uv=self.uv[loop.vertex_index]
  ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob)
  # Weld per-component duplicate face vertices, preserving sharp split normals.
  bpy.context.view_layer.objects.active=ob;ob.select_set(True);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.remove_doubles(threshold=.00001);bpy.ops.mesh.normals_make_consistent(inside=False);bpy.ops.object.mode_set(mode='OBJECT');ob.select_set(False)
  return ob

def basis(normal):
 n=Vector(normal).normalized();u=n.cross(Vector((0,0,1)))
 if u.length<.1:u=n.cross(Vector((0,1,0)))
 u.normalize();return u,n.cross(u).normalized(),n

def cyl(b,pos,radius,length,normal=(1,0,0),mat=2,n=12,r2=None):
 u,v,w=basis(normal);p=Vector(pos);r2=radius if r2 is None else r2
 rings=[[p+w*z+(u*cos(2*pi*i/n)+v*sin(2*pi*i/n))*r for i in range(n)] for z,r in [(-length/2,radius),(length/2,r2)]]
 for i in range(n):j=(i+1)%n;b.quad(rings[0][i],rings[0][j],rings[1][j],rings[1][i],mat,smooth=True)
 for row,rev in [(rings[0],True),(rings[1],False)]:
  for i in range(n):j=(i+1)%n;b.face([p+w*(-length/2 if rev else length/2),row[j if rev else i],row[i if rev else j]],mat)

def annulus(b,pos,ri,ro,width,normal=(1,0,0),mat=2,n=48,segments=False):
 u,v,w=basis(normal);p=Vector(pos)
 for i in range(n):
  a=2*pi*(i+(.08 if segments else 0))/n;c=2*pi*(i+1-(.08 if segments else 0))/n
  pts=[p+w*z+(u*cos(t)+v*sin(t))*r for z,r,t in [(-width/2,ri,a),(-width/2,ri,c),(-width/2,ro,c),(-width/2,ro,a),(width/2,ri,a),(width/2,ri,c),(width/2,ro,c),(width/2,ro,a)]]
  for inds in [(0,1,2,3),(4,7,6,5),(0,4,5,1),(3,2,6,7)]+([(0,3,7,4),(1,5,6,2)] if segments else []):b.face([pts[k] for k in inds],mat,smooth=not segments)

def box(b,pos,size,mat=2,axes=None):
 p=Vector(pos);u,v,w=axes or (Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
 pts=[p+u*x*size[0]/2+v*y*size[1]/2+w*z*size[2]/2 for x,y,z in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
 for f in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:b.face([pts[i] for i in f],mat)

def bolt(b,p,normal=(0,0,1),r=.027):
 # Closed hexagonal socket screw. The aperture is actual recessed geometry.
 p=Vector(p);u,v,n=basis(normal)
 rows=[[p+n*z+(u*cos(j*pi/3)+v*sin(j*pi/3))*rad for j in range(6)] for z,rad in [(-.007,r*1.25),(.017,r),(.017,r*.43),(.006,r*.43)]]
 for k in range(3):
  for j in range(6):
   jj=(j+1)%6;b.quad(rows[k][j],rows[k][jj],rows[k+1][jj],rows[k+1][j],6 if k<2 else 2)
 b.face(list(reversed(rows[0])),6);b.face(rows[-1],2)

def plate(b,fn,x0,x1,a0,a1,mat,tile,thick=.043):
 # A curved armor panel, clipped corners, actual thickness and bright bevel.
 uvpoly=([(0,0),(.68,0),(.68,.15),(1,.15),(1,1),(.22,1),(.22,.85),(0,.85)] if mat==1 and tile%2 else [(.08,0),(.92,0),(1,.1),(1,.9),(.92,1),(.08,1),(0,.9),(0,.1)])
 rows=[]
 for inset,offset in [(0,-thick),(0,-.012),(.028,0)]:
  rows.append([Vector(fn(x0+(x1-x0)*(u*(1-2*inset)+inset),a0+(a1-a0)*(v*(1-2*inset)+inset),offset)) for u,v in uvpoly])
 uv=[((tile%4+(u*.90+.05))/4,(tile//4+(v*.90+.05))/4) for u,v in uvpoly]
 # Tessellated top fan, flat-ish plate highlights rather than balloon smoothing.
 center=Vector(fn((x0+x1)/2,(a0+a1)/2,0));uc=((tile%4+.5)/4,(tile//4+.5)/4)
 for i in range(8):
  j=(i+1)%8;b.face([center,rows[2][i],rows[2][j]],mat,[uc,uv[i],uv[j]],True)
  b.quad(rows[1][i],rows[1][j],rows[2][j],rows[2][i],3 if (i+tile)%3==0 else mat,[uv[i],uv[j],uv[j],uv[i]],True)
  b.quad(rows[0][i],rows[0][j],rows[1][j],rows[1][i],mat,[uv[i],uv[j],uv[j],uv[i]],True)
 b.face(list(reversed(rows[0])),2)

def body():
 b=Mesh()
 # Smooth overlapping ball-ended mechanical core conceals openings on bends.
 rr=[(-.60,.25),(-.50,.45),(-.32,.54),(.22,.54),(.46,.48),(.61,.26)]
 for (xx,r),(yy,ss) in zip(rr,rr[1:]):
  for j in range(16):
   a=j*pi/8;c=(j+1)*pi/8;b.quad((xx,r*sin(a),r*cos(a)),(yy,ss*sin(a),ss*cos(a)),(yy,ss*sin(c),ss*cos(c)),(xx,r*sin(c),r*cos(c)),2,smooth=True)
 for xx,r in [rr[0],rr[-1]]:
  b.face([(xx,r*sin(j*pi/8),r*cos(j*pi/8)) for j in range(16)],2)
 for x in [-.40,-.29]:annulus(b,(x,0,0),.55,.635,.035,mat=2,n=16)
 annulus(b,(-.345,0,0),.59,.616,.067,mat=4,n=20,segments=True)
 fn=lambda x,a,o:(x,(.642+o)*sin(a),(.642+o)*cos(a))
 for j in range(8):
  a=j*2*pi/8
  plate(b,fn,-.235,.46,a+.035,a+pi/4-.035,1,(j*5)%16)
  for x,ang in [(.365,a+.66)]:
   pp=Vector(fn(x,ang,.007));nn=Vector((0,sin(ang),cos(ang)));cyl(b,pp,.027,.018,nn,6,6)
   u,v,nn=basis(nn);b.face([pp+nn*.011+(u*cos(k*pi/3)+v*sin(k*pi/3))*.011 for k in range(6)],2)
  # machined recessed grille and raised metal crossbars on alternating panels
  if j in [1,5]:
   mid=a+pi/8;n=Vector((0,sin(mid),cos(mid)));u=Vector((1,0,0));v=Vector((0,cos(mid),-sin(mid)))
   box(b,fn(.10,mid,.008),(.29,.19,.012),7,(u,v,n))
   for k in range(5):box(b,Vector(fn(.10,mid,.017))+u*(k-2)*.048,(.014,.17,.014),6,(u,v,n))
 # Exposed longitudinal pin housings between armor sectors.
 for j in range(2):
  a=pi/2+j*pi;cyl(b,(-.30,.57*sin(a),.57*cos(a)),.065,.24,mat=6,n=8)
 return b.object('Segment')

# Anatomical skull radius/height profiles, muzzle +X. Neck is the joint origin.
PROFILE=[(-.12,.56,.53,.0),(.18,.72,.64,.03),(.62,.79,.69,.04),(1.05,.77,.68,.02),(1.4,.68,.56,-.02),(1.85,.52,.43,-.10),(2.22,.34,.32,-.14),(2.38,.19,.23,-.15)]
def prof(x):
 for i in range(len(PROFILE)-1):
  a,b=PROFILE[i:i+2]
  if x<=b[0]:
   t=max(0,(x-a[0])/(b[0]-a[0]));return tuple(a[k]*(1-t)+b[k]*t for k in range(1,4))
 return PROFILE[-1][1:]
def headfn(x,a,o=0):
 w,h,z=prof(x);return (x,(w+o)*sin(a),(h+o)*cos(a)+z)
def loftskull(b):
 n=36;m=18
 for k in range(m):
  x0=-.12+2.50*k/m;x1=-.12+2.50*(k+1)/m
  for j in range(n):
   a=j*2*pi/n;c=(j+1)*2*pi/n
   b.quad(headfn(x0,a,-.055),headfn(x1,a,-.055),headfn(x1,c,-.055),headfn(x0,c,-.055),2,smooth=True)
 for x in [-.12,2.38]:
  w,h,z=prof(x)
  for j in range(n):b.face([(x,0,z),headfn(x,j*2*pi/n,-.055),headfn(x,(j+1)*2*pi/n,-.055)],2)
def head():
 b=Mesh();loftskull(b)
 # Individual overlapping armored shells, rows staggered with deep seams.
 rows=[(-.08,.46),(.49,1.00),(1.03,1.51),(1.54,1.98),(2.01,2.37)]
 for k,(x0,x1) in enumerate(rows):
  for j in range(10):
   a=j*2*pi/10 + (0.08 if k%2 else 0)
   # Leave genuine hole in visible side armor for the camera socket.
   eye_sector=(k in [1,2] and j in [1,2])
   if eye_sector:continue
   plate(b,headfn,x0,x1,a+.025,a+2*pi/10-.025,0,(k*7+j*3)%16,.052)
   for x,aa in [(x0+.09,a+.11),(x1-.08,a+.51)]:bolt(b,headfn(x,aa,.015),(0,sin(aa),cos(aa)),.026)
 # The snout cap is clad, with a real recessed mouth seam below.
 for j in range(10):
  a=j*2*pi/10
  plate(b,lambda x,aa,o:(2.39+o,x*sin(aa),x*cos(aa)-.15),.025,.205,a+.025,a+2*pi/10-.025,0,(j+2)%16,.025)
 # Jaw articulated-ready lower armor distinct silhouette + hinge pistons.
 for k in range(5):
  x0=.08+k*.44
  plate(b,lambda x,a,o:headfn(x,a,o+.035),x0,x0+.40,pi*.64,pi*1.36,0,(k+9)%16,.065)
 for sign in [-1,1]:
  cyl(b,(.34,sign*.685,-.23),.115,.12,(0,sign,0),6,24)
  annulus(b,(.34,sign*.75,-.23),.066,.09,.02,(0,sign,0),2,n=24)
  # cheek heat exchanger frame and deep vertical louvers.
  p=Vector((.18,sign*.68,.12));u=Vector((1,0,0));v=Vector((0,0,1));n=Vector((0,sign,0))
  box(b,p,(.42,.36,.06),3,(u,v,n));box(b,p+n*.037,(.35,.29,.02),7,(u,v,n))
  for j in range(7):box(b,p+n*.052+u*(j-3)*.046,(.015,.265,.028),6,(u,v,n))
 # ONE visible optical assembly: housing, threaded rings, recessed barrel,
 # six geometric aperture blades, patterned inner iris and small bright core.
 n=Vector((.07,.965,.25)).normalized();p=Vector((1.08,.699,.24));u,v,n=basis(n)
 annulus(b,p,.30,.409,.10,n,0,n=64)
 annulus(b,p+n*.061,.296,.364,.030,n,3,n=64)
 annulus(b,p+n*.071,.278,.298,.018,n,4,n=64,segments=True)
 annulus(b,p+n*.025,.224,.282,.07,n,2,n=64)
 annulus(b,p+n*.015,.195,.231,.02,n,6,n=64)
 cyl(b,p-n*.025,.216,.02,n,5,64)
 for j in range(8):
  a=j*2*pi/8
  pts=[p+n*.001+u*(r*cos(t))+v*(r*sin(t)) for r,t in [(.207,a),(.207,a+.71),(.109,a+.97),(.092,a+.45)]]
  b.face(pts,6,[(.02,.02),(.2,.02),(.2,.2),(.02,.2)])
 for j in range(36):
  a=j*2*pi/36;pp=p+n*.014+(u*cos(a)+v*sin(a))*.164
  box(b,pp,(.012,.022,.005),4,(u*cos(a)+v*sin(a),-u*sin(a)+v*cos(a),n))
 annulus(b,p+n*.005,.085,.108,.012,n,4,n=48)
 cyl(b,p-n*.002,.080,.006,n,4,48)
 for j in range(8):
  a=j*2*pi/8;bolt(b,p+n*.058+(u*cos(a)+v*sin(a))*.382,n,.022)
 # Separate armored orbital wedges around the lens; the center stays physically open.
 for j in range(8):
  aa=j*pi/4+.025;cc=(j+1)*pi/4-.025
  def orbitfn(rad,ang,off):return p+n*(off-.016)+(u*cos(ang)+v*sin(ang))*rad
  plate(b,orbitfn,.411,.55,aa,cc,0,(j+5)%16,.035)
 # True convex lens cover, separate from the recessed geometric aperture.
 lens_center=p+n*.048
 radii=[0,.055,.115,.175,.228]
 for rr0,rr1 in zip(radii,radii[1:]):
  for j in range(48):
   aa=j*2*pi/48;cc=(j+1)*2*pi/48
   def lenspt(rad,ang):return lens_center+n*(.029*(1-(rad/.228)**2))+(u*cos(ang)+v*sin(ang))*rad
   if rr0==0:b.face([lenspt(0,aa),lenspt(rr1,aa),lenspt(rr1,cc)],8,smooth=True)
   else:b.quad(lenspt(rr0,aa),lenspt(rr1,aa),lenspt(rr1,cc),lenspt(rr0,cc),8,smooth=True)
 # Three thin swept fins, sockets, bright perimeter rails, etched ribs and bolts.
 for i,(x,h) in enumerate([(.22,.68),(.72,.88),(1.20,.64)]):
  z=prof(x)[1]+prof(x)[2]
  box(b,(x,0,z+.015),(.34,.25,.09),2);box(b,(x,0,z+.060),(.32,.19,.04),3)
  poly=[(x-.18,z+.07),(x+.19,z+.07),(x+.12,z+.33*h),(x-.03,z+h),(x-.29,z+h-.12),(x-.25,z+.33*h)]
  for side in [-1,1]:
   pts=[(xx,side*.045,zz) for xx,zz in poly];b.face(pts,9,[(.02,.02),(.22,.02),(.22,.08),(.20,.22),(.02,.20),(.02,.08)])
   for j in range(len(poly)):
    aa=Vector(pts[j]);bb=Vector(pts[(j+1)%len(poly)]);mid=(aa+bb)/2;d=bb-aa;cyl(b,mid,.018,d.length,d,3,8)
   for f in [.28,.52,.76]:
    z1=z+.10+h*f;xx=x-.08-f*.07
    box(b,(xx,side*.049,z1),(.22,.008,.014),6)
   bolt(b,(x+.04,side*.056,z+.17),(0,side,0),.03)
  for j in range(len(poly)):
   a=poly[j];c=poly[(j+1)%len(poly)];b.quad((a[0],-.045,a[1]),(c[0],-.045,c[1]),(c[0],.045,c[1]),(a[0],.045,a[1]),3)
 # Muzzle nostril recesses and top vent grille, real black inserts.
 for sign in [-1,1]:
  p=Vector(headfn(2.03,sign*.64,.01));n=Vector((.3,sign*.5,.65)).normalized()
  annulus(b,p,.055,.083,.027,n,3,n=24);cyl(b,p-n*.01,.055,.02,n,2,24)
 for k in range(8):box(b,(.12+k*.06,-.18,.674),(.025,.23,.016),2)
 annulus(b,(-.12,0,0),.49,.565,.08,mat=2,n=48)
 annulus(b,(-.15,0,0),.51,.535,.07,mat=4,n=32,segments=True)
 return b.object('Head')

def export(objects,filename):
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:
  o.select_set(True)
  if not o.modifiers.get('Game_Triangulate'):o.modifiers.new('Game_Triangulate','TRIANGULATE')
 bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,filename),export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_tangents=True,export_normals=True,export_texcoords=True,export_materials='EXPORT',export_draco_mesh_compression_enable=False,export_animations=False,export_extras=True)
 bpy.ops.object.select_all(action='DESELECT')

def tri(o):o.data.calc_loop_triangles();return len(o.data.loop_triangles)

def catmull(points,steps=40):
 out=[]
 pp=[points[0]]+points+[points[-1]]
 for k in range(1,len(pp)-2):
  p0,p1,p2,p3=[Vector(v) for v in pp[k-1:k+3]]
  for j in range(steps):
   t=j/steps;out.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t))
 out.append(Vector(points[-1]));return out

def resample(path,pitch):
 out=[path[0]];run=0
 for a,b in zip(path,path[1:]):
  d=(b-a).length
  while run+d>=pitch:
   remain=pitch-run;a=a+(b-a)*(remain/d);out.append(a.copy());d=(b-a).length;run=0
  run+=d
 return out

def main():
 scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
 h=head()
 if not os.environ.get('SKIP_HEAD_BAKE'):
  import sys;sys.path.insert(0,ROOT)
  from bake_head import bake_head
  bake_head(h,ROOT)
  from consolidate_head import consolidate_head
  consolidate_head(h,ROOT)
 s=body();print('COUNTS_INITIAL',tri(h),tri(s))
 # Local front convention conversion. All mesh data transformed, object scales remain unit.
 conv=Matrix.Rotation(-pi/2,4,'Z')
 h.data.transform(conv);s.data.transform(conv @ Matrix.Diagonal((-1,1,1,1)));s.data.flip_normals()
 h['pivot']='neck joint; local +Z glTF toward muzzle';s['pivot']='forward joint at local origin; section extends toward local -Z in glTF';s['pitch_m']=.92
 # Move body geometry behind its forward joint (Blender +Y), retain ring at forward joint side.
 s.data.transform(Matrix.Translation((0,.46,0)))
 export([h],'snake_head.glb');export([s],'snake_segment.glb')
 h.hide_render=True;s.hide_render=True;h.hide_set(True);s.hide_set(True)
 source=bpy.data.collections.new('Source_Assets');scene.collection.children.link(source)
 for ob in [h,s]:
  for c in list(ob.users_collection):c.objects.unlink(ob)
  source.objects.link(ob)
 source.hide_render=True
 # Raised serpentine S and grounded coil, sampled at a fixed joint pitch.
 pts=[(-2.35,.15,3.85),(-1.55,.30,3.60),(-.80,.42,2.82),(-.90,.33,1.75),(-1.70,.10,.78),(-2.65,-.75,.65),(-2.15,-1.85,.65),(-.35,-2.05,.65),(1.60,-1.55,.65),(2.55,-.20,.65),(2.20,1.20,.65),(.55,1.75,.65),(-.75,1.30,.65),(-.30,.25,.65),(1.35,.15,.65),(3.00,.38,.58),(3.75,-.65,.46),(3.20,-1.95,.30),(2.05,-2.65,.20)]
 path=resample(catmull(pts),.92);print('SEGMENT_COUNT',len(path)-1)
 # Curve transport frames. Local Blender -Y is forward; local Z remains dorsal.
 def frame(p,forward):
  z=Vector((0,0,1));f=forward.normalized();right=z.cross(f).normalized();up=f.cross(right).normalized()
  return Matrix(((right.x,-f.x,up.x,p.x),(right.y,-f.y,up.y,p.y),(right.z,-f.z,up.z,p.z),(0,0,0,1)))
 full=[];hh=bpy.data.objects.new('Head_Joint',h.data);scene.collection.objects.link(hh);hh.matrix_world=frame(path[0],Vector((-1,0,.12)));hh['role']='static head on neck joint';full.append(hh)
 for i in range(len(path)-1):
  p=path[i];f=path[i]-path[i+1]
  o=bpy.data.objects.new('Segment_%02d'%i,s.data.copy());scene.collection.objects.link(o)
  scale=1.0 if i< len(path)-8 else max(.20,1-(i-(len(path)-8))*.13)
  o.matrix_world=frame(p,f)
  if scale!=1:
   # Taper dimensions in mesh data, keep object scale one for game transforms.
   o.data.transform(Matrix.Diagonal((scale,1,scale,1)))
  # Each assembly gets a distinct crop/rotation of the shared worn-metal atlas.
  for poly in o.data.polygons:
   if poly.material_index==1:
    for li in poly.loop_indices:
     uv=o.data.uv_layers.active.data[li].uv
     tx=min(3,int(uv.x*4));ty=min(3,int(uv.y*4));local=Vector((uv.x*4-tx,uv.y*4-ty));tile=(ty*4+tx+i*3)%16
     if i%2:local.x=1-local.x
     local=local*(.88+(i%5)*.018)+Vector((.012*(i%4),.009*(i%3)))
     uv.x=(tile%4+local.x)/4;uv.y=(tile//4+local.y)/4
  o['joint_index']=i;o['curve_distance_m']=i*.92;o['rigid_segment']=True;o['radius_scale']=scale;full.append(o)
 # Pointed terminal tail with lateral metal fins, separate joint mesh.
 tail=Mesh()
 cyl(tail,(0,.40,0),.20,1.16,(0,1,0),2,16,r2=.018)
 def tailfn(x,a,o):
  r=.22*(1-max(0,x)/1.12)+.025+o
  return (r*sin(a),x,r*cos(a))
 for k,(x0,x1) in enumerate([(-.13,.28),(.30,.68),(.70,1.02)]):
  for j in range(6):
   a=j*pi/3;plate(tail,tailfn,x0,x1,a+.025,a+pi/3-.025,1,(k*5+j)%16,.026)
 for side in [-1,1]:
  points=[(side*.16,.10,.015),(side*.49,.25,.015),(side*.38,.55,.015),(side*.11,.68,.015)]
  tail.face(points,0);tail.face([(x,y,z-.035) for x,y,z in reversed(points)],0)
  for j in range(4):
   aa=Vector(points[j]);bb=Vector(points[(j+1)%4]);tail.quad(aa,bb,bb-Vector((0,0,.035)),aa-Vector((0,0,.035)),3)
  box(tail,(side*.17,.31,0),(.07,.44,.075),6)
 # Dorsal tail-tip fin mounted in a titanium socket.
 box(tail,(0,.25,.21),(.10,.33,.06),6)
 tail.face([(-.025,.10,.22),(-.025,.19,.42),(-.025,.50,.28),(-.025,.48,.17)],0)
 tail.face([(.025,.48,.17),(.025,.50,.28),(.025,.19,.42),(.025,.10,.22)],0)
 
 for a,b in zip([(.10,.22),(.19,.42),(.50,.28),(.48,.17)],[ (.19,.42),(.50,.28),(.48,.17),(.10,.22)]):
  tail.quad((-.025,a[0],a[1]),(.025,a[0],a[1]),(.025,b[0],b[1]),(-.025,b[0],b[1]),3)
 tt=tail.object('Tail_Joint');tt.matrix_world=frame(path[-1],path[-2]-path[-1]);full.append(tt)
 total=sum(tri(o) for o in full)
 assert 10000<=tri(h)<=18000 and total<=60000,(tri(h),total)
 print('COUNTS_FINAL',tri(h),tri(s),total)
 json.dump({'head':tri(h),'segment':tri(s),'full':total,'segment_count':len(path)-1,'pitch_m':.92,'joints':[{'name':o.name,'matrix':[list(row) for row in o.matrix_world]} for o in full]},open(os.path.join(ROOT,'build_stats.json'),'w'),indent=2)
 export(full,'snake_full.glb')
 for im in bpy.data.images:
  if im.source=='FILE':im.pack()
 bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'snake.blend'))
if __name__=='__main__':main()
