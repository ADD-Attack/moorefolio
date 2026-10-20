"""M4 material-only replacement. Start from M3 procedural blend, keep geometry and non-optic UVs; lens allocation only for texel resolution.
Usage: blender -b material/m3-procedural.blend -P source/material_setup_m4.py -- <absolute ticket path>
"""
import bpy,sys,os,json,hashlib,math,numpy as np
from pathlib import Path
T=Path(sys.argv[sys.argv.index('--')+1]);os.chdir(T);OUT=T/'material'
# Reuse only utility functions, never M3 shader construction or UV projection.
helpers=(T/'source/material_setup.py').read_text().split('def material(')[0]
exec(helpers)
def noise(nt,coord,scale,detail,name,stretch=None):
 if stretch:
  v=node(nt,'ShaderNodeVectorMath',name+'Stretch');v.operation='MULTIPLY';nt.links.new(coord,v.inputs[0]);v.inputs[1].default_value=stretch;coord=v.outputs[0]
 n=node(nt,'ShaderNodeTexNoise',name);n.inputs['Scale'].default_value=scale;n.inputs['Detail'].default_value=detail;nt.links.new(coord,n.inputs['Vector']);return n.outputs['Fac']
def mask(nt,fac,lo,hi,name):return ramp(nt,fac,[(lo,(0,0,0)),(hi,(1,1,1))],name)
def make(name,base,rough,kind='metal'):
 m=bpy.data.materials.new('M4_'+name);m.use_nodes=True;nt=m.node_tree;nt.nodes.clear()
 p=node(nt,'ShaderNodeBsdfPrincipled','Surface');out=node(nt,'ShaderNodeOutputMaterial','Output');nt.links.new(p.outputs[0],out.inputs[0])
 tc=node(nt,'ShaderNodeTexCoord','Coordinates');co=tc.outputs['Object'];geo=node(nt,'ShaderNodeNewGeometry','ActualCurvature')
 fine=noise(nt,co,105,2,'MachinedPitting');grain=noise(nt,co,42,2,'FineGrain')
 streak=noise(nt,co,1,2,'DirectionalScuff', (6,65,90))
 breakup=noise(nt,co,22,2,'WearBreakup')
 curvature=mask(nt,geo.outputs['Pointiness'],.505,.55,'ConvexEdgeMask')
 bevel=node(nt,'ShaderNodeBevel','EdgeProbeOnly');bevel.inputs['Radius'].default_value=.009;bevel.samples=8
 dot=node(nt,'ShaderNodeVectorMath','EdgeNormalDot');dot.operation='DOT_PRODUCT';nt.links.new(bevel.outputs['Normal'],dot.inputs[0]);nt.links.new(geo.outputs['Normal'],dot.inputs[1])
 edge_delta=mathn(nt,'SUBTRACT',1,dot.outputs['Value'])
 edge=mask(nt,edge_delta,.0008,.025,'PhysicalEdgeMask')
 edge=mathn(nt,'MULTIPLY',edge,mathn(nt,'ADD',.3,mathn(nt,'MULTIPLY',curvature,.7)))
 anchor=node(nt,'ShaderNodeAttribute','PreservedSeamAttribute');anchor.attribute_name='M4_SeamDistance'
 split=node(nt,'ShaderNodeSeparateColor','SeamDistanceChannels');nt.links.new(anchor.outputs['Color'],split.inputs[0])
 seam_band=ramp(nt,split.outputs['Red'],[(0,(0,)*3),(.003,(0,)*3),(.007,(1,)*3),(.015,(0,)*3),(1,(0,)*3)],'ExistingSeamShoulder')
 edge=mathn(nt,'MAXIMUM',edge,mathn(nt,'MULTIPLY',seam_band,.85))
 edge=mathn(nt,'MULTIPLY',edge,mask(nt,breakup,.27,.65,'BrokenEdges'))
 ao=node(nt,'ShaderNodeAmbientOcclusion','LocalAO');ao.inputs['Distance'].default_value=.12;ao.samples=32;ao.only_local=True
 grime=mathn(nt,'SUBTRACT',1,ao.outputs['AO'])
 seam_zone=mathn(nt,'SUBTRACT',1,mask(nt,split.outputs['Red'],.012,.035,'SeamOxideReach'))
 grime=mathn(nt,'MAXIMUM',grime,mathn(nt,'MULTIPLY',seam_zone,.32))
 grime=output(nt,grime,'CAVITY_MASK')
 # Tiny connected-component shifts, never invented Voronoi plates.
 step=ramp(nt,geo.outputs['Random Per Island'],[(0,tuple(c*.90 for c in base)),(1,tuple(c*1.04 for c in base))],'ComponentTint')
 color=mix(nt,step,tuple(c*.76 for c in base),mathn(nt,'MULTIPLY',grain,.5),'GrainTone')
 stain=noise(nt,co,1,2,'FineDirectionalOxidation',(9,44,65))
 color=mix(nt,color,tuple(c*.55 for c in base),mathn(nt,'MULTIPLY',mask(nt,stain,.35,.7,'DirectionalToneMask'),.12),'DirectionalTone')
 color=mix(nt,color,rgb('34312A'),mathn(nt,'MULTIPLY',grime,.60),'RecessGrime')
 scratch=mask(nt,streak,.60,.70,'NarrowScratches');scratch=mathn(nt,'MULTIPLY',scratch,mask(nt,breakup,.42,.60,'InterruptedScratch'))
 # Scratches concentrate near convex edges but don't vanish entirely on plate faces.
 scratch=mathn(nt,'MULTIPLY',scratch,mathn(nt,'ADD',.10,mathn(nt,'MULTIPLY',edge,.9)))
 color=mix(nt,color,rgb('B4B3AA'),mathn(nt,'MULTIPLY',edge,.85),'EdgePolish')
 color=mix(nt,color,rgb('B9B8AE'),mathn(nt,'MULTIPLY',scratch,.55),'FineScuffColor')
 # Sparse elongated marks, not connected Voronoi cell boundaries (those read as cracks).
 hairfield=noise(nt,co,1,1,'IsolatedDirectionalHairlines',(4,150,105))
 hair=mask(nt,hairfield,.67,.73,'HairlineThreshold')
 hair=mathn(nt,'MULTIPLY',hair,mask(nt,breakup,.44,.62,'ScratchScatter'))
 color=mix(nt,color,rgb('BBBDB5'),mathn(nt,'MULTIPLY',hair,.80),'SilverHairlines')
 rustfield=noise(nt,co,1,2,'OxideRuns',(60,60,7))
 rust=mask(nt,rustfield,.60,.69,'SparseOxide');rust=mathn(nt,'MULTIPLY',rust,mathn(nt,'MINIMUM',1,mathn(nt,'ADD',.10,mathn(nt,'ADD',mathn(nt,'MULTIPLY',grime,1.8),mathn(nt,'MULTIPLY',edge,.85)))))
 color=mix(nt,color,rgb('61472F'),mathn(nt,'MULTIPLY',rust,.85),'RestrainedBrownOxide')
 rr=mathn(nt,'ADD',rough,mathn(nt,'MULTIPLY',mathn(nt,'SUBTRACT',grain,.5),.14))
 rr=mathn(nt,'ADD',rr,mathn(nt,'MULTIPLY',mathn(nt,'SUBTRACT',stain,.5),.20))
 rr=mathn(nt,'SUBTRACT',rr,mathn(nt,'MULTIPLY',edge,.075));rr=mathn(nt,'ADD',rr,mathn(nt,'MULTIPLY',rust,.13))
 height=mathn(nt,'SUBTRACT',mathn(nt,'MULTIPLY',fine,.5),mathn(nt,'MULTIPLY',scratch,.25))
 bump=node(nt,'ShaderNodeBump','FineMachiningOnly');bump.inputs['Strength'].default_value=.48;bump.inputs['Distance'].default_value=.0025;nt.links.new(height,bump.inputs['Height']);nt.links.new(bump.outputs[0],p.inputs['Normal'])
 metal=mathn(nt,'SUBTRACT',.98,mathn(nt,'MULTIPLY',rust,.55))
 if kind in ('dark','grille'):metal=const(nt,.85,'DarkMetal');bump.inputs['Distance'].default_value=.0005
 if kind=='grille':
  xyz=node(nt,'ShaderNodeSeparateXYZ','WeaveCoordinates');nt.links.new(co,xyz.inputs[0])
  yz=mathn(nt,'ADD',xyz.outputs['Y'],xyz.outputs['Z'])
  wires=[]
  for sign in [1,-1]:
   axis=mathn(nt,'ADD',xyz.outputs['X'],mathn(nt,'MULTIPLY',yz,sign))
   wave=mathn(nt,'SINE',mathn(nt,'MULTIPLY',axis,460))
   wires.append(mask(nt,wave,.63,.86,'WireCross'+str(sign)))
  wire=mathn(nt,'MAXIMUM',*wires)
  color=mix(nt,rgb('1A1D1B'),rgb('6A7069'),wire,'FineRecessedWeave')
  rr=const(nt,.58,'WeaveRough');nt.links.new(wire,bump.inputs['Height']);bump.inputs['Distance'].default_value=.0012
 if kind=='dark':
  # Hidden chassis should stay near-black, not inherit broad pale wear from armor.
  color=mix(nt,base,tuple(c*.68 for c in base),mathn(nt,'MULTIPLY',grain,.45),'ChassisTone')
 emission=const(nt,0,'NoEmission')
 if kind=='glow':
  color=ramp(nt,grain,[(0,rgb('45AC98')),(1,rgb('8DE1CA'))],'InsertTint');emission=color;metal=const(nt,.10,'InsertMetal');rr=const(nt,.32,'InsertRough');p.inputs['Emission Strength'].default_value=1.2
 for s,n in [(color,'BAKE_COLOR'),(rr,'BAKE_ROUGH'),(metal,'BAKE_METAL'),(ao.outputs['AO'],'BAKE_AO'),(emission,'BAKE_EMISSION')]:output(nt,s,n)
 for s,k in [(color,'Base Color'),(rr,'Roughness'),(metal,'Metallic'),(emission,'Emission Color')]:nt.links.new(s,p.inputs[k])
 m.diffuse_color=(*base,1);return m
