"""BRAMBLE — a procedural goblin character study. Blender 4.5 LTS.
Run: blender -b --python build.py
Optional development pass: blender -b --python build.py -- --preview
No external assets, textures, fonts or add-ons are required.
"""
import bpy, math, random, os, sys
from mathutils import Vector, Matrix
from math import sin, cos, pi
random.seed(71)
PREVIEW = '--preview' in sys.argv
OUT = os.path.dirname(os.path.abspath(__file__))
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for data in bpy.data.materials: bpy.data.materials.remove(data)

# ---------- Layered, physically based surfaces ----------
def material(name, color, rough=.5, metal=0, noise=0, bump=.1, scale=45):
    m=bpy.data.materials.new(name); m.use_nodes=True
    n=m.node_tree.nodes; l=m.node_tree.links; p=n.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=rough; p.inputs['Metallic'].default_value=metal
    if noise:
        tex=n.new('ShaderNodeTexNoise'); tex.inputs['Scale'].default_value=scale
        tex.inputs['Detail'].default_value=3; tex.inputs['Roughness'].default_value=.72
        ramp=n.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position=.18
        ramp.color_ramp.elements[0].color=(*(c*(1-noise) for c in color),1)
        ramp.color_ramp.elements[1].position=.82
        ramp.color_ramp.elements[1].color=(*(min(1,c*(1+noise)) for c in color),1)
        l.new(tex.outputs['Fac'],ramp.inputs[0]); l.new(ramp.outputs[0],p.inputs['Base Color'])
        b=n.new('ShaderNodeBump'); b.inputs['Strength'].default_value=bump; b.inputs['Distance'].default_value=.035
        l.new(tex.outputs['Fac'],b.inputs['Height']); l.new(b.outputs[0],p.inputs['Normal'])
    return m
skin=material('01 • olive jade | living skin',(.115,.205,.064),.56,noise=.22,bump=.19,scale=83)
p=skin.node_tree.nodes.get('Principled BSDF'); p.inputs['Subsurface Weight'].default_value=.075
p.inputs['Subsurface Radius'].default_value=(1,.52,.3)
p.inputs['Specular IOR Level'].default_value=.32
skin_hi=material('02 • raised skin folds',(.132,.218,.075),.56,noise=.15,bump=.12,scale=85)
skin_dark=material('03 • recessed creases',(.085,.13,.044),.61)
ear_mat=material('04 • warm inner ear',(.22,.165,.09),.62,noise=.25,bump=.14,scale=65)
lip=material('05 • olive umber lips',(.10,.125,.038),.56,noise=.17,bump=.1)
nostril=material('06 • nostril & mouth interior',(.023,.031,.014),.72)
leather=material('07 • weathered umber hide',(.105,.052,.025),.57,noise=.45,bump=.31,scale=65)
leather_edge=material('08 • leather cut edges',(.24,.126,.055),.64,noise=.25,bump=.2)
leather_dark=material('09 • boot leather',(.044,.035,.024),.49,noise=.35,bump=.3,scale=95)
cloth=material('10 • oxblood woven linen',(.19,.037,.025),.84,noise=.3,bump=.35,scale=145)
cloth_dark=material('11 • charcoal linen',(.052,.063,.052),.88,noise=.3,bump=.28,scale=125)
steel=material('12 • blued forged iron',(.055,.085,.09),.45,.82,noise=.38,bump=.23,scale=48)
edge=material('13 • exposed steel edges',(.33,.39,.38),.3,.86,noise=.18,bump=.1,scale=75)
brass=material('14 • antique bronze',(.40,.245,.075),.34,.78,noise=.3,bump=.16,scale=65)
bone=material('15 • old ivory',(.69,.57,.33),.36,noise=.16,bump=.12,scale=75)
thread=material('16 • waxed flax stitching',(.48,.34,.16),.8)
fur_dark=material('17 • mantle underfur',(.075,.065,.045),.88,noise=.38,bump=.4)
fur=material('18 • guard hairs',(.24,.22,.16),.8,noise=.3,bump=.2)
hair=material('19 • near black hair',(.035,.045,.025),.55,noise=.3,bump=.2)
eye_white=material('20 • golden sclera',(.36,.30,.12),.27)
iris=material('21 • amber iris',(.78,.275,.018),.24,metal=.12,noise=.3,bump=.05,scale=30)
pupil=material('22 • vertical pupils',(.006,.009,.003),.17)
scar=material('23 • healed scar tissue',(.24,.28,.12),.58,noise=.15,bump=.12)

cornea=material('26 • clear wet cornea',(.96,.98,1.0),.045)
cbs=cornea.node_tree.nodes.get('Principled BSDF'); cbs.inputs['Transmission Weight'].default_value=1
cbs.inputs['IOR'].default_value=1.36
nail_mat=material('25 • horn fingernails',(.065,.080,.033),.40,noise=.2,bump=.12)

# Skin uses independent pore, mottling, roughness and anatomical warmth scales.
for skinmat in [skin,skin_hi]:
    nodes=skinmat.node_tree.nodes; links=skinmat.node_tree.links
    bs=nodes.get('Principled BSDF')
    original=bs.inputs['Base Color'].links[0].from_socket
    mottling=nodes.new('ShaderNodeTexNoise'); mottling.inputs['Scale'].default_value=5.5; mottling.inputs['Detail'].default_value=4
    blood=nodes.new('ShaderNodeAttribute'); blood.attribute_name='BloodFlow'
    mult=nodes.new('ShaderNodeMath'); mult.operation='MULTIPLY'; mult.inputs[1].default_value=.16
    add=nodes.new('ShaderNodeMath'); add.operation='ADD'
    links.new(mottling.outputs['Fac'],mult.inputs[0]); links.new(mult.outputs[0],add.inputs[0]); links.new(blood.outputs['Fac'],add.inputs[1])
    mix=nodes.new('ShaderNodeMixRGB'); mix.blend_type='MIX'; mix.inputs[2].default_value=(.235,.18,.065,1)
    links.new(add.outputs[0],mix.inputs[0]); links.new(original,mix.inputs[1]); links.new(mix.outputs[0],bs.inputs['Base Color'])
    pores=nodes.new('ShaderNodeTexVoronoi'); pores.distance='EUCLIDEAN'; pores.inputs['Scale'].default_value=185
    porebump=nodes.new('ShaderNodeBump'); porebump.inputs['Strength'].default_value=.22; porebump.inputs['Distance'].default_value=.012; porebump.invert=True
    links.new(pores.outputs['Distance'],porebump.inputs['Height'])
    oldnormal=bs.inputs['Normal'].links[0].from_socket
    links.new(oldnormal,porebump.inputs['Normal']); links.new(porebump.outputs[0],bs.inputs['Normal'])
    rough=nodes.new('ShaderNodeMapRange'); rough.inputs['From Min'].default_value=0; rough.inputs['From Max'].default_value=1
    rough.inputs['To Min'].default_value=.43; rough.inputs['To Max'].default_value=.64
    links.new(mottling.outputs['Fac'],rough.inputs['Value']); links.new(rough.outputs['Result'],bs.inputs['Roughness'])

