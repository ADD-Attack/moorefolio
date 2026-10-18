"""Independent saved-blend budget and clay-purity audit. Blender -b asset.blend -P audit_fix.py -- out.json"""
import bpy,sys,json
from pathlib import Path
sc=bpy.context.scene
assets=[o for o in sc.objects if o.type=='MESH' and not o.hide_render and not o.name.startswith('STAGE_')]
def tris(o):
 o.data.calc_loop_triangles();return len(o.data.loop_triangles)
counts={o.name:tris(o) for o in assets}
head=counts['Head_node'];module=counts['Segment_07']+counts['Glow_07'];tail=sum(v for k,v in counts.items() if k.startswith(('Tail','Glow_T')));total=sum(counts.values())
checks={'head':head<=14000,'module_insert':module<=1450,'tail':tail<=3000,'assembly':30000<=total<=60000}
mats={m.name for o in assets for m in o.data.materials};checks['one_clay_material']=len(mats)==1
for o in assets:
 assert len(o.data.materials)==1,o.name
 for m in o.data.materials:
  p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
  assert p.inputs['Metallic'].default_value==0
  assert p.inputs['Emission Strength'].default_value==0
  assert p.inputs['Transmission Weight'].default_value==0
report={'counts':{'head':head,'module_insert':module,'tail':tail,'assembly':total},'checks':checks,'materials':sorted(mats),'visible_nodes':len(assets),'per_node':counts,'acceptance':'NOT asserted by technical audit'}
Path(sys.argv[sys.argv.index('--')+1]).write_text(json.dumps(report,indent=2));assert all(checks.values()),report
print('AUDIT_PASS',report['counts'])
