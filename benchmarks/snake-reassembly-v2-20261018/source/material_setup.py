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
 tc=node(nt,'ShaderNodeTexCoord','Coordinates');noise=node(nt,'ShaderNodeTexNoise','Patina');noise.inputs['Scale'].default_value=9;noise.inputs['Detail'].default_value=6;nt.links.new(tc.outputs['Object'],noise.inputs['Vector'])
 cells=node(nt,'ShaderNodeTexVoronoi','PlateCells');cells.feature='F1';cells.inputs['Scale'].default_value=2.4;cells.inputs['Randomness'].default_value=1;nt.links.new(tc.outputs['Object'],cells.inputs['Vector'])
 sep=node(nt,'ShaderNodeSeparateColor','CellSplit');nt.links.new(cells.outputs['Color'],sep.inputs['Color'])
 # Hard per-plate steps. Capture distance was washing out the old 0.75-1.18 noise.
 color=ramp(nt,sep.outputs['Red'],[(.15,tuple(c*.62 for c in base)),(.38,tuple(c*.82 for c in base)),(.62,base),(.82,tuple(min(1,c*1.35) for c in base))],'PlateSteps')
 color_node=nt.nodes['PlateSteps'];color_node.color_ramp.interpolation='CONSTANT'
 seams=node(nt,'ShaderNodeTexVoronoi','PlateSeams');seams.feature='DISTANCE_TO_EDGE';seams.inputs['Scale'].default_value=2.4;nt.links.new(tc.outputs['Object'],seams.inputs['Vector'])
 grime=mathn(nt,'LESS_THAN',seams.outputs['Distance'],.08);color=mix(nt,color,(.05,.045,.035),grime,'SeamDark')
 geo=node(nt,'ShaderNodeNewGeometry','Geometry');wear=ramp(nt,geo.outputs['Pointiness'],[(.46,(0,0,0)),(.58,(1,1,1))],'EdgeWear')
 wear=mathn(nt,'MULTIPLY',wear,.55);color=mix(nt,color,tuple(min(1,c*1.25) for c in base),wear,'EdgeBright')
 rustn=node(nt,'ShaderNodeTexNoise','RustField');rustn.inputs['Scale'].default_value=3.2;rustn.inputs['Detail'].default_value=2;nt.links.new(tc.outputs['Object'],rustn.inputs['Vector'])
 rust_amt=mathn(nt,'GREATER_THAN',rustn.outputs['Fac'],.67);color=mix(nt,color,(.55,.22,.07),rust_amt,'VisibleOxide')
 rr=mathn(nt,'ADD',mathn(nt,'MULTIPLY',mathn(nt,'SUBTRACT',sep.outputs['Green'],.5),.10),rough)
 rr=mathn(nt,'ADD',rr,mathn(nt,'MULTIPLY',rust_amt,.12))
 pits=mathn(nt,'GREATER_THAN',noise.outputs['Fac'],.78);color=mix(nt,color,(.03,.025,.02),pits,'PitDark')
 plate_rust=mathn(nt,'GREATER_THAN',sep.outputs['Red'],.84);color=mix(nt,color,(.48,.18,.06),plate_rust,'PlateOxide')
 height=mathn(nt,'SUBTRACT',mathn(nt,'ADD',mathn(nt,'MULTIPLY',pits,1),mathn(nt,'MULTIPLY',noise.outputs['Fac'],.2)),mathn(nt,'MULTIPLY',grime,.4))
 bump=node(nt,'ShaderNodeBump','MicroNormal');bump.inputs['Strength'].default_value=.85;bump.inputs['Distance'].default_value=.018;nt.links.new(height,bump.inputs['Height']);nt.links.new(bump.outputs['Normal'],p.inputs['Normal'])
 if kind=='grille':
  w1=node(nt,'ShaderNodeTexWave','WeaveA');w1.wave_type='BANDS';w1.bands_direction='DIAGONAL';w1.inputs['Scale'].default_value=100;nt.links.new(tc.outputs['Object'],w1.inputs['Vector']);nt.links.new(w1.outputs['Color'],bump.inputs['Height']);bump.inputs['Distance'].default_value=.0018
 if kind=='dark':color=mix(nt,color,base,const(nt,.35,'DarkLock'),'DarkSteel')
 output(nt,color,'BAKE_COLOR');output(nt,rr,'BAKE_ROUGH');output(nt,const(nt,metal,'Metalness'),'BAKE_METAL')
 nt.links.new(color,p.inputs['Base Color']);nt.links.new(rr,p.inputs['Roughness']);p.inputs['Metallic'].default_value=metal
 if 'Specular IOR Level' in p.inputs:p.inputs['Specular IOR Level'].default_value=.42
 ao=node(nt,'ShaderNodeAmbientOcclusion','LocalAO');ao.inputs['Distance'].default_value=.16;ao.samples=16;ao.only_local=True;output(nt,ao.outputs['AO'],'BAKE_AO')
 output(nt,const(nt,0.,'NoEmission'),'BAKE_EMISSION');m['emission_strength']=0.;m.diffuse_color=(*base,1)
 return m