ivnodes=bone.node_tree.nodes; ivlinks=bone.node_tree.links; ivp=ivnodes.get('Principled BSDF')
ivtc=ivnodes.new('ShaderNodeTexCoord'); ivsep=ivnodes.new('ShaderNodeSeparateXYZ')
ivlinks.new(ivtc.outputs['Generated'],ivsep.inputs[0])
ivr=ivnodes.new('ShaderNodeValToRGB'); ivr.color_ramp.elements[0].position=.04; ivr.color_ramp.elements[0].color=(.30,.21,.10,1)
ivr.color_ramp.elements[1].position=.75; ivr.color_ramp.elements[1].color=(.76,.69,.48,1)
ivlinks.new(ivsep.outputs['Z'],ivr.inputs[0]); ivlinks.new(ivr.outputs[0],ivp.inputs['Base Color'])
ivp.inputs['Subsurface Weight'].default_value=.035

# ---------- Reusable modeling primitives ----------
def smooth(obj, mat=None):
    if mat: obj.data.materials.append(mat)
    if obj.type=='MESH':
        for p in obj.data.polygons: p.use_smooth=True
    return obj

def uv(name, loc, scale, mat, seg=40, rings=28):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return smooth(o,mat)

def mesh(name, verts, faces, mat, sub=0):
    me=bpy.data.meshes.new(name); me.from_pydata(verts,[],faces); me.update()
    o=bpy.data.objects.new(name,me); bpy.context.collection.objects.link(o); smooth(o,mat)
    if sub:
        md=o.modifiers.new('Soft sculpted contours','SUBSURF'); md.levels=sub; md.render_levels=sub
    return o

def tube(name, points, radii, mat, sides=12, sub=1):
    # Generalized cylinder following a three-dimensional gesture.
    vs=[]; fs=[]
    for i,p in enumerate(points):
        p=Vector(p)
        tangent=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(i-1,0)])
        tangent.normalize(); ref=Vector((0,1,0))
        if abs(tangent.dot(ref))>.94: ref=Vector((1,0,0))
        a=tangent.cross(ref).normalized(); b=tangent.cross(a).normalized()
        for j in range(sides):
            t=2*pi*j/sides; v=p+radii[i]*(a*cos(t)+b*sin(t)); vs.append(tuple(v))
    for i in range(len(points)-1):
        for j in range(sides):
            a=i*sides+j; b=i*sides+(j+1)%sides; fs.append((a,b,b+sides,a+sides))
    fs.append(tuple(range(sides-1,-1,-1))); fs.append(tuple((len(points)-1)*sides+j for j in range(sides)))
    return mesh(name,vs,fs,mat,sub)

def curve(name, points, radius, mat):
    cu=bpy.data.curves.new(name,'CURVE'); cu.dimensions='3D'; cu.resolution_u=16
    sp=cu.splines.new('BEZIER'); sp.bezier_points.add(len(points)-1)
    for b,co in zip(sp.bezier_points,points): b.co=co; b.handle_left_type='AUTO'; b.handle_right_type='AUTO'
    cu.bevel_depth=radius; cu.bevel_resolution=3
    ob=bpy.data.objects.new(name,cu); bpy.context.collection.objects.link(ob); ob.data.materials.append(mat); return ob

def link(name,a,b,r1,r2,mat):
    a,b=Vector(a),Vector(b)
    bpy.ops.mesh.primitive_cone_add(vertices=32,radius1=r1,radius2=r2,depth=(b-a).length,location=(a+b)/2)
    o=bpy.context.object; o.name=name; o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler(); smooth(o,mat)
    be=o.modifiers.new('Rounded edges','BEVEL'); be.width=.035; be.segments=3
    return o

def cube(name,loc,scale,mat,bevel=.05):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=bpy.context.object; o.name=name; o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); smooth(o,mat)
    if bevel:
        m=o.modifiers.new('Hand softened edges','BEVEL'); m.width=bevel; m.segments=3
        m=o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    return o

def loft(name, rings, mat, n=64, sub=2):
    # rings: z, x radius, y radius, x offset, y offset
    vs=[]; fs=[]
    for z,rx,ry,cx,cy in rings:
        for j in range(n):
            a=2*pi*j/n; vs.append((cx+rx*cos(a),cy+ry*sin(a),z))
    for k in range(len(rings)-1):
        for j in range(n):
            a=k*n+j; b=k*n+(j+1)%n; fs.append((a,b,b+n,a+n))
    fs.extend([tuple(range(n-1,-1,-1)),tuple((len(rings)-1)*n+j for j in range(n))])
    return mesh(name,vs,fs,mat,sub)

def fuse(name,obs,mat,voxel=.036):
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs: o.select_set(True)
    bpy.context.view_layer.objects.active=obs[0]; bpy.ops.object.join(); o=bpy.context.object; o.name=name
    r=o.modifiers.new('Unified sculpt volume','REMESH'); r.mode='VOXEL'; r.voxel_size=voxel
    bpy.ops.object.modifier_apply(modifier=r.name)
    sm=o.modifiers.new('Relax sculpt','SMOOTH'); sm.factor=.6; sm.iterations=5
    bpy.ops.object.modifier_apply(modifier=sm.name)
    o.data.materials.clear(); o.data.materials.append(mat); smooth(o)
    d=o.modifiers.new('Subtle dermal irregularity','DISPLACE'); tex=bpy.data.textures.new(name+' skin grain',type='CLOUDS'); tex.noise_scale=.13; tex.noise_depth=2
    d.texture=tex; d.strength=.009; d.mid_level=.5
    su=o.modifiers.new('Sculpt finish','SUBSURF'); su.levels=1
    return o

def rivet(loc,r=.045,mat=brass): return uv('Hand peened rivet',loc,(r,r*.50,r),mat,20,12)
def torus(name,loc,major,minor,mat,rot=(pi/2,0,0)):
    bpy.ops.mesh.primitive_torus_add(major_segments=48,minor_segments=12,location=loc,major_radius=major,minor_radius=minor,rotation=rot)
    o=bpy.context.object; o.name=name; return smooth(o,mat)

