"""Fix pass on the delivered 45cb5d8 scene, not a source rebuild.

ASSEMBLY_BASELINE must name the original delivered snake-sectional.blend.
FIX_STAGE=wip skips the final module/tail silhouette additions.
"""
import bpy, bmesh, math, os, json
import numpy as np
from mathutils import Vector, Matrix
from math import pi, sin, cos
from pathlib import Path

O = Path(os.environ['ASSEMBLY_OUTPUT'])
baseline = os.environ['ASSEMBLY_BASELINE']
final = os.environ.get('FIX_STAGE', 'final') == 'final'
bpy.ops.wm.open_mainfile(filepath=baseline)
sc = bpy.context.scene
head = bpy.data.objects['Head']
body = bpy.data.objects['Segment_00']
tail = bpy.data.objects['Tail']
eyes = [o for o in head.children if o.type == 'MESH']
lens_baseline = {o.name: {'vertices': [list(v.co) for v in o.data.vertices],
                         'matrix': [list(r) for r in o.matrix_basis]} for o in eyes}

def select(o):
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o

def triangulate(o):
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(o.data); bm.free(); o.data.update()

def tris(o):
    o.data.calc_loop_triangles()
    return len(o.data.loop_triangles)

def reduce(o, target):
    select(o)
    m = o.modifiers.new('Fix-pass budget reallocation', 'DECIMATE')
    m.ratio = min(1.0, target / tris(o))
    bpy.ops.object.modifier_apply(modifier=m.name)
    triangulate(o)

def mat(name, color, metal=.85, rough=.32):
    m = bpy.data.materials.new(name); m.use_nodes = True
    bs = m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (*color, 1)
    bs.inputs['Metallic'].default_value = metal
    bs.inputs['Roughness'].default_value = rough
    return m

steel = mat('Fix machined edges', (.28,.31,.33), .9, .29)
carbon = mat('Fix recessed carbon', (.014,.020,.023), .8, .4)
armor = head.data.materials[0]

def mesh(name, vertices, faces, material):
    me = bpy.data.meshes.new(name); me.from_pydata(vertices, [], faces); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o)
    me.materials.append(material)
    return o

def plate(name, points, normal, thickness=.025, bevel=.008, material=None):
    """Closed, planar, clipped polygon with a one-step machined perimeter."""
    n = Vector(normal).normalized(); ps = [Vector(p) for p in points]; N = len(ps)
    o = mesh(name, [p-n*thickness for p in ps]+ps,
             [tuple(reversed(range(N))), tuple(range(N,2*N))] +
             [(i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N)], material or armor)
    # Correct winding before bevel; the section's explicit normal determines outward.
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
    if bevel:
        select(o); m=o.modifiers.new('Crisp manufactured edge','BEVEL');m.width=bevel;m.segments=1
        bpy.ops.object.modifier_apply(modifier=m.name)
    triangulate(o)
    return o

def box(name, loc, scale, material):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o=bpy.context.object;o.name=name
    # Geometry is always in the receiving section's local coordinates.
    o.data.transform(Matrix.Translation(Vector(loc)) @ Matrix.Diagonal((*scale,1)))
    o.data.materials.append(material)
    return o

def join_local(base, additions):
    """Join local-space additions without disturbing section origins or children."""
    saved=base.matrix_world.copy();base.matrix_world=Matrix.Identity(4)
    bpy.context.view_layer.update()
    select(base)
    for o in additions:o.select_set(True)
    bpy.ops.object.join()
    base.matrix_world=saved
    bpy.context.view_layer.update()

# Retain the delivered skull, but flatten thick source fin tips under new thin fins.
for v in head.data.vertices:
    if v.co.z > .44:v.co.z=.44
bm=bmesh.new();bm.from_mesh(head.data)
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.0001)
bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.0001)
bm.to_mesh(head.data);bm.free()
reduce(head, 8300)
for p in head.data.polygons:p.use_smooth=True

