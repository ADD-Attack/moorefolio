"""Surface-derived volume repair. Rasterize actual clay triangles, close one-voxel
sampling gaps, fill enclosed section interiors, extract the surface. No fitted primitives.
The axial section fill closes the cut collar, not the exterior mouth/brow recesses.
"""
import sys,json,numpy as np,trimesh
from scipy import ndimage as ndi
from skimage.measure import marching_cubes
p,out=sys.argv[1:3];d=np.load(p);m=trimesh.Trimesh(d['v'],d['f'],process=False)
pitch=.006
vg=m.voxelized(pitch);occ=np.pad(vg.matrix,2);occ=ndi.binary_closing(occ,iterations=1)
for i in range(occ.shape[0]):occ[i]=ndi.binary_fill_holes(occ[i])
occ=ndi.binary_fill_holes(occ)
v,f,n,val=marching_cubes(occ.astype(np.float32),.5,spacing=(pitch,)*3)
v+=vg.transform[:3,3]-2*pitch
np.savez(out,v=v,f=f)
print(json.dumps({'source_vertices':len(m.vertices),'source_faces':len(m.faces),'pitch':pitch,'grid':list(occ.shape),'out_faces':len(f)}))
