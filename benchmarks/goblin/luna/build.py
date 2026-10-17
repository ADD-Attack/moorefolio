import bpy, math, random, os
from mathutils import Vector
random.seed(21)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for d in bpy.data.materials: bpy.data.materials.remove(d)
# materials
def mat(name,color,rough=.55,metal=0,sub=0):
 m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True; p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1); p.inputs['Roughness'].default_value=rough; p.inputs['Metallic'].default_value=metal; p.inputs['Subsurface Weight'].default_value=sub; return m
skin=mat('Moss jade skin',(0.19,.34,.105),.48,0,.08); skinhi=mat('Warm raised skin',(0.29,.43,.14),.5,0,.06); shadow=mat('Deep green recess',(.055,.095,.035),.7); ear=mat('Ear inner | burnt rose',(.34,.105,.075),.62); cloth=mat('Oxblood woven leather',(.18,.035,.028),.65); clothhi=mat('Worn crimson seams',(.4,.095,.045),.58); leather=mat('Dark umber leather',(.105,.055,.028),.56); leatherhi=mat('Leather edge',(.31,.17,.065),.5); brass=mat('Hammered brass',(.58,.32,.075),.3,.72); steel=mat('Blue tempered iron',(.12,.19,.22),.27,.82); bone=mat('Ivory',(.83,.72,.48),.33); eye=mat('Amber iris',(.93,.43,.045),.2); black=mat('Obsidian pupil',(.018,.012,.008),.18); white=mat('Eye glint',(1,.93,.72),.14); ground=mat('Studio gray',(.235,.25,.27),.82)
# helpers
def uv(name,loc,scale,ma,seg=32,rings=20):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,location=loc); o=bpy.context.object; o.name=name; o.scale=scale; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(ma); bpy.ops.object.shade_smooth(); return o
def cube(name,loc,scale,ma,bevel=.08):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=bpy.context.object; o.name=name; o.dimensions=scale; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(ma)
 if bevel: mod=o.modifiers.new('Hand softened edges','BEVEL'); mod.width=bevel; mod.segments=3; o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
 return o
def cyl(name,a,b,r,ma,r2=None,verts=16):
 a,b=Vector(a),Vector(b); v=b-a; bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=r if r2 is None else r2, depth=v.length, location=(a+b)/2); o=bpy.context.object; o.name=name; o.rotation_mode='QUATERNION'; o.rotation_quaternion=v.to_track_quat('Z','Y'); o.data.materials.append(ma); o.modifiers.new('Soft edge normals','WEIGHTED_NORMAL'); return o
def curve(name,pts,bevel,ma):
 c=bpy.data.curves.new(name,'CURVE'); c.dimensions='3D'; c.resolution_u=16; c.bevel_depth=bevel; c.bevel_resolution=3; s=c.splines.new('BEZIER'); s.bezier_points.add(len(pts)-1)
 for p,co in zip(s.bezier_points,pts): p.co=co; p.handle_left_type='AUTO'; p.handle_right_type='AUTO'
 o=bpy.data.objects.new(name,c); bpy.context.collection.objects.link(o); o.data.materials.append(ma); return o
def torus(name,loc,major,minor,ma,rot=None):
 bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,major_segments=32,minor_segments=10,location=loc); o=bpy.context.object;o.name=name;o.data.materials.append(ma);o.rotation_euler=rot or (0,0,0);bpy.ops.object.shade_smooth();return o
# torso: compact hunched broad silhouette
uv('ribcage',(0,0,3.28),(.72,.43,.84),skin); uv('belly',(0,-.06,2.78),(.57,.39,.55),skin); uv('pelvis',(0,.015,2.35),(.57,.39,.4),skin)
# shoulder / neck
uv('neck',(0,-.04,3.95),(.37,.33,.46),skin); uv('trapezius',(0,.015,3.77),(.69,.34,.34),skinhi)
# head jaw / skull
uv('jaw',(0,-.13,4.42),(.53,.42,.51),skin); uv('cranium',(0,-.05,4.77),(.59,.46,.62),skin)
# cheek pads, muzzle, nose bridge
for s in [-1,1]:
 uv('Cheek plane',(.39*s,-.36,4.49),(.23,.19,.24),skinhi)