# ---------- Weight, gesture and underlying anatomy ----------
# Broad chest, narrow hips and a grounded, slightly uneven stance.
body=loft('Underlying torso',[(2.55,.48,.32,0,.08),(2.7,.60,.37,0,.07),(3.2,.62,.39,0,.04),(3.7,.69,.43,0,0),(4.15,.88,.46,0,0),(4.5,1.00,.43,0,.03),(4.75,.72,.35,0,.05),(4.92,.35,.29,0,.02)],skin)
body.scale.x=.90; body.scale.y=.84
uv('Powerful neck',(0,.03,4.98),(.37,.33,.55),skin)
right_arm_objects=[]
for side in [-1,1]:
    hip=(side*.44,.10,2.84); knee=(side*.62,-.03,1.67); ankle=(side*.76,-.01,.60)
    trouserv=[]; trouserf=[]; nr=35; ns=36
    for k in range(nr):
        t=k/(nr-1); z=2.86-2.28*t; cx=side*(.44+.32*t); cy=.10*(1-t)
        rad=.35-.17*t
        for j in range(ns):
            a=2*pi*j/ns
            envelope=math.exp(-((z-1.85)/.45)**2)
            wrinkle=envelope*(.014*sin(z*35+a*2.3)+.009*sin(z*58-a*3.1))
            rr=rad+wrinkle
            trouserv.append((cx+rr*cos(a),cy+rr*sin(a),z+.008*envelope*sin(a*4+z*5)))
    for k in range(nr-1):
        for j in range(ns):
            a=k*ns+j; b=k*ns+(j+1)%ns; trouserf.append((a,b,b+ns,a+ns))
    mesh('Wrinkled woven trouser leg',trouserv,trouserf,cloth_dark,1)
    # Upper arms are visible, sinewy and not covered by spherical armor.
    _arm_before=set(bpy.data.objects)
    shoulder=(side*.98,.02,4.55); elbow=(side*1.37,-.04,3.94); wrist=(side*1.56,-.27,3.25)
    parts=[uv('deltoid',shoulder,(.36,.34,.40),skin),uv('bicep',(side*1.19,-.005,4.27),(.29,.29,.44),skin),uv('elbow',elbow,(.23,.245,.27),skin),uv('forearm',(side*1.48,-.14,3.61),(.24,.235,.43),skin),uv('wrist',wrist,(.18,.18,.25),skin)]
    fuse('Sinewy arm '+str(side),parts,skin,.035)
    # Tendons, elbow folds and healed little abrasions.
    for off in [-.06,.045]:
        curve('Forearm tendon',[(side*(1.35+off),-.245,3.97),(side*(1.48+off),-.342,3.62),(side*(1.55+off),-.403,3.26)],.019,skin_hi)
    palm=(side*1.58,-.29,3.10)
    uv('Knuckled palm',palm,(.225,.185,.29),skin)
    for j in range(4):
        x=side*(1.405+j*.115); z=3.02-abs(j-1.4)*.025
        pts=[(x,-.39,z+.12),(x+side*.018,-.49,z-.035),(x+side*.026,-.48,z-.19),(x+side*.02,-.365,z-.225)]
        tube('Curled finger',pts,[.070,.075,.063,.04],skin,12,2)
        uv('Finger knuckle',(x,-.485,z+.015),(.075,.042,.065),skin_hi,24,16)
        for dz in [-.014,.015]:
            curve('Finger joint crease',[(x-.045,-.515,z+dz),(x,-.531,z+dz-.006),(x+.045,-.515,z+dz)],.0035,skin_dark)
        nail=uv('Dark tapered fingernail',(x+side*.02,-.39,z-.225),(.043,.025,.070),nail_mat,24,16)
    tube('Opposing thumb',[(side*1.39,-.27,3.21),(side*1.31,-.43,3.10),(side*1.38,-.53,2.99)],[.105,.09,.06],skin,16,2)
    if side==1: right_arm_objects.extend(set(bpy.data.objects)-_arm_before)

# ---------- A unified sculpted head ----------
_head_before=set(bpy.data.objects)
headparts=[]
def hs(name,loc,scale):
    o=uv(name,loc,scale,skin); headparts.append(o); return o
hs('Cranium',(0,.045,5.93),(.77,.61,.85))
hs('Occiput',(0,.20,5.72),(.68,.54,.66))
hs('Broad jaw',(0,-.18,5.24),(.59,.46,.37))
hs('Chin',(0,-.52,5.13),(.40,.29,.23))
hs('Lower face',(0,-.37,5.50),(.60,.43,.43))
for s in [-1,1]:
    cheek=hs('High angular cheekbone',(s*.53,-.44,5.65),(.29,.26,.31)); cheek.rotation_euler[1]=-s*.40
    hs('Lower orbital plane',(s*.39,-.51,5.83),(.28,.24,.135))
    hs('Temple',(s*.62,-.16,5.99),(.23,.36,.42))
    hs('Upper muzzle',(s*.22,-.72,5.43),(.30,.24,.19))
    brow=hs('Massive orbital brow',(s*.38,-.64,6.105),(.42,.32,.175)); brow.rotation_euler[1]=s*-.22
hs('Glabella',(0,-.58,6.11),(.22,.26,.31))
hs('Long nose bridge',(0,-.70,5.91),(.17,.27,.37))
hs('Hooked nose',(0,-.99,5.67),(.205,.32,.23))
hs('Hooked nose tip',(-.025,-1.105,5.605),(.14,.205,.16))
for s in [-1,1]: hs('Nasal ala',(s*.20,-.875,5.59),(.15,.19,.12))
head=fuse('HEAD • continuous voxel sculpt',headparts,skin,.022)
# Project micro-sculpt details onto the actual fused face, never floating in front.
bpy.context.view_layer.update()
head_eval=head.evaluated_get(bpy.context.evaluated_depsgraph_get())
head_inv=head.matrix_world.inverted()
flow=head.data.attributes.new('BloodFlow','FLOAT','POINT')
for v,d in zip(head.data.vertices,flow.data):
    x,y,z=head.matrix_world @ v.co
    nose=.55*math.exp(-((x/.26)**2+((z-5.63)/.31)**2+((y+1.10)/.31)**2))
    cheeks=.23*math.exp(-(((abs(x)-.53)/.24)**2+((z-5.65)/.22)**2+((y+.61)/.27)**2))
    d.value=nose+cheeks

def face_y(x,z,offset=.007):
    hit, loc, normal, index=head_eval.ray_cast(head_inv @ Vector((x,-3,z)),Vector((0,1,0)))
    return (head.matrix_world @ loc).y-offset if hit else -.45

def facial_curve(name,xz,radius,mat,offset=.007):
    # Dense surface sampling also follows the brow's steep relief changes.
    sampled=[]
    for a,b in zip(xz[:-1],xz[1:]):
        steps=max(2,math.ceil(math.dist(a,b)/.022))
        for k in range(steps):
            t=k/steps; x=a[0]*(1-t)+b[0]*t; z=a[1]*(1-t)+b[1]*t
            sampled.append((x,face_y(x,z,offset),z))
    x,z=xz[-1]; sampled.append((x,face_y(x,z,offset),z))
    return curve(name,sampled,radius,mat)


# Large swept ears with cupped interior geometry and thick cartilage rims.
for s in [-1,1]:
    outline=[(.58,.0,6.20),(.85,-.035,6.29),(1.20,.02,6.43),(1.70,.16,6.56),(1.55,.18,6.14),(1.28,.10,5.83),(.91,-.005,5.64),(.65,-.07,5.73)]
    outline=[(s*x,y,z) for x,y,z in outline]
    center=(s*1.05,.07,6.03)
    vs=[center]+outline+[(s*1.06,.25,6.05)]+[(x,y+.16,z) for x,y,z in outline]
    fs=[]; count=len(outline)
    for j in range(count):
        fs.append((0,1+j,1+(j+1)%count)); fs.append((9,10+(j+1)%count,10+j)); fs.append((1+j,10+j,10+(j+1)%count,1+(j+1)%count))
    mesh('Swept goblin ear',vs,fs,skin,2)
    inner=[(s*.77,-.066,6.09),(s*1.04,-.03,6.16),(s*1.53,.12,6.43),(s*1.28,.07,6.04),(s*.97,-.04,5.81)]
    mesh('Warm cupped ear interior',inner,[(0,1,2,3,4)],ear_mat,2)
    curve('Ear outer helix',[(s*.67,-.095,6.16),(s*.99,-.06,6.24),(s*1.35,.04,6.39),(s*1.68,.16,6.54)],.044,skin_hi)
    curve('Ear lower cartilage',[(s*1.65,.16,6.51),(s*1.40,.10,6.05),(s*1.09,-.05,5.82),(s*.79,-.17,5.80)],.042,skin)
    curve('Ear inner fork',[(s*.77,-.17,5.81),(s*.94,-.10,6.00),(s*1.23,.015,6.19)],.037,skin_hi)
    torus('Bronze ear hoop',(s*1.10,-.055,5.79),.13,.032,brass)
    uv('Piercing bead',(s*1.1,-.075,5.91),(.045,.042,.05),brass,24,16)

