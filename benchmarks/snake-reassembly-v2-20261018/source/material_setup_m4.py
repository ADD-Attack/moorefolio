"""M4 material-only replacement. Start from M3 procedural blend, keep all UVs and geometry.
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
 fine=noise(nt,co,135,2,'MachinedPitting');grain=noise(nt,co,42,2,'FineGrain')
 streak=noise(nt,co,1,2,'DirectionalScuff', (9,145,95))
 breakup=noise(nt,co,22,2,'WearBreakup')
 edge=mask(nt,geo.outputs['Pointiness'],.505,.55,'ConvexEdgeMask')
 edge=mathn(nt,'MULTIPLY',edge,mask(nt,breakup,.27,.65,'BrokenEdges'))
 ao=node(nt,'ShaderNodeAmbientOcclusion','LocalAO');ao.inputs['Distance'].default_value=.07;ao.samples=32;ao.only_local=True
 grime=mathn(nt,'SUBTRACT',1,ao.outputs['AO'])
 # Tiny connected-component shifts, never invented Voronoi plates.
 step=ramp(nt,geo.outputs['Random Per Island'],[(0,tuple(c*.94 for c in base)),(1,tuple(c*1.04 for c in base))],'ComponentTint')
 color=mix(nt,step,tuple(c*.80 for c in base),mathn(nt,'MULTIPLY',grain,.24),'GrainTone')
 color=mix(nt,color,rgb('34312A'),mathn(nt,'MULTIPLY',grime,.60),'RecessGrime')
 scratch=mask(nt,streak,.67,.76,'NarrowScratches');scratch=mathn(nt,'MULTIPLY',scratch,mask(nt,breakup,.42,.60,'InterruptedScratch'))
 # Scratches concentrate near convex edges but don't vanish entirely on plate faces.
 scratch=mathn(nt,'MULTIPLY',scratch,mathn(nt,'ADD',.14,mathn(nt,'MULTIPLY',edge,.86)))
 color=mix(nt,color,rgb('B4B3AA'),mathn(nt,'MULTIPLY',edge,.42),'EdgePolish')
 color=mix(nt,color,rgb('B9B8AE'),mathn(nt,'MULTIPLY',scratch,.55),'FineScuffColor')
 rustfield=noise(nt,co,1,2,'OxideRuns',(48,48,5))
 rust=mask(nt,rustfield,.66,.78,'SparseOxide');rust=mathn(nt,'MULTIPLY',rust,mathn(nt,'MINIMUM',1,mathn(nt,'ADD',mathn(nt,'MULTIPLY',grime,1.4),mathn(nt,'MULTIPLY',edge,.7))))
 color=mix(nt,color,rgb('6A4930'),mathn(nt,'MULTIPLY',rust,.60),'RestrainedBrownOxide')
 rr=mathn(nt,'ADD',rough,mathn(nt,'MULTIPLY',mathn(nt,'SUBTRACT',grain,.5),.09))
 rr=mathn(nt,'SUBTRACT',rr,mathn(nt,'MULTIPLY',edge,.075));rr=mathn(nt,'ADD',rr,mathn(nt,'MULTIPLY',rust,.13))
 height=mathn(nt,'SUBTRACT',mathn(nt,'MULTIPLY',fine,.28),mathn(nt,'MULTIPLY',scratch,.25))
 bump=node(nt,'ShaderNodeBump','FineMachiningOnly');bump.inputs['Strength'].default_value=.32;bump.inputs['Distance'].default_value=.0009;nt.links.new(height,bump.inputs['Height']);nt.links.new(bump.outputs[0],p.inputs['Normal'])
 metal=mathn(nt,'SUBTRACT',.98,mathn(nt,'MULTIPLY',rust,.55))
 if kind in ('dark','grille'):metal=const(nt,.85,'DarkMetal');bump.inputs['Distance'].default_value=.0005
 emission=const(nt,0,'NoEmission')
 if kind=='glow':
  color=ramp(nt,grain,[(0,rgb('45AC98')),(1,rgb('8DE1CA'))],'InsertTint');emission=color;metal=const(nt,.10,'InsertMetal');rr=const(nt,.32,'InsertRough');p.inputs['Emission Strength'].default_value=1.2
 for s,n in [(color,'BAKE_COLOR'),(rr,'BAKE_ROUGH'),(metal,'BAKE_METAL'),(ao.outputs['AO'],'BAKE_AO'),(emission,'BAKE_EMISSION')]:output(nt,s,n)
 for s,k in [(color,'Base Color'),(rr,'Roughness'),(metal,'Metallic'),(emission,'Emission Color')]:nt.links.new(s,p.inputs[k])
 m.diffuse_color=(*base,1);return m
palette={'Gunmetal_00':('99978D',.46,'metal'),'Gunmetal_01':('A09C91',.44,'metal'),'Gunmetal_02':('949287',.49,'metal'),'Gunmetal_03':('9D9789',.47,'metal'),'DarkHousing':('494B47',.57,'dark'),'MachinedSteel':('ABA99F',.38,'metal'),'RecessedGrille':('4C4B44',.59,'grille'),'FinInset':('858379',.48,'metal'),'TealInsert':('71CCBD',.32,'glow')}
new={k:make(k,rgb(h),r,kind) for k,(h,r,kind) in palette.items()}
base=json.load(open(OUT/'inventory.json'));report={}
for ob in [o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('SRC_')]:
 me=ob.data;assert fingerprint(me)==base[ob.name]['mesh_hash'];uvhash=hashlib.sha256(np.array([u.uv[:] for u in me.uv_layers.active.data],np.float32).tobytes()).hexdigest()
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
   # Core diameter / disc diameter = .28; crisp mint annulus and teal perimeter.
   col=ramp(nt,radius,[(0,rgb('FFFFFF')),(.28,rgb('FFFFFF')),(.295,rgb('55D8B1')),(.47,rgb('55D8B1')),(.49,rgb('B0FFE5')),(.57,rgb('B0FFE5')),(.59,rgb('25876B')),(.83,rgb('25876B')),(.85,rgb('63C4A5')),(.89,rgb('63C4A5')),(.91,rgb('123E33')),(1,rgb('123E33'))],'SharpRadialTarget')
   em=ramp(nt,radius,[(0,(1,1,1)),(.28,(1,1,1)),(.295,(.035,.30,.16)),(.47,(.035,.30,.16)),(.49,(.25,.8,.53)),(.57,(.25,.8,.53)),(.59,(.005,.045,.025)),(.83,(.005,.045,.025)),(.85,(.025,.2,.12)),(.89,(.025,.2,.12)),(.91,(0,0,0)),(1,(0,0,0))],'LensEmission')
   for l in list(p.inputs['Normal'].links):nt.links.remove(l)
   for s,k in [(col,'BAKE_COLOR'),(em,'BAKE_EMISSION'),(const(nt,.24,'OpticRough'),'BAKE_ROUGH'),(const(nt,.15,'OpticMetal'),'BAKE_METAL')]:nt.links.new(s,nt.nodes[k].inputs[0])
   nt.links.new(col,p.inputs['Base Color']);nt.links.new(em,p.inputs['Emission Color']);nt.links.new(nt.nodes['BAKE_ROUGH'].outputs[0],p.inputs['Roughness']);nt.links.new(nt.nodes['BAKE_METAL'].outputs[0],p.inputs['Metallic']);p.inputs['Emission Strength'].default_value=3
   me.materials[slot]=m
  elif old.name in new:me.materials[slot]=new[old.name]
  else:raise RuntimeError('Unknown M3 material '+old.name)
 assert fingerprint(me)==base[ob.name]['mesh_hash'];assert uvhash==hashlib.sha256(np.array([u.uv[:] for u in me.uv_layers.active.data],np.float32).tobytes()).hexdigest()
 report[ob.name]={'geometry_unchanged':True,'uv_unchanged':True,'uv_hash':uvhash}
(OUT/'m4-assignment.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'m4-procedural.blend'));print('M4_SETUP_COMPLETE',flush=True)
