import bpy
for o in bpy.context.scene.objects:
    if o.type=='MESH':
        bb=[o.matrix_world@__import__('mathutils').Vector(c) for c in o.bound_box]
        print('OBJ',o.name,'parent',o.parent.name if o.parent else None,'tris',len(o.data.polygons),'min',tuple(round(min(v[i] for v in bb),2) for i in range(3)),'max',tuple(round(max(v[i] for v in bb),2) for i in range(3)),'hide',o.hide_render)
