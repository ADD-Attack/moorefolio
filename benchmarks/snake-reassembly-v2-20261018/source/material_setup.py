"""Material phase only: assigns shaders/UVs; never changes positions, topology or transforms."""
import bpy,sys,json,math,hashlib,numpy as np
from pathlib import Path
from mathutils import Vector
OUT=Path('material');OUT.mkdir(exist_ok=True)
def linear(c):return ((c+.055)/1.055)**2.4 if c>.04045 else c/12.92
def rgb(hex):return tuple(linear(int(hex[i:i+2],16)/255) for i in (0,2,4))
def fingerprint(me):
 v=np.array([v.co[:] for v in me.vertices],np.float32);f=[tuple(p.vertices) for p in me.polygons]
 return hashlib.sha256(v.tobytes()+repr(f).encode()).hexdigest()
def node(nt,typ,name):n=nt.nodes.new(typ);n.name=name;return n
def mathn(nt,op,a,b=None):
 n=node(nt,'ShaderNodeMath',op);n.operation=op
 for i,v in enumerate([a,b]):
  if v is None:continue
  if isinstance(v,(int,float)):n.inputs[i].default_value=v
  else:nt.links.new(v,n.inputs[i])
 return n.outputs[0]
def ramp(nt,fac,points,name):
 n=node(nt,'ShaderNodeValToRGB',name);r=n.color_ramp
 while len(r.elements)>1:r.elements.remove(r.elements[-1])
 for i,(pos,col) in enumerate(points):
  e=r.elements[0] if i==0 else r.elements.new(pos);e.position=pos;e.color=(*col,1)
 nt.links.new(fac,n.inputs[0]);return n.outputs[0]
def mix(nt,a,b,f,name):
 n=node(nt,'ShaderNodeMixRGB',name);nt.links.new(f,n.inputs[0])
 for i,v in [(1,a),(2,b)]:
  if isinstance(v,tuple):n.inputs[i].default_value=(*v,1)
  else:nt.links.new(v,n.inputs[i])
 return n.outputs[0]
def output(nt,socket,name):n=node(nt,'NodeReroute',name);nt.links.new(socket,n.inputs[0]);return n.outputs[0]
def const(nt,val,name):n=node(nt,'ShaderNodeValue',name);n.outputs[0].default_value=val;return n.outputs[0]
def material(name,base,rough=.44,metal=1.,kind='metal'):
 m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;nt.nodes.clear();p=node(nt,'ShaderNodeBsdfPrincipled','Surface');o=node(nt,'ShaderNodeOutputMaterial','Output');nt.links.new(p.outputs[0],o.inputs['Surface'])
 tc=node(nt,'ShaderNodeTexCoord','Coordinates');noise=node(nt,'ShaderNodeTexNoise','Patina');noise.inputs['Scale'].default_value=28;noise.inputs['Detail'].default_value=4;nt.links.new(tc.outputs['Object'],noise.inputs['Vector'])
 broad=node(nt,'ShaderNodeTexNoise','PlateSheen');broad.inputs['Scale'].default_value=4;nt.links.new(tc.outputs['Object'],broad.inputs['Vector'])
 color=ramp(nt,broad.outputs['Fac'],[(.18,tuple(c*.75 for c in base)),(.78,tuple(c*1.18 for c in base))],'MetalVariation')
 geo=node(nt,'ShaderNodeNewGeometry','Geometry');wear=ramp(nt,geo.outputs['Pointiness'],[(.49,(0,0,0)),(.555,(1,1,1))],'EdgeWear')
 # Broken-up worn edges, never a repeated comb pattern.
 wear=mathn(nt,'MULTIPLY',mathn(nt,'MULTIPLY',wear,noise.outputs['Fac']),.4);color=mix(nt,color,(.18,.17,.15),wear,'WornSteel')
 rust=ramp(nt,noise.outputs['Fac'],[(.68,(0,0,0)),(.79,(.30,.30,.30))],'RustMask');color=mix(nt,color,(.11,.055,.025),rust,'RestrainedOxide')
 # Keep per-plate sheen inside the spec band. Do not subtract a floor; that was the chrome.
 rr=mathn(nt,'ADD',mathn(nt,'MULTIPLY',mathn(nt,'SUBTRACT',broad.outputs['Fac'],.5),.08),rough)
 scale=node(nt,'ShaderNodeVectorMath','ScratchStretch');scale.operation='MULTIPLY';scale.inputs[1].default_value=(4,180,70);nt.links.new(tc.outputs['Object'],scale.inputs[0])
 scratch=node(nt,'ShaderNodeTexNoise','MicroScratches');scratch.inputs['Scale'].default_value=4;scratch.inputs['Detail'].default_value=2;nt.links.new(scale.outputs[0],scratch.inputs['Vector'])
 bump=node(nt,'ShaderNodeBump','MicroNormal');bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.0012;nt.links.new(scratch.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs['Normal'],p.inputs['Normal'])
 if kind=='grille':
  w1=node(nt,'ShaderNodeTexWave','WeaveA');w1.wave_type='BANDS';w1.bands_direction='DIAGONAL';w1.inputs['Scale'].default_value=100;nt.links.new(tc.outputs['Object'],w1.inputs['Vector']);nt.links.new(w1.outputs['Color'],bump.inputs['Height']);bump.inputs['Distance'].default_value=.0018
 if kind=='dark':color=mix(nt,color,base,const(nt,.75,'DarkLock'),'DarkSteel');rr=const(nt,rough,'DarkRoughness')
 output(nt,color,'BAKE_COLOR');output(nt,rr,'BAKE_ROUGH');output(nt,const(nt,metal,'Metalness'),'BAKE_METAL')
 nt.links.new(color,p.inputs['Base Color']);nt.links.new(rr,p.inputs['Roughness']);p.inputs['Metallic'].default_value=metal
 if 'Specular IOR Level' in p.inputs:p.inputs['Specular IOR Level'].default_value=.50
 ao=node(nt,'ShaderNodeAmbientOcclusion','LocalAO');ao.inputs['Distance'].default_value=.16;ao.samples=16;ao.only_local=True;output(nt,ao.outputs['AO'],'BAKE_AO')
 output(nt,const(nt,0.,'NoEmission'),'BAKE_EMISSION');m['emission_strength']=0.;m.diffuse_color=(*base,1)
 return m
