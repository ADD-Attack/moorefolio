"""M5 shader-only correction from M4 procedural; mesh/UV/transforms immutable."""
import bpy,sys,os,json,hashlib,numpy as np
from pathlib import Path
T=Path(sys.argv[sys.argv.index('--')+1]);os.chdir(T);OUT=T/'material'
exec((T/'source/material_setup.py').read_text().split('def material(')[0])
def noise(nt,co,stretch,name):
 v=node(nt,'ShaderNodeVectorMath',name+'Scale');v.operation='MULTIPLY';nt.links.new(co,v.inputs[0]);v.inputs[1].default_value=stretch
 n=node(nt,'ShaderNodeTexNoise',name);n.inputs['Scale'].default_value=1;n.inputs['Detail'].default_value=2;nt.links.new(v.outputs[0],n.inputs['Vector']);return n.outputs['Fac']
def mask(nt,x,lo,hi,name):return ramp(nt,x,[(lo,(0,)*3),(hi,(1,)*3)],name)
def route(nt,s,name):nt.links.new(s,nt.nodes[name].inputs[0])
before={o.name:(fingerprint(o.data),hashlib.sha256(np.array([u.uv[:] for u in o.data.uv_layers.active.data],np.float32).tobytes()).hexdigest()) for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('SRC_')}
# Replace tail's coarse face-centre grille assignment with a per-shading-point window.
tail=bpy.data.objects['SRC_TailTip'];tail.data.materials[6]=tail.data.materials[1]
used={m for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('SRC_') for m in o.data.materials if m}
for m in used:
 nt=m.node_tree;p=nt.nodes.get('Surface')
 if not p:continue
 if 'Optic_' in m.name:continue
 co=nt.nodes['Coordinates'].outputs['Object']
 if 'TealInsert' in m.name:
  # Narrow optical band on the existing insert: dark edge rails, no mesh hiding.
  xyz=node(nt,'ShaderNodeSeparateXYZ','M5InsertAxes');nt.links.new(co,xyz.inputs[0])
  x=xyz.outputs['X'];x0=min(v.co.x for v in bpy.data.objects['SRC_GlowInsert'].data.vertices);x1=max(v.co.x for v in bpy.data.objects['SRC_GlowInsert'].data.vertices)
  # Taper insert has its own local X interval; use Generated coordinates instead.
  nt.links.new(nt.nodes['Coordinates'].outputs['Generated'],xyz.inputs[0])
  band=mathn(nt,'MULTIPLY',mask(nt,xyz.outputs['X'],.12,.24,'InsertLeftRail'),mathn(nt,'SUBTRACT',1,mask(nt,xyz.outputs['X'],.76,.88,'InsertRightRail')))
  col=mix(nt,rgb('263E38'),rgb('45B99B'),band,'M5InsertColor')
  em=mix(nt,(0,0,0),rgb('47CBA7'),mathn(nt,'MULTIPLY',band,.52),'M5InsertEmission')
  route(nt,col,'BAKE_COLOR');route(nt,em,'BAKE_EMISSION');nt.links.new(col,p.inputs['Base Color']);nt.links.new(em,p.inputs['Emission Color']);continue
 if 'DarkHousing' in m.name or 'RecessedGrille' in m.name:continue
 # Steel palette variation belongs to actual existing components, never invented cells.
 old=nt.nodes['BAKE_COLOR'].inputs[0].links[0].from_socket
 edge=nt.nodes['ConvexConcaveMask'].outputs['Red'] if 'ConvexConcaveMask' in nt.nodes else nt.nodes['PhysicalEdgeMask'].outputs[0]
 grain=noise(nt,co,(45,45,45),'M5Breakup');edge=mathn(nt,'MULTIPLY',edge,mask(nt,grain,.30,.64,'M5BrokenEdge'))
 # Stronger narrow polish at existing physical boundaries; subdued warm grime shoulders.
 col=mix(nt,old,rgb('B8B6AB'),mathn(nt,'MULTIPLY',edge,.82),'M5BoundaryPolish')
 runs=noise(nt,co,(36,60,5),'M5StreakField');runmask=mask(nt,runs,.56,.72,'M5FineRuns')
 cavity=nt.nodes['CAVITY_MASK'].outputs[0]
 deposit=mathn(nt,'MULTIPLY',runmask,mathn(nt,'ADD',.06,mathn(nt,'MULTIPLY',cavity,.65)))
 col=mix(nt,col,rgb('514A3B'),deposit,'M5WarmDeposits')
 scuff=noise(nt,co,(7,180,120),'M5FineScuffs');scuff=mask(nt,scuff,.64,.73,'M5ScuffThreshold')
 col=mix(nt,col,rgb('B0AEA3'),mathn(nt,'MULTIPLY',scuff,.22),'M5HairlineColor')
 rr=nt.nodes['BAKE_ROUGH'].inputs[0].links[0].from_socket
 rr=mathn(nt,'SUBTRACT',rr,mathn(nt,'MULTIPLY',edge,.12));rr=mathn(nt,'ADD',rr,mathn(nt,'MULTIPLY',deposit,.18))
 bump=nt.nodes['FineMachiningOnly'];bump.inputs['Distance'].default_value=.00065;bump.inputs['Strength'].default_value=.35
 # Tail shell and fins remain metal. Darken only the precise vent windows per point.
 if 'SRC_TailTip' in m.name:
  xyz=node(nt,'ShaderNodeSeparateXYZ','M5TailAxes');nt.links.new(co,xyz.inputs[0]);x,y,z=[xyz.outputs[k] for k in 'XYZ']
  def inside(v,a,b):return mathn(nt,'MULTIPLY',mathn(nt,'GREATER_THAN',v,a),mathn(nt,'LESS_THAN',v,b))
  top=mathn(nt,'MULTIPLY',inside(x,-.816,-.484),inside(y,-.098,.098));top=mathn(nt,'MULTIPLY',top,inside(z,.015,.18))
  side=mathn(nt,'MULTIPLY',inside(x,-1.116,-.864),inside(z,-.076,.031));side=mathn(nt,'MULTIPLY',side,mathn(nt,'GREATER_THAN',mathn(nt,'ABSOLUTE',y),.065))
  vent=mathn(nt,'MAXIMUM',top,side)
  col=mix(nt,col,rgb('343A35'),vent,'M5ConfinedTailVent');rr=mathn(nt,'ADD',rr,mathn(nt,'MULTIPLY',vent,.08))
 route(nt,col,'BAKE_COLOR');route(nt,rr,'BAKE_ROUGH');nt.links.new(col,p.inputs['Base Color']);nt.links.new(rr,p.inputs['Roughness'])
after={o.name:(fingerprint(o.data),hashlib.sha256(np.array([u.uv[:] for u in o.data.uv_layers.active.data],np.float32).tobytes()).hexdigest()) for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('SRC_')}
assert before==after
(OUT/'m5-shader-audit.json').write_text(json.dumps({'geometry_and_uv_exactly_unchanged':True,'fingerprints':after},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'m5-procedural.blend'));print('M5_SHADER_PASS')