# Eyes: small spherical globes framed by heavy upper/lower lids.
for s in [-1,1]:
    x=s*.385; z=5.955
    uv('Golden eyeball',(x,-.648,z),(.221,.185,.132),eye_white,48,32)
    # Forward-facing iris, with radial stroma filaments and a narrow predator pupil.
    uv('Amber iris',(x+.025,-.825,z+.003),(.078,.026,.088),iris,40,24)
    torus('Dark limbal ring',(x+.025,-.829,z+.003),.081,.005,skin_dark)
    uv('Vertical slit pupil',(x+.025,-.852,z+.003),(.018,.012,.067),pupil,32,24)
    for k in range(25):
        a=2*pi*k/25
        curve('Iris radial fiber',[(x+.025+.041*cos(a),-.852,z+.003+.048*sin(a)),(x+.025+.069*cos(a),-.842,z+.003+.077*sin(a))],.0025,bone if k%4==0 else skin_dark)
    uv('Clear reflective corneal lens',(x+.025,-.841,z+.003),(.087,.042,.098),cornea,48,32)
    # Gentle, irregular almond shape, not circular spectacle-like sockets.
    upper=[(x-s*.225,-.687,z-.005),(x-s*.125,-.808,z+.055),(x,-.839,z+.065),(x+s*.15,-.79,z+.055),(x+s*.23,-.666,z-.02)]
    lower=[(x-s*.225,-.69,z-.005),(x-s*.11,-.795,z-.085),(x+s*.055,-.82,z-.095),(x+s*.19,-.735,z-.070),(x+s*.23,-.67,z-.02)]
    # A broad hood blends the lid into the brow, partially occluding the globe.
    lidverts=upper+[(xx,yy+.09,zz+.12) for xx,yy,zz in upper]
    mesh('Heavy upper eyelid hood',lidverts,[(i,i+1,i+6,i+5) for i in range(4)],skin,2)
    curve('Upper eyelid fleshy rim',upper,.030,skin)
    curve('Lower eyelid fleshy rim',lower,.028,skin_hi)
    curve('Lower orbital crease',[(x-s*.20,-.686,z-.11),(x,-.743,z-.21),(x+s*.22,-.615,z-.15)],.012,skin_dark)
    curve('Under eye bag',[(x-s*.15,-.711,z-.145),(x+s*.04,-.743,z-.18),(x+s*.24,-.603,z-.11)],.027,skin_hi)
    # Eyebrow hairs lie across the massive overhanging brow.
    for j in range(85):
        q=random.random(); xx=s*(.15+.49*q); zz=6.095+.12*q+random.uniform(-.014,.017)
        length=random.uniform(.028,.067)
        facial_curve('Irregular bristled eyebrow',[(xx,zz),(xx+s*length*.45,zz+.020),(xx+s*length,zz+.028+random.uniform(-.012,.015))],random.uniform(.0018,.0030),hair,.012)
    # Crow's feet and cheek planes.
    for j in range(3):
        curve('Orbital expression crease',[(s*.59,-.62,5.94-j*.035),(s*.68,-.53,5.95-j*.065),(s*.71,-.46,5.96-j*.09)],.008,skin_dark)
    # Real dark nostrils under a raised cartilage rim.
    o=uv('Inset nostril',(s*.17,-1.095,5.568),(.081,.030,.047),nostril,32,20); o.rotation_euler[1]=s*.22
    curve('Nostril wing',[(s*.081,-1.12,5.59),(s*.175,-1.125,5.625),(s*.25,-1.01,5.59)],.029,skin_hi)
    curve('Nose to mouth fold',[(s*.245,-.90,5.62),(s*.34,-.87,5.49),(s*.40,-.77,5.32)],.024,skin_hi)
    curve('Nasolabial crease',[(s*.27,-.88,5.59),(s*.38,-.84,5.45),(s*.43,-.74,5.31)],.010,skin_dark)

# Deep, slightly asymmetric mouth and thick sculpted lips.
curve('Mouth shadow',[(-.43,-.716,5.265),(-.27,-.866,5.30),(0,-.902,5.31),(.26,-.853,5.31),(.43,-.70,5.285)],.046,nostril)
curve('Lower lip',[(-.41,-.73,5.215),(-.24,-.875,5.24),(0,-.916,5.24),(.25,-.864,5.25),(.41,-.72,5.235)],.052,lip)
curve('Upper lip',[(-.41,-.743,5.30),(-.22,-.882,5.35),(0,-.922,5.35),(.21,-.88,5.36),(.41,-.74,5.32)],.032,lip)
curve('Philtrum left',[(-.077,-.944,5.51),(-.06,-.948,5.41),(-.10,-.931,5.36)],.017,skin_hi)
curve('Philtrum right',[(.077,-.944,5.51),(.06,-.948,5.41),(.10,-.931,5.36)],.017,skin_hi)
for s in [-1,1]:
    tube('Lower ivory tusk',[(s*.315,-.828,5.23),(s*.34,-.908,5.32),(s*.37,-.945,5.47),(s*.34,-.928,5.61)],[.079,.070,.044,.0015],bone,24,2)
    for j in range(3):
        curve('Tusk age groove',[(s*(.30+j*.016),-.90,5.29),(s*(.33+j*.014),-.95,5.42),(s*.34,-.933,5.56)],.0028,leather_edge)
# Fine forehead wrinkles follow the actual forehead surface.
for k in range(3):
    zz=6.36+k*.085
    xz=[(-.43,zz-.02),(-.22,zz+.015),(0,zz+.025),(.22,zz+.015),(.43,zz-.02)]
    facial_curve('Forehead furrow',xz,.0045,skin_dark,.004)
    facial_curve('Forehead wrinkle crest',[(x,z+.018) for x,z in xz],.009,skin_hi,.003)
for s in [-1,1]:
    facial_curve('Frown muscle',[(s*.11,6.12),(s*.12,6.28),(s*.17,6.37)],.013,skin_hi,.003)
    facial_curve('Frown cut',[(s*.069,6.15),(s*.075,6.29),(s*.11,6.37)],.004,skin_dark,.003)
