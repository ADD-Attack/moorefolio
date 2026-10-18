import bpy,sys,json
from mathutils import Vector
p=sys.argv[sys.argv.index('--')+1]
json.dump({o.name:[list(o.matrix_world@Vector(c)) for c in o.bound_box] for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render},open(p,'w'),indent=1)