palette={'Gunmetal_00':('96968D',.53,'metal'),'Gunmetal_01':('9B998F',.52,'metal'),'Gunmetal_02':('929287',.55,'metal'),'Gunmetal_03':('999589',.54,'metal'),'DarkHousing':('494B47',.57,'dark'),'MachinedSteel':('ABA99F',.47,'metal'),'RecessedGrille':('4C4B44',.59,'grille'),'FinInset':('858379',.54,'metal'),'TealInsert':('71CCBD',.32,'glow')}
new={k:make(k,rgb(h),r,kind) for k,(h,r,kind) in palette.items()}
base=json.load(open(OUT/'inventory.json'));report={}
for ob in [o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('SRC_')]:
 me=ob.data;assert fingerprint(me)==base[ob.name]['mesh_hash'];nonoptic=[li for poly in me.polygons if not me.materials[poly.material_index].name.startswith('Optic_') for li in poly.loop_indices];uv_before=np.array([u.uv[:] for u in me.uv_layers.active.data],np.float32);uvhash=hashlib.sha256(np.array([u.uv[:] for u in me.uv_layers.active.data],np.float32).tobytes()).hexdigest()
 # Distance-to-existing-seam is a material attribute only; vertices/faces untouched.
 if 'M4_SeamDistance' in me.color_attributes:me.color_attributes.remove(me.color_attributes['M4_SeamDistance'])
 attr=me.color_attributes.new('M4_SeamDistance','FLOAT_COLOR','POINT')
 distances=np.ones(len(me.vertices))
 if ob.name=='SRC_Head':
  raw=np.array([[.19-v.co.x/(1.30/.59),.435+v.co.z/(1.30/.59)] for v in me.vertices])
  paths=[[(-.97,.39),(-.90,.42),(-.84,.47)],[(-.86,.49),(-.82,.57),(-.75,.61)],[(-.78,.62),(-.70,.65),(-.60,.65),(-.53,.61)],[(-.86,.39),(-.82,.34),(-.80,.29)],[(-.73,.38),(-.70,.33),(-.68,.285)],[(-.59,.40),(-.57,.345),(-.54,.30)],[(-.47,.40),(-.45,.345),(-.43,.29)],[(-.49,.61),(-.43,.66),(-.35,.685)],[(-.41,.69),(-.40,.62),(-.37,.59)],[(-.13,.64),(-.10,.60),(-.09,.55)],[(-.85,.23),(-.84,.28)],[(-.67,.225),(-.65,.28)],[(-.48,.23),(-.47,.29)]]
  for path in paths:
   for a,b in zip(path[:-1],path[1:]):
    a=np.array(a);b=np.array(b);ab=b-a;t=np.clip((raw-a)@ab/(ab@ab),0,1);d=np.linalg.norm(raw-a-t[:,None]*ab,axis=1);distances=np.minimum(distances,d)
  # Side cuts are not projected through the crown or concealed medial surfaces.
  for i,v in enumerate(me.vertices):
   if abs(v.co.y)<.15:distances[i]=1
 for i,d in enumerate(distances):attr.data[i].color=(float(d),0,0,1)
 for slot,old in enumerate(list(me.materials)):
  if old.name.startswith('Optic_'):
   ids=sorted({v for poly in me.polygons if poly.material_index==slot for v in poly.vertices});V=np.array([me.vertices[i].co[:] for i in ids]);ct=V.mean(0);_,_,vh=np.linalg.svd(V-ct);normal=vh[-1];R=np.linalg.norm((V-ct)-np.outer((V-ct)@normal,normal),axis=1).max()
   m=make(old.name,rgb('164F42'),.2,'dark');nt=m.node_tree;p=nt.nodes['Surface'];co=nt.nodes['Coordinates'].outputs['Object']
   def vec(op,a,b,name):
    n=node(nt,'ShaderNodeVectorMath',name);n.operation=op
    for j,v in enumerate([a,b]):
     if isinstance(v,(tuple,list,np.ndarray)):n.inputs[j].default_value=v
     else:nt.links.new(v,n.inputs[j])
    return n
   rel=vec('SUBTRACT',co,ct,'LensOrigin').outputs[0];du=vec('DOT_PRODUCT',rel,vh[0],'LensU').outputs['Value'];dv=vec('DOT_PRODUCT',rel,vh[1],'LensV').outputs['Value']
   radius=mathn(nt,'DIVIDE',mathn(nt,'SQRT',mathn(nt,'ADD',mathn(nt,'MULTIPLY',du,du),mathn(nt,'MULTIPLY',dv,dv))),float(R))
   # The optical cover is .60 of outer assembly radius (frozen P8 lathe profile).
   assembly_radius=radius
   radius=mathn(nt,'DIVIDE',radius,.60)
   # Map entire forward-facing lens assembly continuously into its existing reserved box.
   eye_index=0 if ct[1]<0 else 1;bx,by=(.02,.55) if eye_index==0 else (.02,.05)
   for poly in me.polygons:
    if poly.material_index!=slot:continue
    for li in poly.loop_indices:
     v=np.array(me.vertices[me.loops[li].vertex_index].co[:])-ct
     me.uv_layers.active.data[li].uv=(bx+.11+.108*float(v@vh[0])/R,by+.11+.108*float(v@vh[1])/R)
   # Core diameter / lit-disc diameter = .28; crisp mint annulus and teal perimeter.
   col=ramp(nt,radius,[(0,rgb('FFFFFF')),(.28,rgb('FFFFFF')),(.30,rgb('C9FAF4')),(.54,rgb('9EE6DA')),(.57,rgb('60C4B0')),(.70,rgb('60C4B0')),(.73,rgb('0C8B6C')),(1,rgb('08624A'))],'SharpRadialTarget')
   em=ramp(nt,radius,[(0,(1,1,1)),(.28,(1,1,1)),(.30,(.35,.75,.58)),(.54,(.17,.50,.35)),(.57,(.025,.32,.20)),(.70,(.025,.32,.20)),(.73,(.005,.12,.06)),(1,(.002,.045,.022))],'LensEmission')
   # Keep the machined outer ring, groove and bezel non-emissive.
   hardware=ramp(nt,assembly_radius,[(.59,rgb('123E33')),(.61,rgb('123E33')),(.68,rgb('161E1B')),(.70,rgb('171B18')),(.72,rgb('9C9F95')),(.76,rgb('9C9F95')),(.79,rgb('202823')),(.82,rgb('202823')),(.84,rgb('6D736A')),(.9,rgb('969C91')),(1,rgb('747B72'))],'LensHardware')
   outside=mask(nt,assembly_radius,.596,.604,'OutsideLitDisc')
   col=mix(nt,col,hardware,outside,'TargetAndHardware')
   em=mix(nt,em,(0,0,0),outside,'ConfinedEmission')
   # Ring brightness stays below the core; Standard display + bloom must not merge them.
   for e in nt.nodes['LensEmission'].color_ramp.elements:
    if .29<e.position<.9:
     e.color=tuple(c*.32 for c in e.color[:3])+(1,)
   for l in list(p.inputs['Normal'].links):nt.links.remove(l)
   for s,k in [(col,'BAKE_COLOR'),(em,'BAKE_EMISSION'),(ramp(nt,assembly_radius,[(0,(.26,)*3),(.6,(.26,)*3),(.7,(.43,)*3),(1,(.43,)*3)],'OpticRough'),'BAKE_ROUGH'),(ramp(nt,assembly_radius,[(0,(.1,)*3),(.6,(.1,)*3),(.7,(.95,)*3),(1,(.95,)*3)],'OpticMetal'),'BAKE_METAL')]:nt.links.new(s,nt.nodes[k].inputs[0])
   nt.links.new(col,p.inputs['Base Color']);nt.links.new(em,p.inputs['Emission Color']);nt.links.new(nt.nodes['BAKE_ROUGH'].outputs[0],p.inputs['Roughness']);nt.links.new(nt.nodes['BAKE_METAL'].outputs[0],p.inputs['Metallic']);p.inputs['Emission Strength'].default_value=1.8
   me.materials[slot]=m
  elif old.name in new:me.materials[slot]=new[old.name]
  else:raise RuntimeError('Unknown M3 material '+old.name)
 maskpath=OUT/'masks'/(ob.name+'_EdgeMask.png')
 if maskpath.exists():
  im=bpy.data.images.load(str(maskpath.resolve()),check_existing=True);im.colorspace_settings.name='Non-Color';im.pack()
  for slot,old in enumerate(list(me.materials)):
   if 'Optic_' in old.name:continue
   m=old.copy();m.name=old.name+'_'+ob.name;me.materials[slot]=m;nt=m.node_tree
   tex=node(nt,'ShaderNodeTexImage','FrozenGeometryEdgeMask');tex.image=im
   sep=node(nt,'ShaderNodeSeparateColor','ConvexConcaveMask');nt.links.new(tex.outputs['Color'],sep.inputs[0])
   oldedge=nt.nodes['PhysicalEdgeMask']
   for link in list(oldedge.outputs[0].links):nt.links.new(sep.outputs['Red'],link.to_socket)
   cav=nt.nodes['CAVITY_MASK'];original=cav.inputs[0].links[0].from_socket
   enhanced=mathn(nt,'MAXIMUM',original,mathn(nt,'MULTIPLY',sep.outputs['Green'],.65));nt.links.new(enhanced,cav.inputs[0])
 assert fingerprint(me)==base[ob.name]['mesh_hash']
 if ob.name!='SRC_Head':assert uvhash==hashlib.sha256(np.array([u.uv[:] for u in me.uv_layers.active.data],np.float32).tobytes()).hexdigest()
 assert np.array_equal(uv_before[nonoptic],np.array([u.uv[:] for u in me.uv_layers.active.data],np.float32)[nonoptic])
 report[ob.name]={'geometry_unchanged':True,'non_optic_uv_unchanged':True,'optic_uv_planar_for_resolution':ob.name=='SRC_Head','uv_hash':uvhash}
(OUT/'m4-assignment.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'m4-procedural.blend'));print('M4_SETUP_COMPLETE',flush=True)