# A pale healed slash crossing one eyebrow, interrupted at the eye.
facial_curve('Healed brow scar',[(.48,6.46),(.43,6.29),(.40,6.14)],.018,scar,.005)
facial_curve('Healed cheek scar',[(.37,5.78),(.34,5.68),(.29,5.57)],.014,scar,.006)
for j in range(4):
    z=6.20+j*.059; x=.41+(z-6.2)*.35
    facial_curve('Scar stitch impressions',[(x-.027,z+.012),(x+.027,z-.011)],.004,skin_dark,.005)
# Tiny relief details: cheek creases, chin cleft, and asymmetrical sun spots.
for side in [-1,1]:
    for j in range(4):
        facial_curve('Fine cheek skin crease',[(side*(.46+j*.025),5.53-j*.035),(side*(.51+j*.025),5.48-j*.03),(side*(.55+j*.025),5.45-j*.02)],.0035,skin_dark,.003)
facial_curve('Chin cleft',[(-.025,5.15),(-.01,5.11),(.016,5.095)],.006,skin_dark,.003)
for j in range(42):
    x=random.choice([-1,1])*random.uniform(.41,.63); z=random.uniform(5.53,5.77)
    rr=random.uniform(.004,.010)
    uv('Subtle cheek sun spot',(x,face_y(x,z,.004),z),(rr,.002,rr*.7),skin_dark,12,8)
# Sparse stubble on the jaw, small warts and follicles.
for j in range(42):
    a=random.uniform(pi*1.10,pi*1.90); z=random.uniform(5.02,5.17)
    x=.43*cos(a); y=-.35+.40*sin(a)
    curve('Chin stubble',[(x,y,z),(x+random.uniform(-.01,.01),y-.025,z-.035)],.0045,hair)
for x,y,z,r in [(-.53,-.655,5.58,.038),(-.57,-.60,5.53,.021),(.59,-.54,5.42,.024),(-.14,-1.255,5.69,.018)]:
    uv('Small skin wart',(x,y,z),(r,r*.6,r),skin_hi,24,16)
# Tied-back rough scalp ridge; silhouette remains distinct and goblin-like.
for k in range(9):
    y=.04+k*.065; z=6.67-.20*(k/8)**2
    tube('Swept scalp lock',[(-.11,y-.10,z-.06),(-.075,y,z+.08),(.015,y+.12,z+.13),(.08,y+.19,z+.035)],[.08,.085,.06,.005],hair,10,1)
# Short bound braid behind the ear line.
tube('Back braid core',[(.04,.61,6.36),(.08,.73,6.07),(.12,.73,5.80),(.15,.68,5.59)],[.11,.10,.075,.02],hair,16,2)
for k in range(6):
    z=6.30-k*.11
    uv('Overlapping braid lock',(.07+(-1)**k*.045,.73,z),(.08,.08,.09),hair,24,16)
torus('Braid bronze binding',(.14,.70,5.76),.075,.022,brass,rot=(0,0,0))

# A slight head cant and turn toward the lens gives the portrait a living gesture.
bpy.context.view_layer.update()
headpivot=Vector((0,.02,4.98))
headpose=Matrix.Translation(headpivot) @ Matrix.Rotation(.10,4,'Z') @ Matrix.Rotation(-.045,4,'Y') @ Matrix.Translation(-headpivot)
for ob in set(bpy.data.objects)-_head_before:
    ob.matrix_world=headpose @ ob.matrix_world

# ---------- Tailored torso armor, oxblood sash and skirt ----------
vest=loft('Fitted sleeveless leather cuirass',[(2.95,.64,.41,0,.04),(3.10,.67,.43,0,.04),(3.5,.69,.46,0,.015),(3.92,.79,.48,0,.005),(4.30,.91,.47,0,.025),(4.51,.91,.42,0,.04),(4.66,.64,.34,0,.05),(4.73,.37,.30,0,.03)],leather,64,2)
# Paneled front seams form tailored leather rather than a smooth tube.
for s in [-1,1]:
    pts=[(s*.19,-.40,3.12),(s*.28,-.45,3.52),(s*.39,-.463,4.0),(s*.49,-.399,4.44),(s*.27,-.283,4.69)]
    curve('Cuirass raised panel welt',pts,.024,leather_edge)
    for j in range(22):
        t=j/21; z=3.2+t*1.23; x=s*(.21+.26*t); y=-.46+.055*t*t
        curve('Saddle stitched cuirass',[(x-s*.035,y-.008,z-.017),(x+s*.032,y-.008,z+.017)],.008,thread)
    # Rolled neckline.
    curve('Rolled leather collar',[(0,-.29,4.76),(s*.27,-.32,4.70),(s*.55,-.29,4.62),(s*.78,-.14,4.59)],.042,leather_edge)
# X lacing down the central cuirass seam.
for j in range(9):
    z=3.37+j*.135
    for s in [-1,1]:
        torus('Lacing eyelet',(s*.085,-.492,z),.026,.009,brass)
    curve('Crossed leather chest lace',[(-.085,-.514,z),(.085,-.515,z+.12)],.013,leather_dark)
    curve('Crossed leather chest lace',[(.085,-.520,z),(-.085,-.520,z+.12)],.013,leather_dark)
# Broad diagonal cross-body strap, surface built as an actual ribbon.
strap_pts=[(-.76,-.22,4.58),(-.56,-.41,4.37),(-.30,-.51,4.10),(-.01,-.53,3.82),(.27,-.51,3.53),(.53,-.40,3.24)]
def ribbon(name,pts,width,mat):
    vs=[]
    for i,p in enumerate(pts):
        t=Vector(pts[min(i+1,len(pts)-1)])-Vector(pts[max(i-1,0)])
        q=Vector((t.z,0,-t.x)).normalized()*width*.5
        vs.extend([tuple(Vector(p)+q),tuple(Vector(p)-q)])
    fs=[(2*i,2*i+1,2*i+3,2*i+2) for i in range(len(pts)-1)]
    o=mesh(name,vs,fs,mat,2); so=o.modifiers.new('Thick saddle leather','SOLIDIFY'); so.thickness=.045
    return o,vs
strap,sv=ribbon('Diagonal weapon baldric',strap_pts,.23,leather_dark)
for parity in [0,1]: curve('Baldric edge piping',[sv[i] for i in range(parity,len(sv),2)],.013,leather_edge)
# Buckle sits on the shoulder-to-hip diagonal.
o=torus('Baldric oval bronze buckle',(-.27,-.562,4.08),.155,.028,brass); o.scale=(.86,1,1.2); o.rotation_euler[1]=-.74
curve('Baldric buckle tongue',[(-.36,-.59,3.99),(-.20,-.59,4.15)],.017,brass)
# Red wrapped waist band with uneven draped front cloth.
loft('Wrapped oxblood waist sash',[(2.86,.68,.44,0,.04),(2.94,.72,.465,0,.04),(3.06,.70,.47,0,.04),(3.17,.69,.455,0,.04),(3.24,.65,.43,0,.04)],cloth,64,2)
for k in range(4):
    pts=[]
    for j in range(22):
        a=pi+pi*j/21; pts.append((.706*cos(a),.04+.473*sin(a),2.92+k*.068+.018*sin(a*4+k)))
    curve('Compressed folds in wrapped sash',pts,.012,cloth_dark)