steel=[material('Gunmetal_%02d'%i,tuple(c*f for c in (.145,.138,.122)),r) for i,(f,r) in enumerate([(.88,.46),(1,.42),(1.12,.38),(.74,.52)])]
dark=material('DarkHousing',(.03,.032,.028),.52,1.,'dark');hardware=material('MachinedSteel',(.22,.21,.19),.40);grille=material('RecessedGrille',(.04,.042,.036),.55,1.,'grille');fin=material('FinInset',(.09,.095,.085),.48)
bar=material('TealInsert',rgb('71CCBD'),.40,.08,'dark');p=bar.node_tree.nodes['Surface'];p.inputs['Emission Color'].default_value=(*rgb('71CCBD'),1);p.inputs['Emission Strength'].default_value=0.50;bar['emission_strength']=0.50
nt=bar.node_tree;co=node(nt,'ShaderNodeRGB','InsertEmission');co.outputs[0].default_value=(*rgb('71CCBD'),1);nt.links.new(co.outputs[0],nt.nodes['BAKE_EMISSION'].inputs[0])
materials=steel+[dark,hardware,grille,fin,bar]
def eye_material(name,center,normal,R):
 m=material(name,(.07,.11,.08),.18,.25,'dark');nt=m.node_tree;p=nt.nodes['Surface'];tc=nt.nodes['Coordinates']
 sub=node(nt,'ShaderNodeVectorMath','EyeOffset');sub.operation='SUBTRACT';sub.inputs[1].default_value=center;nt.links.new(tc.outputs['Object'],sub.inputs[0])
 dot=node(nt,'ShaderNodeVectorMath','EyePlaneDepth');dot.operation='DOT_PRODUCT';dot.inputs[1].default_value=normal;nt.links.new(sub.outputs[0],dot.inputs[0])
 ns=node(nt,'ShaderNodeVectorMath','EyeNormalDepth');ns.operation='SCALE';ns.inputs[0].default_value=normal;nt.links.new(dot.outputs['Value'],ns.inputs['Scale'])
 proj=node(nt,'ShaderNodeVectorMath','EyeRadial');proj.operation='SUBTRACT';nt.links.new(sub.outputs[0],proj.inputs[0]);nt.links.new(ns.outputs[0],proj.inputs[1])
 length=node(nt,'ShaderNodeVectorMath','EyeRadius');length.operation='LENGTH';nt.links.new(proj.outputs[0],length.inputs[0]);rad=mathn(nt,'DIVIDE',length.outputs['Value'],R)
 color=ramp(nt,rad,[(0,rgb('F8FDFF')),(.08,rgb('F8FDFF')),(.20,rgb('C9FAF4')),(.36,rgb('60C4B0')),(.55,rgb('0C8B6C')),(.68,rgb('08624A')),(.73,rgb('1D342A')),(.80,rgb('454F44')),(.87,rgb('112016')),(1,rgb('49483F'))],'EyeRadialColor')
 mask=ramp(nt,rad,[(0,(1,1,1)),(.68,(1,1,1)),(.73,(0,0,0)),(1,(0,0,0))],'EyeLitDisc')
 em=mix(nt,(0,0,0),color,mask,'EyeEmission');nt.links.new(color,nt.nodes['BAKE_COLOR'].inputs[0]);nt.links.new(color,p.inputs['Base Color']);nt.links.new(em,nt.nodes['BAKE_EMISSION'].inputs[0]);nt.links.new(em,p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=1.05;p.inputs['Coat Weight'].default_value=.22;p.inputs['Coat Roughness'].default_value=.32;m['emission_strength']=1.05
 # Preserve optical smoothness: no corrosion/noise normal on the cover.
 for l in list(p.inputs['Normal'].links):nt.links.remove(l)
 nt.links.new(const(nt,.18,'OpticalRough'),nt.nodes['BAKE_ROUGH'].inputs[0]);p.inputs['Roughness'].default_value=.18
 return m
sources=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('SRC_')]
baseline=json.load(open('material/inventory.json'));report={}
for ob in sources:
 me=ob.data;assert fingerprint(me)==baseline[ob.name]['mesh_hash'];me.update();me.materials.clear()
 for m in materials:me.materials.append(m)
 parent=list(range(len(me.vertices)))
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for poly in me.polygons:
  a=root(poly.vertices[0])
  for j in poly.vertices[1:]:parent[root(j)]=a
 comps={}
 for i in range(len(me.vertices)):comps.setdefault(root(i),[]).append(i)
 component_info={k:(len(ids),np.mean([me.vertices[i].co[:] for i in ids],axis=0)) for k,ids in comps.items()}
 eye_ids={}
 if ob.name=='SRC_Head':
  for k,ids in comps.items():
   if len(ids)!=288:continue
   V=np.array([me.vertices[i].co[:] for i in ids]);ct=V.mean(0);_,_,vh=np.linalg.svd(V-ct);n=vh[-1];n*=np.sign(n[1]*ct[1]);rad=np.linalg.norm((V-ct)-np.outer((V-ct)@n,n),axis=1);R=float(rad.max());m=eye_material('Optic_'+str(k),ct,n,R);me.materials.append(m);eye_ids[k]=len(me.materials)-1
 plate_ids={}
 if ob.name in ('SRC_SegmentHero','SRC_SegmentNeck'):
  sequence=[(80,1),(54,0),(60,2),(10,4),(34,6),(39,6),(34,6),(34,6),(12,2),(6,2),(12,0),(40,4),(160,4),(40,5),(12,4)]
  j=0;used_tri=0
  for poly in me.polygons:
   if j>=len(sequence):break
   plate_ids[poly.index]=sequence[j][1];used_tri+=len(poly.vertices)-2
   if used_tri==sequence[j][0]:j+=1;used_tri=0
   elif used_tri>sequence[j][0]:raise RuntimeError(('face-range mismatch',ob.name,j))
 for poly in me.polygons:
  c=poly.center;x,y,z=c;rad=math.hypot(y,z);ang=math.degrees(math.atan2(z,y));k=root(poly.vertices[0]);count,ct=component_info[k]
  mat=1
  if 'Glow' in ob.name:mat=8
  elif ob.name=='SRC_Head':
   if k in eye_ids:mat=eye_ids[k]
   elif count<80:mat=5 if count>8 else 4
   else:
    # Broad plate values only; no artificial large relief or invented seams.
    mat=0 if z<-.32 else 1
    if z>.76:mat=7
    if x<.40:mat=0
    # Existing cheek vent recesses and slats.
    if .98<x<1.35 and -.02<z<.23 and abs(y)>.50:mat=6
  elif 'Segment' in ob.name or 'Taper' in ob.name:
   mat=0 if z<-.12 else 1
   if 'Taper' in ob.name:
    local=[math.hypot(v.co.y,v.co.z) for v in me.vertices if abs(v.co.x-x)<.09]
    if local:rad=rad/max(local)*.515
   if rad<.405:mat=4
   if count<30 and rad>.42:mat=5
   # Dark recess floors and crossed wire; frame surfaces retain metal.
   xx=x/1.32113066657
   for x0,x1,a0,a1 in [(-.28,-.075,114,124),(-.025,.135,140,153),(-.27,-.055,36,43),(-.27,-.065,172,188)]:
    aa=ang if ang>=0 else ang+360
    if x0<xx<x1 and a0<aa<a1 and rad<.505:mat=6
   if x<-.56 and rad<.47:mat=4
  elif 'TailTip' in ob.name:
   mat=1 if z>-.03 else 0
   if count<32:mat=5
   if -.83<x<-.47 and abs(y)<.105 and z>.02:mat=6
   if -1.14<x<-.85 and abs(z)<.09 and abs(y)>.06:mat=6
  if poly.index in plate_ids:
   mat=plate_ids[poly.index]
   # Preserve metallic bevel frames; only recessed grille surfaces are dark.
   if mat==6 and rad>.49:mat=5
  poly.material_index=mat
 # Only UV topology metadata changes; mesh positions/faces are frozen.
 ob.hide_viewport=False;ob.hide_set(False);bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.012,area_weight=.2);bpy.ops.object.mode_set(mode='OBJECT');ob.hide_viewport=True
 assert fingerprint(me)==baseline[ob.name]['mesh_hash'],ob.name
 report[ob.name]={'hash_unchanged':True,'materials':{m.name:sum(p.material_index==i for p in me.polygons) for i,m in enumerate(me.materials)}}
# Raw source meshes and their visible instances share data; no object transforms changed.
Path('material/m1d-assignment.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'m1d-procedural.blend'))
print('MATERIAL_SETUP_COMPLETE',flush=True)
