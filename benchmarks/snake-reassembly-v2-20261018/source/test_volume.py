import bpy,sys,os,numpy as np,math
sys.path.append(os.path.dirname(__file__));from lib import *
a=sys.argv[sys.argv.index('--')+1:];reset();d=np.load(os.path.join(a[0],'head-volume.npz'))
me=bpy.data.meshes.new('clay-volume');me.from_pydata(d['v'].tolist(),[],d['f'].tolist());me.update();o=bpy.data.objects.new('test_volume',me);bpy.context.collection.objects.link(o);bpy.context.view_layer.objects.active=o
m=o.modifiers.new('reduce','DECIMATE');m.ratio=11000/tris(o);m.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=m.name)
for f in me.polygons:f.use_smooth=True
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(a[0],'head-volume-test.blend'))