# Individually cut overlapping tassets, with a serrated, varied hem.
for k in range(9):
    a=2*pi*k/9
    a1=a-.36; a2=a+.36; bottom=2.20+.12*sin(k*2.4)
    vs=[]
    for z,rx,ry in [(2.99,.68,.45),(2.77,.79,.51),(bottom,.88,.57)]:
        for j in range(5):
            an=a1+(a2-a1)*j/4; vs.append((rx*cos(an),.05+ry*sin(an),z+(.025*sin(j*3+k) if z==bottom else 0)))
    fs=[(i*5+j,i*5+j+1,(i+1)*5+j+1,(i+1)*5+j) for i in range(2) for j in range(4)]
    o=mesh('Overlapping leather skirt tasset',vs,fs,leather,2); so=o.modifiers.new('Hide thickness','SOLIDIFY'); so.thickness=.045
    for jj in [0,4]: curve('Tasset stitched border',[vs[jj],vs[5+jj],vs[10+jj]],.014,leather_edge)
    for jj in [1,3]: rivet((.74*cos(a1+(a2-a1)*jj/4),.05+.49*sin(a1+(a2-a1)*jj/4),2.83),.035)
# Frayed central tabard with actual cloth undulations.
vs=[]; fs=[]; cols=14; rows=18
for j in range(rows):
    t=j/(rows-1); width=.30+.11*t
    for i in range(cols):
        u=i/(cols-1); x=(u-.5)*width*2-.11*t
        z=3.03-1.02*t+(t**8)*(.06*sin(u*21)+.025*sin(u*49))
        y=-.49-.12*t-.035*sin(u*6*pi+t*2)*(.3+t)
        vs.append((x,y,z))
for j in range(rows-1):
    for i in range(cols-1):
        a=j*cols+i; fs.append((a,a+1,a+1+cols,a+cols))
o=mesh('Draped oxblood tabard',vs,fs,cloth,2); so=o.modifiers.new('Woven cloth thickness','SOLIDIFY'); so.thickness=.019
for s in [0,cols-1]: curve('Tabard woven edging',[vs[j*cols+s] for j in range(rows)],.012,thread)
# Stitched geometric motif at the tabard hem.
for off in [-.20,0,.20]:
    curve('Tabard embroidered chevron',[(off-.10,-.67,2.35),(off,-.68,2.25),(off+.10,-.67,2.35)],.012,thread)
# Utility belt crosses over the sash.
loft('Heavy equipment belt',[(2.97,.727,.489,0,.04),(3.00,.745,.503,0,.04),(3.18,.72,.491,0,.04),(3.21,.703,.47,0,.04)],leather_dark,64,1)
for zz in [3.02,3.17]:
    curve('Belt edge seam',[(.745*cos(pi+pi*j/32),.04+.511*sin(pi+pi*j/32),zz) for j in range(33)],.009,thread)
# Rectangular buckle made from four rounded forged pieces.
for x in [-.165,.165]: cube('Bronze belt buckle',(x,-.522,3.106),(.045,.06,.235),brass,.018)
for z in [2.99,3.22]: cube('Bronze belt buckle',(0,-.522,z),(.35,.06,.045),brass,.018)
link('Buckle pin',(-.02,-.563,3.08),(.145,-.563,3.08),.016,.016,brass)
for k in range(4): rivet((.30+k*.105,-.49+.10*k/4,3.105),.018,nostril)

# ---------- Asymmetric armor and fur mantle ----------
# One hand-hammered shoulder plate, developed over an ellipsoidal cap.
vs=[]; fs=[]; rn=11; an=32
for i in range(rn):
    t=.08+(pi*.56-.08)*i/(rn-1)
    for j in range(an):
        a=2*pi*j/an
        vs.append((1.00+.54*sin(t)*cos(a),.03+.49*sin(t)*sin(a),4.58+.49*cos(t)))
for i in range(rn-1):
    for j in range(an):
        a=i*an+j; b=i*an+(j+1)%an; fs.append((a,b,b+an,a+an))
o=mesh('Single forged iron pauldron',vs,fs,steel,1); so=o.modifiers.new('Armor plate thickness','SOLIDIFY'); so.thickness=.065
curve('Rolled steel pauldron rim',[vs[(rn-1)*an+j] for j in range(an)]+[vs[(rn-1)*an]],.039,edge)
for j in range(0,an,4):
    p=Vector(vs[(rn-2)*an+j]); p.y-=.02; rivet(tuple(p),.044,brass)
# Three conical armor spikes, curved and individually socketed.
for x,y,z,h in [(1.0,.03,5.04,.40),(1.32,.03,4.95,.33),(.77,.03,4.99,.28)]:
    torus('Spike welded socket',(x,y,z),.09,.024,edge,(0,0,0))
    tube('Forged pauldron spike',[(x,y,z),(x+.05,y,z+h*.58),(x+.13,y+.025,z+h)],[.095,.056,.001],steel,16,1)
# Decorative bronze inlay and scrapes across the front of the plate.
curve('Pauldron inlaid broken chevron',[(.72,-.405,4.83),(.99,-.46,4.68),(1.30,-.36,4.81)],.019,brass)
for j in range(9):
    x=.76+j*.062
    curve('Bright battle scratches',[(x,-.442,4.72+(j%3)*.035),(x+.055,-.44,4.78+(j%3)*.035)],.004,edge)
# Segmented descending lame on outside of shoulder.
for k in range(2):
    o=cube('Articulated shoulder lame',(1.38+k*.035,.015,4.42-k*.17),(.36,.64,.22),steel,.09)
    o.rotation_euler[1]=-.22
    rivet((1.40+k*.035,-.32,4.43-k*.17),.047)
# Opposite shoulder has a dense shaggy mantle: layered angular fur locks.
uv('Fur mantle foundation',(-.82,.08,4.68),(.60,.44,.245),fur_dark)
furverts=[]; furfaces=[]; furmats=[]
for k in range(3200):
    a=random.uniform(0,2*pi); ph=math.acos(random.uniform(.04,1))
    root=Vector((-.82+.607*sin(ph)*cos(a),.08+.447*sin(ph)*sin(a),4.68+.25*cos(ph)))
    length=random.uniform(.10,.25)
    direction=Vector((cos(a)*(.4+sin(ph)),sin(a)*(.4+sin(ph)),-.55-.65*sin(ph))).normalized()
    mid=root+direction*length*.55+Vector((0,0,.018))
    tip=root+direction*length
    tangent=direction; axis=tangent.cross(Vector((0,0,1))).normalized(); other=tangent.cross(axis).normalized()
    base=len(furverts); r=random.uniform(.003,.006)
    for p,rr in [(root,r),(mid,r*.7),(tip,.0003)]:
        for j in range(5): furverts.append(tuple(p+rr*(axis*cos(2*pi*j/5)+other*sin(2*pi*j/5))))
    for q in range(2):
        for j in range(5):
            furfaces.append((base+q*5+j,base+q*5+(j+1)%5,base+(q+1)*5+(j+1)%5,base+(q+1)*5+j)); furmats.append(k%3)