uv('Muzzle',(0,-.45,4.37),(.39,.22,.23),skinhi); uv('Nose bridge',(0,-.43,4.69),(.18,.2,.34),skin); uv('Broad nose',(0,-.56,4.55),(.25,.2,.16),skinhi)
for s in [-1,1]: uv('Nostril',(.13*s,-.718,4.53),(.052,.018,.035),shadow,20,12)
# ears broad tapered leaf mesh via shaped ellipsoids plus point cone
for s in [-1,1]:
 # sculpted leaf form oriented outward
 o=uv('Long pointed ear',(.69*s,-.01,4.91),(.48,.16,.22),skinhi); o.rotation_euler[1]=s*math.radians(-17)
 cyl('Ear tip',(.84*s,-.015,4.95),(1.23*s,-.015,5.16),.145,skinhi,.005,24)
 o=uv('Inset ear',(.75*s,-.15,4.94),(.29,.035,.105),ear); o.rotation_euler[1]=s*math.radians(-15)
 curve('Ear cartilage',[(.55*s,-.19,4.88),(.72*s,-.2,5.0),(.92*s,-.19,4.99)],.018,skin)
# eyes, brow ridge and fine facial shapes
for s in [-1,1]:
 uv('Eye socket',(.245*s,-.414,4.79),(.205,.12,.16),shadow)
 uv('Golden eye',(.245*s,-.51,4.79),(.138,.074,.103),bone)
 uv('Amber iris',(.24*s,-.572,4.786),(.063,.025,.073),eye,24,16)
 uv('Vertical pupil',(.24*s,-.593,4.786),(.018,.012,.057),black,20,16)
 uv('Catchlight',(.255*s,-.606,4.82),(.017,.009,.017),white,16,10)
 o=uv('Heavy brow',(.245*s,-.49,4.98),(.26,.16,.115),skinhi);o.rotation_euler[1]=-s*.16
 # tusks upward at corners
 cyl('Lower tusk',(.34*s,-.57,4.28),(.31*s,-.6,4.48),.095,bone,.012,20)
# mouth dark inset and lip
uv('Mouth shadow',(0,-.604,4.31),(.28,.026,.07),shadow); curve('Lower lip',[(-.22,-.63,4.28),(0,-.65,4.25),(.22,-.63,4.28)],.025,skinhi)
# head wrinkles/scars
for s in [-1,1]:
 curve('Forehead crease',[(.07*s,-.49,5.12),(.18*s,-.515,5.16),(.29*s,-.48,5.13)],.012,skin)
 curve('Cheek scar',[(.43*s,-.526,4.57),(.48*s,-.53,4.49),(.45*s,-.51,4.43)],.018,clothhi)
# hair cap via UV + locks
uv('Rough black-green hair',(0,.015,5.22),(.57,.46,.23),leather)
for i in range(11):
 x=(i-5)*.085; z=5.29+random.uniform(-.04,.06); uv('Hair clump',(x,-.15,z),(.1,.22,.12),leather,20,12)
# asymmetrical shoulder armor / leather harness
for s in [-1,1]:
 uv('Shoulder muscle',(.75*s,0,3.78),(.35,.38,.34),skin)
