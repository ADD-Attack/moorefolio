import bpy,json,os
D=os.environ.get('ASSEMBLY_WORKDIR','D:/OpenClaw/assembly-sol-op-20261017');O=os.environ.get('ASSEMBLY_OUTPUT',D+'/delivery');bpy.ops.wm.open_mainfile(filepath=O+'/snake-sectional.blend')
obs=bpy.data.objects;segments=[o for o in obs if o.name.startswith('Segment_')];assert len(segments)==28
assert len({o.data for o in segments})==1
assert len([o for o in obs if o.name.startswith('Lens_') and o.name.endswith('_ring_0')])==1
images=set()
for o in obs:
 if o.type=='MESH':
  for m in o.data.materials:
   if m and m.use_nodes:
    for n in m.node_tree.nodes:
     if n.type=='TEX_IMAGE' and n.image:images.add(n.image)
assert images and all(im.packed_file for im in images)
report={'reopened_blend':True,'rigid_segments':len(segments),'body_unique_meshes':1,'complete_lenses':1,'material_images':len(images),'all_material_images_packed':True,'master_curve_present':obs.get('MasterCurve') is not None,'render_size':[bpy.context.scene.render.resolution_x,bpy.context.scene.render.resolution_y]}
json.dump(report,open(O+'/blend-audit.json','w'),indent=2);print('BLEND_AUDIT_PASS',report,flush=True)