fo=mesh('Thousands of tapered mantle guard hairs',furverts,furfaces,fur)
fo.data.materials.append(fur_dark); fo.data.materials.append(leather_edge)
for poly,mi in zip(fo.data.polygons,furmats): poly.material_index=mi
# Bronze clasp and hanging hunter's charms.
torus('Mantle clasp',(-.61,-.40,4.57),.14,.035,brass)
uv('Clasp dark inset',(-.61,-.405,4.57),(.10,.025,.10),steel,32,20)
curve('Charm suspension cord',[(-.80,-.38,4.58),(-.98,-.49,4.40),(-.90,-.51,4.15)],.016,leather_dark)
for k in range(3):
    x=-.97+k*.09; z=4.20+abs(k-1)*.04
    tube('Hanging trophy fang',[(x,-.51,z+.10),(x-.025,-.53,z),(x+.01,-.54,z-.17)],[.045,.045,.001],bone,16,2)
    torus('Trophy binding',(x,-.515,z+.085),.047,.012,brass,(0,0,0))

# ---------- Bracers, boots, pouches ----------
for s in [-1,1]:
    _bracer_before=set(bpy.data.objects)
    # A tapered leather cuff follows each sloping forearm.
    a=Vector((s*1.43,-.105,3.77)); b=Vector((s*1.56,-.25,3.32))
    link('Leather vambrace',a,b,.255,.205,leather_dark)
    for t in [.10,.85]:
        c=a.lerp(b,t); link('Bracer retaining strap',c-Vector((s*.012,-.015,.045)),c+Vector((s*.012,-.015,.045)),.268-(t*.05),.268-(t*.05),leather_edge)
    # Raised front iron splint, flanked by real stitch holes.
    plate=cube('Forearm iron splint',(s*1.50,-.355,3.56),(.27,.07,.43),steel,.07); plate.rotation_euler[1]=s*-.18
    for dz in [-.14,.14]: rivet((s*1.5,-.403,3.56+dz),.035)
    for dz in [-.18,-.09,0,.09,.18]:
        for dx in [-.16,.16]: curve('Bracer stitch',[(s*1.5+dx,-.322,3.55+dz),(s*1.5+dx+.025,-.323,3.57+dz)],.007,thread)
    if s==1: right_arm_objects.extend(set(bpy.data.objects)-_bracer_before)
    # Soft turned boot with reinforced heel, toe and layered sole.
    x=s*.75
    uv('Boot rounded toe',(x,-.29,.30),(.32,.57,.265),leather_dark)
    uv('Boot heel',(x,.115,.29),(.28,.28,.27),leather_dark)
    loft('Tall folded boot',[(.25,.285,.29,x,.02),(.47,.27,.28,x,.025),(.80,.24,.255,x,.03),(1.12,.275,.28,x-s*.04,.015),(1.40,.30,.29,x-s*.08,0),(1.48,.32,.30,x-s*.09,0)],leather,40,2)
    # Sole perimeter follows an elongated footprint.
    for z in [.12,.18]:
        curve('Layered boot sole',[(x+.315*cos(2*pi*j/48),-.19+.54*sin(2*pi*j/48),z) for j in range(49)],.034,leather_dark)
    curve('Boot welt stitches',[(x+.325*cos(pi+pi*j/32),-.19+.55*sin(pi+pi*j/32),.215) for j in range(33)],.009,thread)
    # Knee/shin guard with pointed silhouette and rolled edging.
    cx=x-s*.055
    v=[(cx-.24,-.255,1.42),(cx,-.335,1.59),(cx+.24,-.255,1.42),(cx+.20,-.36,.78),(cx,-.40,.62),(cx-.20,-.36,.78),(cx,-.43,1.15)]
    f=[(0,1,6),(1,2,6),(2,3,6),(3,4,6),(4,5,6),(5,0,6)]
    o=mesh('Faceted iron greave',v,f,steel,0)
    so=o.modifiers.new('Greave plate thickness','SOLIDIFY'); so.thickness=.055
    be=o.modifiers.new('Greave softened edges','BEVEL'); be.width=.035; be.segments=3
    curve('Greave edge band',v[:6]+[v[0]],.023,edge)
    curve('Greave central ridge',[(cx,-.36,1.5),(cx,-.452,1.15),(cx,-.42,.68)],.015,edge)
    for dz in [.86,1.36]:
        curve('Boot retention straps',[(cx-.27,-.18,dz),(cx-.20,-.38,dz),(cx+.20,-.38,dz),(cx+.27,-.18,dz)],.045,leather_dark)
        rivet((cx+s*.20,-.415,dz),.040)
    # Boot top cuff and folded creases.
    for z in [1.43,1.50]:
        curve('Turned boot cuff',[(x-s*.09+.32*cos(2*pi*j/32),.31*sin(2*pi*j/32),z) for j in range(33)],.035,leather_dark)
    for j in range(4):
        curve('Ankle leather wrinkles',[(x-.23,-.24,.44+j*.055),(x,-.30,.42+j*.055),(x+.23,-.24,.46+j*.055)],.015,leather_edge)
# Side satchel, attached behind the belt, with flap and little buckle.
uv('Belt pouch body',(.78,-.035,2.92),(.28,.26,.37),leather)
o=cube('Pouch flap',(.79,-.252,3.04),(.47,.075,.31),leather_edge,.10)
curve('Pouch flap stitched border',[(.59,-.302,3.15),(.58,-.31,2.96),(.80,-.32,2.89),(.99,-.29,2.97),(.99,-.29,3.15)],.009,thread)
cube('Pouch buckle strap',(.79,-.31,2.98),(.09,.035,.31),leather_dark,.025)
torus('Pouch buckle',(.79,-.348,3.0),.064,.014,brass)
# Rolled blanket on rear hip, visible at the silhouette.
link('Bedroll',(-.63,.43,3.20),(.47,.43,3.20),.24,.24,cloth_dark)
for x in [-.43,.27]: torus('Bedroll leather tie',(x,.43,3.20),.247,.027,leather_edge,(0,pi/2,0))
# Knife on opposite hip, with carved hilt and metal throat.
a=Vector((-.71,-.04,3.16)); b=Vector((-.93,-.04,2.26))
link('Dagger leather sheath',a,b,.125,.06,leather_dark)
link('Dagger exposed handle',(-.70,-.04,3.18),(-.60,-.04,3.63),.085,.08,leather_edge)
link('Dagger cross guard',(-.90,-.04,3.18),(-.48,-.04,3.18),.045,.045,brass)
uv('Dagger bronze pommel',(-.59,-.04,3.64),(.11,.09,.08),brass)
for k in range(6):
    torus('Dagger hilt winding',(-.69+k*.018,-.04,3.23+k*.065),.087,.012,leather_dark,(0,.22,0))

# ---------- Lowered executioner's axe ----------
# Grip through the left fist. Axe is canted outwards and clear of the feet.
A=Vector((-1.54,-.39,3.43)); B=Vector((-2.24,-.45,.61)); direction=(A-B).normalized()
link('Axe ashwood haft',B,A,.067,.073,leather_edge)
# Add long irregular wood grain, not texture-only, along the haft.
for j in range(8):
    angle=2*pi*j/8
    shift=Vector((.065*cos(angle),.065*sin(angle),0))
    curve('Axe haft longitudinal grain',[tuple(B+direction*.12+shift),tuple(B.lerp(A,.36)+shift*1.05),tuple(B.lerp(A,.68)+shift),tuple(A-direction*.09+shift)],.004,leather_dark)