hp=[]
# Source-fitted angular muzzle, jaw, temple, and brow overlays. None intersects the lens.
for side in [-1,1]:
    def sideplate(name, outline, yfun, bevel=.008):
        return plate(name, [(x, side*yfun(x,z),z) for x,z in outline],
                     (0,side,0),.028,bevel)
    hp.append(sideplate('Angular lower jaw',
        [(-1.45,-.34),(-1.28,-.47),(-.40,-.50),(-.09,-.39),(-.12,-.29),(-1.31,-.28)],
        lambda x,z:.32+(x+1.45)*.17))
    hp.append(sideplate('Chamfered snout armor',
        [(-1.54,-.26),(-1.53,-.08),(-1.33,.12),(-1.18,.10),(-1.19,-.20),(-1.32,-.29)],
        lambda x,z:.32+(x+1.50)*.28))
    hp.append(sideplate('Temple armor',
        [(-.69,.26),(-.54,.40),(-.11,.39),(-.045,.29),(-.06,.06),(-.61,.06)],
        lambda x,z:.60+(x+.69)*.26))
    hp.append(sideplate('Boxy cheek armor',
        [(-.68,-.20),(-.60,.025),(-.11,.025),(-.04,-.08),(-.13,-.255),(-.55,-.27)],
        lambda x,z:.67+(x+.68)*.16))
    hp.append(sideplate('Angular lens brow',
        [(-1.16,.25),(-1.08,.36),(-.75,.40),(-.67,.29),(-.75,.23),(-1.10,.23)],
        lambda x,z:.41+(x+1.16)*.19))
    # A real rectangular vent frame and parallel metal vanes over a dark recess.
    hp.append(box('Cheek vent dark well',(-.36,side*.765,-.105),(.31,.045,.19),carbon))
    for x,z,sx,sz in [(-.36,.002,.35,.028),(-.36,-.212,.35,.028),
                       (-.55,-.105,.028,.235),(-.17,-.105,.028,.235)]:
        hp.append(box('Cheek vent square rim',(x,side*.795,z),(sx,.035,sz),steel))
    for i in range(6):
        hp.append(box('Cheek grille vane',(-.50+i*.054,side*.801,-.105),(.014,.028,.17),steel))

# Three source-positioned thin crest fins with a sharp swept-back manufactured profile.
for y in [-.39,0,.39]:
    hp.append(plate('Thin crest fin', [(-.73,y,.43),(-.49,y,.91),(-.08,y,1.015),
                    (-.12,y,.84),(-.36,y,.43)], (0,-1,0), .035,.006))
    hp.append(box('Crest bolted foot',(-.38,y-.014,.447),(.55,.085,.042),armor))

join_local(head,hp)

# Clean the source-sampled shared module without replacing its rigid section mesh.
# Clamp only shell vertices (first 13 x 36 in the delivered retopology); hardware stays.
for v in body.data.vertices[:468]:
    x,y,z=v.co; a=math.atan2(z,y); r=math.hypot(y,z)
    # A faceted barrel with planar longitudinal shell bands, not a melted sphere.
    q=(a+pi/12)%(pi/6)-pi/12
    angular=.467/math.cos(q)
    barrel=1-.065*(abs(x)/.48)**4
    nr=angular*barrel + .06*(r-.47)
    v.co.y=nr*cos(a);v.co.z=nr*sin(a)
body.data.update()
if final:
    bp=[]
    # Four low-cost overlapping shoulders, 24 triangles each. One shared module.
    for a in [pi/4,3*pi/4,5*pi/4,7*pi/4]:
        verts=[]
        for x,r in [(-.32,.484),(.16,.492),(.23,.48)]:
            for t in [a-.30,a+.30]:verts.append((x,r*cos(t),r*sin(t)))
        bp.append(mesh('Layered shell shoulder',verts,[(0,1,3,2),(2,3,5,4)],armor))
    # Pair of actual longitudinal hydraulic rods in the side recesses.
    for sy in [-1,1]:
        bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=.026,depth=.29,rotation=(0,pi/2,0))
        o=bpy.context.object;bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
        o.data.transform(Matrix.Translation(Vector((-.18,sy*.474,-.16))))
        o.data.materials.append(steel);bp.append(o)
    # Joining a shared datablock requires reconnecting every rigid instance afterwards.
    old=body.data
    others=[o for o in bpy.data.objects if o.type=='MESH' and o.data==old and o!=body]
    join_local(body,bp)
    for o in others:o.data=body.data

# Keep the original tail section and attachment; sharpen and extend only its distal run.
reduce(tail,1900)
if final:
    for v in tail.data.vertices:
        t=max(0,min(1,(v.co.x-1.15)/1.38))
        v.co.x+=.62*t
        # Thin distal silhouette; do not scale/move its attachment frame.
        v.co.y*=1-.16*t;v.co.z=-.11+(v.co.z+.11)*(1-.16*t)
    tp=[]
    for sy in [-1,1]:
        tp.append(plate('Tail blade fin',[(1.72,sy*.21,.12),(2.02,sy*.26,.48),
                  (2.60,sy*.32,.29),(2.27,sy*.26,.09)],(0,sy,0),.024,.004))
    join_local(tail,tp)