# pauldron on character's left (image right)
uv('Iron pauldron',(.72,-.01,3.94),(.47,.46,.31),steel)
# layered armor lobes
for x,z in [(.42,3.93),(.7,4.13),(1,3.98),(.7,3.76)]: uv('Pauldron plate scale',(x,-.36,z),(.22,.12,.16),steel)
curve('Brass pauldron rim',[(.36,-.31,3.82),(.56,-.42,3.67),(.85,-.4,3.67),(1.08,-.27,3.83)],.036,brass)
for x,z in [(.52,3.98),(.73,4.1),(.92,3.96),(.72,3.78)]: uv('Armor rivet',(x,-.477,z),(.035,.025,.035),brass,16,10)
# straps crossing torso, modeled as curves
curve('Cross-body baldric',[(-.48,-.35,3.69),(-.22,-.48,3.43),(.12,-.47,3.14),(.47,-.28,2.96)],.09,leather)
curve('Baldric piping',[(-.5,-.405,3.72),(-.23,-.54,3.45),(.14,-.53,3.15),(.48,-.35,2.98)],.018,leatherhi)
# tunic skirt torso tabard at front, shaped mesh drape
def panel(name,verts,faces,ma):
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.materials.append(ma);o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o); sol=o.modifiers.new('Tailored thickness','SOLIDIFY');sol.thickness=.045; be=o.modifiers.new('Soft cloth edges','BEVEL');be.width=.025;be.segments=2;return o
panel('Split oxblood tabard',[(-.39,-.44,2.63),(.39,-.44,2.63),(.36,-.44,1.92),(.12,-.46,2.02),(0,-.46,1.87),(-.12,-.46,2.03),(-.38,-.44,1.92)],[(0,1,2,3,4,5,6)],cloth)
for x in [-.27,-.1,.1,.27]: curve('Tabard stitched fold',[(x,-.49,2.58),(x*1.08,-.5,2.3),(x*.9,-.5,2.05)],.012,clothhi)
# Belt band and large buckle
cube('Wide battle belt',(0,-.015,2.54),(1.17,.79,.2),leather,.08)
curve('Belt top piping',[(-.56,-.43,2.65),(0,-.44,2.65),(.56,-.43,2.65)],.023,leatherhi)
cube('Brass buckle',(0,-.433,2.55),(.28,.09,.23),brass,.025);cube('Buckle inset',(0,-.49,2.55),(.16,.03,.12),leather,.018)
# belt pouches, straps, metal studs
for x in [-.46,.45]:
 cube('Belt pouch',(x,-.44,2.47),(.22,.17,.25),leather,.045);cube('Pouch flap',(x,-.54,2.55),(.23,.06,.1),leatherhi,.022);uv('Pouch stud',(x,-.58,2.54),(.025,.018,.025),brass,16,10)
for x in [-.52,-.35,.35,.52]: uv('Belt brass stud',(x,-.432,2.55),(.025,.018,.025),brass,16,10)
# arms posed: left relaxed bent, right hand holding dagger up diagonally
# shoulder -> elbow -> wrist and tapered anatomy
# arm camera-facing coordinates
for s in [-1,1]:
 shoulder=(.67*s,0,3.72)
 if s==-1: elbow=(-.94,-.02,3.12); wrist=(-.82,-.25,2.77)
 else: elbow=(1.02,-.01,3.35); wrist=(1.22,-.32,3.63)
 uv('Upper arm',((shoulder[0]+elbow[0])/2,(shoulder[1]+elbow[1])/2,(shoulder[2]+elbow[2])/2),(.24,.25,.47),skin)
 cyl('Forearm',(elbow[0],elbow[1],elbow[2]),(wrist[0],wrist[1],wrist[2]),.19,skinhi,.135,24)
 uv('Elbow',(elbow[0],elbow[1],elbow[2]),(.23,.23,.22),skin)
 uv('Hand',(wrist[0],wrist[1],wrist[2]-.04),(.2,.16,.21),skinhi)
 # four individual fingers, curled slightly toward palm
 for j in range(4):
  dx=(j-1.5)*.085; start=(wrist[0]+dx,wrist[1]-.11,wrist[2]-.1)
  end=(wrist[0]+dx+(.02 if s==1 else -.02),wrist[1]-.16,wrist[2]-.28-(.025 if j in [1,2] else 0))
  cyl('Finger',start,end,.047,skinhi,.037,12);uv('Knuckle',start,(.055,.05,.052),skin,16,10)
 # thumb
 cyl('Thumb',(wrist[0]-.15,wrist[1]-.04,wrist[2]),(wrist[0]-.25,wrist[1]-.17,wrist[2]-.1),.065,skinhi,.045,12)