for k in range(12):
    c=A-direction*(.09+k*.036)
    o=torus('Axe grip leather winding',c,.077,.012,leather_dark,(0,0,0)); o.rotation_euler=direction.to_track_quat('Z','Y').to_euler()
# Axe head is forged as a solid wedge with a swept broad cutting edge.
# Profile in world X/Z; thickness provides a visibly sharpened silver bevel.
profile=[(-2.10,1.42),(-2.44,1.48),(-2.77,1.77),(-3.00,1.66),(-3.07,1.30),(-2.95,.93),(-2.67,.80),(-2.47,1.07),(-2.17,1.11)]
vs=[(x,y,z) for y in [-.54,-.32] for x,z in profile]; n=len(profile)
fs=[tuple(range(n-1,-1,-1)),tuple(n+j for j in range(n))]+[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
o=mesh('Solid forged axe head',vs,fs,steel)
be=o.modifiers.new('Forged softened arrises','BEVEL'); be.width=.045; be.segments=3
no=o.modifiers.new('Weighted axe normals','WEIGHTED_NORMAL')
# Polished bevel strip runs along the broad outer blade.
outer=[(-2.77,1.77),(-3.0,1.66),(-3.07,1.30),(-2.95,.93),(-2.67,.80)]
inner=[(-2.70,1.64),(-2.87,1.57),(-2.94,1.30),(-2.83,1.04),(-2.61,.94)]
vs=[(x,-.566,z) for x,z in outer]+[(x,-.57,z) for x,z in inner]
mesh('Sharpened axe bevel',vs,[(j,j+1,j+6,j+5) for j in range(4)],edge)
link('Axe socket collar',(-2.15,-.43,1.08),(-2.05,-.43,1.49),.13,.13,steel)
for z in [1.15,1.43]: rivet((-2.18,-.575,z),.045,brass)
# Bronze maker's sigil and etched runes cut across dark iron.
curve('Axe maker sigil',[(-2.44,-.574,1.19),(-2.58,-.574,1.30),(-2.44,-.574,1.43),(-2.32,-.574,1.30),(-2.44,-.574,1.19)],.014,brass)
curve('Axe maker sigil stem',[(-2.44,-.577,1.12),(-2.44,-.577,1.48)],.010,brass)
for k in range(13):
    x=random.uniform(-2.80,-2.50); z=random.uniform(1.10,1.56)
    curve('Axe blade surface scoring',[(x,-.576,z),(x-.05,-.575,z-.055)],.0035,edge)
link('Axe haft metal butt',B-direction*.03,B+direction*.14,.092,.092,steel)

# Bend the free arm inward at the elbow: a relaxed, confident hand-on-belt pose.
# Meshes and actual leather/metal accessories share the same articulated gesture.
bpy.context.view_layer.update()
hinge=Vector((1.37,-.04,3.94))
def posed(point):
    weight=max(0,min(1,(4.20-point.z)/.25)); weight=weight*weight*(3-2*weight)
    rot=Matrix.Rotation(.85*weight,4,'Y') @ Matrix.Rotation(-.15*weight,4,'X')
    return hinge+rot.to_3x3() @ (point-hinge)
for ob in right_arm_objects:
    mw=ob.matrix_world.copy(); inv=mw.inverted()
    if ob.type=='MESH':
        for v in ob.data.vertices: v.co=inv @ posed(mw @ v.co)
        ob.data.update()
    elif ob.type=='CURVE':
        for sp in ob.data.splines:
            for bp in sp.bezier_points:
                bp.co=inv @ posed(mw @ bp.co)

# ---------- Studio: neutral sweep, sculptural three-point illumination ----------
mat_floor=material('24 • neutral gray studio',(.215,.215,.215),.83)
bpy.ops.mesh.primitive_plane_add(size=2000,location=(0,0,.055)); floor=bpy.context.object; floor.name='Seamless neutral gray cyclorama'; floor.data.materials.append(mat_floor)
world=bpy.data.worlds.new('Neutral studio ambient'); bpy.context.scene.world=world; world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.215,.215,.215,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.32

def area(name,loc,power,color,size,target):
    bpy.ops.object.light_add(type='AREA',location=loc); o=bpy.context.object; o.name=name
    o.data.energy=power; o.data.color=color; o.data.shape='DISK'; o.data.size=size
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler(); return o
area('KEY • large warm softbox',(-5,-8,11),1300,(1.0,.86,.70),5.0,(0,0,3.8))
area('FILL • cool frontal softbox',(6,-5,6),650,(.68,.81,1.0),4.5,(0,0,3.7))
area('RIM • high rear strip',(2,4,9),1700,(1.0,.92,.77),3.5,(0,0,4.0))
bpy.ops.object.camera_add(location=(8.0,-23.5,8.25)); camera=bpy.context.object; camera.name='Hero portrait • 70mm'
target=Vector((-.25,0,3.43)); camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler(); camera.data.type='PERSP'; camera.data.lens=66
camera.data.dof.use_dof=False
scene=bpy.context.scene; scene.camera=camera
scene.render.engine='CYCLES'; scene.cycles.samples=40 if PREVIEW else 192
scene.cycles.use_denoising=True; scene.cycles.adaptive_threshold=.025 if PREVIEW else .008
scene.cycles.max_bounces=8; scene.cycles.diffuse_bounces=3; scene.cycles.glossy_bounces=4
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='OPTIX'; prefs.get_devices()
    for d in prefs.devices: d.use=(d.type=='OPTIX')
    if any(d.type=='OPTIX' for d in prefs.devices): scene.cycles.device='GPU'
except Exception as e: print('GPU unavailable, using CPU:',e)
scene.render.resolution_x=1920; scene.render.resolution_y=1080
scene.render.resolution_percentage=50 if PREVIEW else 100
scene.render.image_settings.file_format='PNG'; scene.render.image_settings.color_mode='RGBA'; scene.render.image_settings.color_depth='8'
scene.render.film_transparent=False
scene.view_settings.view_transform='AgX'; scene.view_settings.look='AgX - Medium High Contrast'; scene.view_settings.exposure=.0
scene.render.filepath=os.path.join(OUT,'preview.png' if PREVIEW else 'render.png')
# Mild bloom only on bright specular highlights, no photographic overlays.
scene.use_nodes=True; nt=scene.node_tree; nt.nodes.clear()
rl=nt.nodes.new('CompositorNodeRLayers'); gl=nt.nodes.new('CompositorNodeGlare'); gl.glare_type='FOG_GLOW'; gl.quality='HIGH'; gl.threshold=2.5
comp=nt.nodes.new('CompositorNodeComposite'); nt.links.new(rl.outputs['Image'],gl.inputs['Image']); nt.links.new(gl.outputs['Image'],comp.inputs['Image'])
print('BRAMBLE scene ready:',len(bpy.data.objects),'objects. Rendering',scene.render.filepath,flush=True)
bpy.ops.render.render(write_still=True)
print('BRAMBLE render complete.',flush=True)
