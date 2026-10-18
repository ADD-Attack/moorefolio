import bpy,bmesh,numpy as np,sys,os,mathutils
from mathutils.bvhtree import BVHTree
from mathutils import Vector
p=sys.argv[sys.argv.index('--')+1];o=bpy.data.objects['HEAD_master'];S=1.3/.59;M=mathutils.Matrix.Scale(S,4)@mathutils.Matrix(((-1,0,0,.19),(0,-1,0,0),(0,0,1,-.435),(0,0,0,1)))
bm=bmesh.new();bm.from_mesh(o.data);bv=BVHTree.FromBMesh(bm);xx=np.linspace(-1.05,.19,400);zz=np.linspace(.19,.98,300)
for side in [-1,1]:
 Y=np.full((len(zz),len(xx)),np.nan)
 for j,z in enumerate(zz):
  for i,x in enumerate(xx):
   hit=bv.ray_cast(M@Vector((x,side*2,z)),Vector((0,side,0)))
   if hit[0] is not None:Y[j,i]=(M.inverted()@hit[0]).y*side
 np.savez(os.path.join(p,'head-depth-%d.npz'%side),x=xx,z=zz,y=Y)