steel=[material('Gunmetal_%02d'%i,rgb(h),r) for i,(h,r) in enumerate([('6E6758',.50),('8A8070',.56),('5C5648',.62),('7A6A52',.54)])]
dark=material('DarkHousing',rgb('2A2824'),.62,1.,'dark');hardware=material('MachinedSteel',rgb('8C8474'),.48);grille=material('RecessedGrille',rgb('3A342C'),.64,1.,'grille');fin=material('FinInset',rgb('4A453C'),.56)
bar=material('TealInsert',rgb('71CCBD'),.40,.08,'dark');p=bar.node_tree.nodes['Surface'];p.inputs['Emission Color'].default_value=(*rgb('71CCBD'),1);p.inputs['Emission Strength'].default_value=0.50;bar['emission_strength']=0.50
nt=bar.node_tree;co=node(nt,'ShaderNodeRGB','InsertEmission');co.outputs[0].default_value=(*rgb('71CCBD'),1);nt.links.new(co.outputs[0],nt.nodes['BAKE_EMISSION'].inputs[0])
materials=steel+[dark,hardware,grille,fin,bar]
def eye_material(name):
 m=material(name,(.07,.11,.08),.22,.2,'dark');nt=m.node_tree;p=nt.nodes['Surface']
 attr=node(nt,'ShaderNodeAttribute','EyeRadialAttr');attr.attribute_name='EyeRadial';rad=attr.outputs['Fac']
 color=ramp(nt,rad,[(0,rgb('FFFFFF')),(.08,rgb('FFFFFF')),(.10,rgb('CFFFF3')),(.17,rgb('CFFFF3')),(.19,rgb('18A07A')),(.28,rgb('18A07A')),(.30,rgb('06382A')),(.40,rgb('06382A')),(1,rgb('141210'))],'EyeRadialColor')
 mask=ramp(nt,rad,[(0,(1,1,1)),(.40,(1,1,1)),(.46,(0,0,0)),(1,(0,0,0))],'EyeLitDisc')
 
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
   V=np.array([me.vertices[i].co[:] for i in ids]);ct=V.mean(0);_,_,vh=np.linalg.svd(V-ct);n=vh[-1];n*=np.sign(n[1]*ct[1] or 1);rad=np.linalg.norm((V-ct)-np.outer((V-ct)@n,n),axis=1);R=float(rad.max()) or 1;m=eye_material('Optic_'+str(k));me.materials.append(m);eye_ids[k]=(len(me.materials)-1,ids,rad/R)
 if ob.name=='SRC_Head' and eye_ids:
  if 'EyeRadial' in me.color_attributes:me.color_attributes.remove(me.color_attributes['EyeRadial'])
  attr=me.color_attributes.new('EyeRadial','FLOAT_COLOR','POINT')
  for k,(slot,ids,frac) in eye_ids.items():
   for vid,f in zip(ids,frac):attr.data[vid].color=(float(f),float(f),float(f),1)
   eye_ids[k]=slot
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
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.012,area_weight=.2);bpy.ops.object.mode_set(mode='OBJECT')
 if ob.name=='SRC_Head':
  uv=me.uv_layers.active.data;boxes=[(.02,.05),(.02,.55)]
  slots=[i for i,m in enumerate(me.materials) if m and m.name.startswith('Optic_')]
  eye_loops=set()
  for (bx,by),slot in zip(boxes,slots):
   loops=[li for poly in me.polygons if poly.material_index==slot for li in poly.loop_indices];eye_loops.update(loops)
   if not loops:continue
   us=[uv[li].uv for li in loops];minx=min(u.x for u in us);maxx=max(u.x for u in us);miny=min(u.y for u in us);maxy=max(u.y for u in us)
   sx=max(maxx-minx,1e-6);sy=max(maxy-miny,1e-6)
   for li in loops:
    u=uv[li].uv;u.x=bx+(u.x-minx)/sx*.22;u.y=by+(u.y-miny)/sy*.22
  for li,luv in enumerate(uv):
   if li in eye_loops:continue
   luv.uv.x=.28+luv.uv.x*.70;luv.uv.y=.02+luv.uv.y*.96
 ob.hide_viewport=True
 assert fingerprint(me)==baseline[ob.name]['mesh_hash'],ob.name
 report[ob.name]={'hash_unchanged':True,'materials':{m.name:sum(p.material_index==i for p in me.polygons) for i,m in enumerate(me.materials)}}
# Raw source meshes and their visible instances share data; no object transforms changed.
Path('material/m3-assignment.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'m3-procedural.blend'))
print('MATERIAL_SETUP_COMPLETE',flush=True)
