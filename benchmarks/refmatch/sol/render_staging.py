"""Neutral seamless review staging. No game environment, HUD or extra models.
Run blender -b snake.blend --python render_staging.py [-- preview|final]
"""
import bpy,os,sys,math
from mathutils import Vector
ROOT=os.path.dirname(os.path.abspath(__file__));s=bpy.context.scene
mode=sys.argv[-1] if '--' in sys.argv else 'preview'
for o in list(bpy.data.objects):
 if o.type in ['LIGHT','CAMERA'] or o.name.startswith('Review'):bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.mesh.primitive_plane_add(size=200);g=bpy.context.object;g.name='Review_Backdrop'
m=bpy.data.materials.new('Review_Neutral_Gray');m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.32,.32,.32,1);p.inputs['Roughness'].default_value=.9;g.data.materials.append(m)
s.world.use_nodes=True;s.world.node_tree.nodes.get('Background').inputs[0].default_value=(.32,.32,.32,1);s.world.node_tree.nodes.get('Background').inputs[1].default_value=.5
def aim(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
for name,pos,energy,size in [('Key',(-3,-6,10),1800,7),('Fill',(5,-1,7),1300,6),('Rim',(1,6,9),2200,5)]:
 d=bpy.data.lights.new('Review_'+name,'AREA');d.energy=energy;d.shape='DISK';d.size=size;o=bpy.data.objects.new(d.name,d);bpy.context.collection.objects.link(o);o.location=pos;aim(o,(0,0,1.5))
s.render.engine='CYCLES';s.cycles.samples=24 if mode=='preview' else 80;s.cycles.use_denoise=True
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='CUDA';prefs.get_devices()
 for d in prefs.devices:d.use=d.type=='CUDA';print('RENDER_DEVICE',d.name,d.type,d.use)
 if any(d.type=='CUDA' for d in prefs.devices):s.cycles.device='GPU'
except Exception as e:print('CPU_FALLBACK',e)
s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast'
s.render.image_settings.file_format='PNG';s.render.film_transparent=False
# Low bloom is review-only. Emissive bars themselves exist in the GLBs.
s.use_nodes=True;nt=s.node_tree;nt.nodes.clear();rl=nt.nodes.new('CompositorNodeRLayers');gl=nt.nodes.new('CompositorNodeGlare');gl.glare_type='FOG_GLOW';gl.quality='HIGH';gl.threshold=2;gl.mix=-.94;co=nt.nodes.new('CompositorNodeComposite');nt.links.new(rl.outputs['Image'],gl.inputs['Image']);nt.links.new(gl.outputs['Image'],co.inputs['Image'])
for name,pos,target,ortho,rx,ry in [('full',(-8,-16,8),(-.35,-.1,2.15),10.4,1920,1440),('head',(-5.4,-7.4,5.8),(-3.45,.05,4.2),4.6,1600,1200)]:
 d=bpy.data.cameras.new('Review_'+name);d.type='ORTHO';d.ortho_scale=ortho;o=bpy.data.objects.new(d.name,d);bpy.context.collection.objects.link(o);o.location=pos;aim(o,target);s.camera=o
 s.render.resolution_x=rx;s.render.resolution_y=ry;s.render.resolution_percentage=50 if mode=='preview' else 100
 s.render.filepath=os.path.join(ROOT,('preview-' if mode=='preview' else 'staging-')+name+'.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'snake.blend'))