# Tighten existing twelve sector inserts, preserving the original triangle count.
# Do not alter shared emitter material: the delivered lens must remain exact.
jointmat=bpy.data.materials['Teal joint emitters'].copy();jointmat.name='Recessed saturated teal joint emission'
bs=jointmat.node_tree.nodes.get('Principled BSDF')
bs.inputs['Base Color'].default_value=(.003,.30,.235,1)
bs.inputs['Emission Color'].default_value=(.005,.80,.60,1)
bs.inputs['Emission Strength'].default_value=5
housemat=mat('Dark recessed joint housing',(.008,.014,.017),.86,.37)
seen=set()
for o in bpy.data.objects:
    if 'GlowBars' in o.name and o.type=='MESH':
        if o.data not in seen:
            seen.add(o.data)
            for v in o.data.vertices:
                a=math.atan2(v.co.z,v.co.y)%(2*pi);sector=int(a/(2*pi/12));mid=(sector+.5)*2*pi/12
                a=mid+(a-mid)*((pi/12-.009)/(pi/12-.045))
                r=math.hypot(v.co.y,v.co.z);v.co.y=r*cos(a);v.co.z=r*sin(a)
            o.data.materials.clear();o.data.materials.append(jointmat)
    elif ('_Housing' in o.name) and o.type=='MESH':
        if o.data not in seen:
            seen.add(o.data);o.data.materials.clear();o.data.materials.append(housemat)