# forearm bracers
cyl('Left bracer',(-.9,-.07,3.0),(-.82,-.2,2.76),.205,leather,.16,12);curve('Bracer brass edge',[(-1.06,-.12,2.93),(-.87,-.26,2.93),(-.72,-.15,2.93)],.025,brass)
cyl('Right vambrace',(.99,-.04,3.38),(1.17,-.24,3.59),.22,leather,.16,12)
# dagger held in raised right hand, blade angled up/right
cyl('Dagger grip',(1.22,-.4,3.62),(1.36,-.4,3.79),.065,leatherhi,.055,12)
cyl('Dagger crossguard',(1.23,-.4,3.77),(1.42,-.4,3.66),.045,brass,.045,12)
cyl('Dagger blade',(1.36,-.4,3.78),(1.72,-.4,4.35),.105,steel,.002,5)
curve('Blade fuller',[(1.38,-.512,3.82),(1.55,-.505,4.11),(1.68,-.44,4.31)],.012,brass)
# legs: asymmetrical heroic stance, braced boots
# pelvis to knees to feet
for s in [-1,1]:
 hip=(.31*s,0,2.27)
 if s==-1: knee=(-.39,-.01,1.28); ankle=(-.52,-.08,.38); foot=(-.56,-.37,.18)
 else: knee=(.43,.02,1.35); ankle=(.52,.12,.4); foot=(.59,-.25,.18)
 uv('Thigh',(hip[0]*.55+knee[0]*.45,0,1.86),(.31,.32,.58),skin)
 cyl('Shin',(knee[0],knee[1],knee[2]),(ankle[0],ankle[1],ankle[2]),.225,skinhi,.15,24)
 uv('Kneecap',(knee[0],-.2,knee[2]),(.26,.2,.23),skin)
 uv('Boot',(foot[0],foot[1],.19),(.34,.53,.2),leather)
 # shin guards
 cyl('Greave',(knee[0],-.23,knee[2]-.04),(ankle[0],-.18,ankle[2]+.08),.235,steel,.17,10)
 curve('Greave bright edge',[(knee[0]-.12,-.43,knee[2]-.08),(knee[0],-.46,(knee[2]+ankle[2])/2),(ankle[0]+.1,-.34,ankle[2]+.1)],.025,brass)
 # ankle wrap bands
 for z in [.48,.58]: torus('Boot wrap',(ankle[0],ankle[1],z),.16,.035,leatherhi)
 # boot toe cap, rivets
 uv('Iron toe cap',(foot[0],foot[1]-.36,.22),(.26,.2,.1),steel)
 for xoff in [-.12,0,.12]: uv('Toe rivet',(foot[0]+xoff,foot[1]-.51,.24),(.018,.015,.018),brass,12,8)
# decorative scars/tattoos and body pores on visible side
for i in range(5): uv('Skin freckle',(-.37+random.random()*.2,-.525,4.53+random.random()*.12),(.012,.008,.012),leatherhi,12,8)
# ground + cyc
bpy.ops.mesh.primitive_plane_add(size=200, location=(0,0,-.025)); bpy.context.object.name='Matte seamless studio floor';bpy.context.object.data.materials.append(ground)
# camera
def aim(o,pt): o.rotation_euler=(Vector(pt)-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(7.7,-12.5,6.15)); cam=bpy.context.object; aim(cam,(0,0,2.68));cam.data.type='ORTHO';cam.data.ortho_scale=12.0; bpy.context.scene.camera=cam;cam.data.lens=50
# lighting
def area(name,loc,power,color,size,target):
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.color=color;o.data.shape='DISK';o.data.size=size;aim(o,target)
area('Key | large warm softbox',(-4,-6,8),1050,(1,.82,.64),5,(0,0,3))
area('Fill | cool softbox',(4,-4,5.4),850,(.64,.78,1),4,(0,0,3))
area('Rim | warm high strip',(1.5,3.8,7.4),1350,(1,.65,.36),3,(0,0,3.2))
area('Face catchlight',(-.5,-4.5,6),250,(1,.93,.8),2,(0,0,4.5))
scene=bpy.context.scene; scene.render.engine='CYCLES'; scene.cycles.samples=64; scene.cycles.use_denoising=True
scene.render.resolution_x=1920;scene.render.resolution_y=1080;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.world.color=(.18,.18,.18)
scene.camera.data.lens=54
scene.render.filepath=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'render.png')
# Set transparent-free plain gray world
scene.world.use_nodes=True; scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.235,.25,.27,1);scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.55
# output
bpy.ops.render.render(write_still=True)
