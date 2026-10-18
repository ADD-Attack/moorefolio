import bpy,math,sys
from mathutils import Matrix
for i in range(6):
 angle=math.radians(-110)*(1 if i<4 else (6-i)/3)
 for name in [f'Segment_{i+1:02d}',f'Glow_{i+1:02d}']:
  o=bpy.data.objects[name];o.matrix_world=o.matrix_world@Matrix.Rotation(angle,4,'X')
bpy.ops.wm.save_as_mainfile(filepath=sys.argv[sys.argv.index('--')+1])