def atlas(o,kind,size):
    """Rasterize section-local surface coordinates to UV0, then manufacture PBR maps.

    No generative image edits and no lighting/AO multiplied into base color.
    Fasteners, stepped panel edges, diamond mesh and directional scuffs share a
    deterministic local coordinate field, not unrelated image-space noise.
    """
    print('ATLAS_START',kind,flush=True)
    select(o);triangulate(o)
    # Consolidate only the section armor. Keep real rods, grille and carbon hardware.
    oldm=list(o.data.materials)
    armor_indices={i for i,m in enumerate(oldm) if m and ('Gunmetal' in m.name)}
    if kind=='segment2':armor_indices.add(0)
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=.75,island_margin=.008)
    bpy.ops.object.mode_set(mode='OBJECT')
    uv=o.data.uv_layers.active.data
    pos=np.zeros((size,size,3),np.float32);normal=np.zeros_like(pos);mask=np.zeros((size,size),bool)
    for p in o.data.polygons:
        if p.material_index not in armor_indices:continue
        loops=list(p.loop_indices);ps=np.array([o.data.vertices[o.data.loops[i].vertex_index].co[:] for i in loops])
        tex=np.array([uv[i].uv[:] for i in loops])*size-.5
        lo=np.maximum(0,np.floor(tex.min(0)).astype(int));hi=np.minimum(size-1,np.ceil(tex.max(0)).astype(int))
        if np.any(hi<lo):continue
        yy,xx=np.mgrid[lo[1]:hi[1]+1,lo[0]:hi[0]+1];v0=tex[1]-tex[0];v1=tex[2]-tex[0]
        den=v0[0]*v1[1]-v1[0]*v0[1]
        if abs(den)<1e-10:continue
        dx=xx-tex[0,0];dy=yy-tex[0,1]
        b=(dx*v1[1]-v1[0]*dy)/den;c=(v0[0]*dy-dx*v0[1])/den;a=1-b-c
        inside=(a>=-.015)&(b>=-.015)&(c>=-.015)
        region=pos[lo[1]:hi[1]+1,lo[0]:hi[0]+1]
        region[inside]=(a[...,None]*ps[0]+b[...,None]*ps[1]+c[...,None]*ps[2])[inside]
        normal[lo[1]:hi[1]+1,lo[0]:hi[0]+1][inside]=p.normal[:]
        mask[lo[1]:hi[1]+1,lo[0]:hi[0]+1]|=inside
    x,y,z=pos.transpose(2,0,1)
    if kind=='segment2':
        u=x+.56;v=np.arctan2(z,y)*.48
        # Shallow stepped seam jogs in a manufactured wraparound shell.
        u+=.055*(np.mod(v+.15,.50)>.31)
        su=.45;sv=.50
    elif kind=='head':
        top=np.abs(normal[:,:,2])>np.abs(normal[:,:,1])
        u=x+1.60;v=np.where(top,y+.9,z+.65)
        su=.34;sv=.25
        u+=.055*(np.mod(v,sv)>.15)
    else:
        u=x;v=y+.98;su=.245;sv=.24
        u+=.045*(np.mod(v,sv)>.15)
    fu=np.mod(u,su);fv=np.mod(v,sv)
    edge=np.minimum(np.minimum(fu,su-fu),np.minimum(fv,sv-fv))
    cellu=np.floor(u/su);cellv=np.floor(v/sv)
    h=np.mod(np.sin(cellu*127.1+cellv*311.7)*43758.5453,1)
    # Large, calm worn-gunmetal regions. Fine noise is restrained, not stone texture.
    macro=(np.sin(x*21+y*17+z*12)*np.sin(z*27-y*8)+1)*.5
    fine=np.mod(np.sin(x*1721.1+y*2371.3+z*1937.7)*7819.2,1)
    value=.25+.15*h+.026*macro+.008*fine
    seam=edge<.0048;bevel=(edge>=.0048)&(edge<.011)
    value=np.where(seam,.022,value)
    value=np.where(bevel,.49+.08*macro,value)
    height=np.where(seam,-.0014,np.where(bevel,.00035,0.))
    # Recessed hex-headed fasteners at panel corners, with a narrow machined rim.
    du=np.minimum(abs(fu-.030),abs(fu-(su-.030)))
    dv=np.minimum(abs(fv-.030),abs(fv-(sv-.030)))
    rr=np.hypot(du,dv)
    rim=(rr>.009)&(rr<.014);bolt=rr<=.009
    value=np.where(rim,.55,np.where(bolt,.075,value))
    slot=bolt&(dv<.0018);value=np.where(slot,.018,value)
    height=np.where(rim,.001,height);height=np.where(bolt,-.0006,height)
    # Regular recessed diamond-mesh service panels, not noisy all-over speckling.
    vent=(fu>su*.41)&(fu<su*.85)&(fv>sv*.34)&(fv<sv*.67)
    ve=np.minimum.reduce([fu-su*.41,su*.85-fu,fv-sv*.34,sv*.67-fv])
    wire=(abs(np.sin((fu+fv)*420))<.25)|(abs(np.sin((fu-fv)*420))<.25)
    value=np.where(vent,np.where(wire,.26,.014),value)
    value=np.where(vent&(ve<.008),.45,value)
    height=np.where(vent,np.where(wire,-.0003,-.0015),height)
    # Directional scratches with sparse broken lengths and a dark trailing abrasion.
    scuff=(abs(np.sin((u+v*.16)*950))>.9983)&(np.sin(v*137+u*27)>.55)&(macro>.39)&(~seam)&(~vent)
    value=np.where(scuff,value+.13,value)
    color=np.ones((size,size,4),np.float32)
    color[:,:,0]=value*(.97+.035*h);color[:,:,1]=value; color[:,:,2]=value*(1.035-.055*h)
    orm=np.ones_like(color);orm[:,:,0]=np.where(seam,.48,np.where(vent,.61,1))
    orm[:,:,1]=np.where(seam,.65,np.where(bevel,.25,.32+.15*(1-h)+macro*.045))
    orm[:,:,2]=np.where(seam,.50,np.where(vent,.72,.88))
    # UV-space tangent gradients; suppress derivatives at UV island boundaries.
    dy,dx=np.gradient(height.astype(np.float32))
    safe=mask.copy()
    for shift,axis in [(1,0),(-1,0),(1,1),(-1,1)]:safe &= np.roll(mask,shift,axis=axis)
    strength=size/3.5
    ns=np.stack([-dx*strength,-dy*strength,np.ones_like(dx)],axis=-1)
    ns/=np.maximum(np.linalg.norm(ns,axis=-1,keepdims=True),1e-6)
    ns[~safe]=(0,0,1)
    nm=np.ones_like(color);nm[:,:,:3]=ns*.5+.5
    # Dilate all channels together into padding; never blur manufactured details.
    for _ in range(7):
        grown=mask.copy()
        for shift,axis in [(1,0),(-1,0),(1,1),(-1,1)]:
            src=np.roll(mask,shift,axis=axis);fill=(~grown)&src
            for arr in [color,orm,nm]:arr[fill]=np.roll(arr,shift,axis=axis)[fill]
            grown|=fill
        mask=grown
    def image(suffix,arr,linear=False):
        name=kind+'_'+suffix
        old=bpy.data.images.get(name)
        if old:bpy.data.images.remove(old)
        im=bpy.data.images.new(name,width=size,height=size,alpha=False)
        im.colorspace_settings.name='Non-Color' if linear else 'sRGB'
        im.pixels.foreach_set(arr.ravel());im.filepath_raw=str(O/'textures'/(name+'.png'))
        im.file_format='PNG';im.save();im.pack();return im
    images=[image('basecolor',color),image('normal',nm,True),image('ORM',orm,True)]
    ao=np.ones_like(color);ao[:,:,:3]=orm[:,:,0,None]
    image('ao',ao,True)
    m=mat(kind+'_Gunmetal_fix',(.3,.3,.3));nodes=m.node_tree.nodes;links=m.node_tree.links;bs=nodes.get('Principled BSDF')
    ts=[]
    for im in images:
        t=nodes.new('ShaderNodeTexImage');t.image=im;ts.append(t)
    links.new(ts[0].outputs['Color'],bs.inputs['Base Color'])
    n=nodes.new('ShaderNodeNormalMap');links.new(ts[1].outputs['Color'],n.inputs['Color']);links.new(n.outputs['Normal'],bs.inputs['Normal'])
    sep=nodes.new('ShaderNodeSeparateColor');links.new(ts[2].outputs['Color'],sep.inputs['Color'])
    links.new(sep.outputs['Green'],bs.inputs['Roughness']);links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
    g=nodes.new('ShaderNodeGroup');g.node_tree=bpy.data.node_groups['glTF Material Output']
    links.new(sep.outputs['Red'],g.inputs['Occlusion'])
    for i in armor_indices:o.data.materials[i]=m
    print('ATLAS_READY',kind,tris(o),flush=True)

