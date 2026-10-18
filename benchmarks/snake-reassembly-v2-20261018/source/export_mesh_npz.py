import bpy,numpy as np,sys
p=sys.argv[sys.argv.index('--')+1:];o=bpy.data.objects[p[0]];o.data.calc_loop_triangles()
np.savez(p[1],v=np.array([v.co[:] for v in o.data.vertices]),f=np.array([t.vertices[:] for t in o.data.loop_triangles]))
