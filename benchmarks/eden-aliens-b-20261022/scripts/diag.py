import bpy,bmesh
for o in bpy.context.scene.objects:
    if o.type!='MESH': continue
    bm=bmesh.new(); bm.from_mesh(o.data)
    fold=sum(1 for e in bm.edges if len(e.link_faces)==2 and e.link_faces[0].normal.dot(e.link_faces[1].normal)<-0.3)
    nm=sum(1 for e in bm.edges if not e.is_manifold); bd=sum(1 for e in bm.edges if e.is_boundary)
    print('DIAG',o.name,'folds',fold,'nonmanifold',nm,'boundary',bd,'zeroarea',sum(1 for f in bm.faces if f.calc_area()<1e-9))