atlas(head,'head',2048)
atlas(body,'segment2',1024)
atlas(tail,'tail',1024)

# Recover all shared instances explicitly after mesh operations.
for o in bpy.data.objects:
    if o.name.startswith('Segment_'):o.data=body.data
assets=[o for o in bpy.data.objects if o.type=='MESH']
for o in assets:
    if not o.data.uv_layers:
        select(o);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(island_margin=.02);bpy.ops.object.mode_set(mode='OBJECT')
    if o not in eyes:triangulate(o)
    o.hide_render=False
assert len([o for o in assets if o.name.startswith('Segment_')])==28
assert len({o.data for o in assets if o.name.startswith('Segment_')})==1
assert lens_baseline=={o.name:{'vertices':[list(v.co) for v in o.data.vertices],
                             'matrix':[list(r) for r in o.matrix_basis]} for o in eyes}, 'Lens changed'

counts={o.name:tris(o) for o in assets}
report={'objects':counts,'total':sum(counts.values()),'head':sum(counts[o.name] for o in [head]+eyes),
        'segment':counts['Segment_00'],'joint':counts['Joint_00_Housing']+counts['Joint_00_GlowBars'],
        'tail':counts['Tail'],'fix_stage':'final' if final else 'wip','lens_geometry_unchanged':True}
print('FIX_COUNTS',report,flush=True)
assert 10000<=report['head']<=18000
assert report['segment']+report['joint']<=1600
assert report['tail']+report['joint']<=3000
assert 30000<=report['total']<=60000
(O/'counts.json').write_text(json.dumps(report,indent=2))

def export(path,obs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,
        export_apply=False,export_yup=True,export_texcoords=True,export_normals=True,
        export_tangents=True,export_draco_mesh_compression_enable=False,export_materials='EXPORT')
export(O/'snake-sectional.glb',assets)
saved=head.matrix_world.copy();head.matrix_world=Matrix.Identity(4)
export(O/'head.glb',[head]+eyes);head.matrix_world=saved
bpy.context.view_layer.update()
sc.render.engine='CYCLES';sc.cycles.samples=32;sc.cycles.use_denoising=True
if os.environ.get('FIX_GPU') == '1':
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='CUDA';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='CUDA'
    sc.cycles.device='GPU'
sc.render.resolution_x=1920;sc.render.resolution_y=1080;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG'
cam=sc.camera
# Reuse the baseline's exact featureless backdrop, three lights, view directions,
# and projected-vertex fitting algorithm. Only filename differs for fix WIP.
source=(Path(__file__).parent/'assemble.py').read_text()
exec(source[source.index('def shot('):source.index('# Exports:')].replace("O+'/captures/'", "str(O)+'/captures/'"))
prefix='' if final else 'fix1-wip-'
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(O/'snake-sectional.blend'))
shot(prefix+'full-body',(-7,-12,7),(.5,0,1.9),11)
shot(prefix+'head-closeup',(-4,-7,5.2),(-2.2,.25,4),3.6,only=[head]+eyes)
cam.location=(-7,-12,7);cam.rotation_euler=(Vector((.5,0,1.9))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=11
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(O/'snake-sectional.blend'))
print('FIX_PASS_RENDERABLE',flush=True)
