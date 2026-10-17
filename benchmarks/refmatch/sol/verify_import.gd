extends SceneTree
var failures: int = 0
func _init():
 for filename in ["snake_head.glb", "snake_segment.glb", "snake_full.glb"]:
  var resource = load("res://models/" + filename) as PackedScene
  if not resource:
   push_error("Missing PackedScene: " + filename)
   failures += 1
   continue
  var instance = resource.instantiate()
  var stats = {"meshes":0,"surfaces":0,"triangles":0,"materials":0,"missing_materials":0,"normal_textured":0,"tangent_surfaces":0}
  inspect(instance,stats)
  print("IMPORT_CHECK ", filename, " ", JSON.stringify(stats))
  if stats.missing_materials > 0 or stats.meshes == 0:
   failures += 1
  instance.free()
 print("IMPORT_RESULT ", "PASS" if failures == 0 else "FAIL")
 quit(failures)
func inspect(node: Node, stats: Dictionary):
 if node is MeshInstance3D:
  var mesh = node.mesh
  stats.meshes += 1
  for i in range(mesh.get_surface_count()):
   stats.surfaces += 1
   var arrays = mesh.surface_get_arrays(i)
   var indices = arrays[Mesh.ARRAY_INDEX]
   stats.triangles += indices.size()/3 if indices != null and indices.size() > 0 else arrays[Mesh.ARRAY_VERTEX].size()/3
   if arrays[Mesh.ARRAY_TANGENT] != null and arrays[Mesh.ARRAY_TANGENT].size()>0: stats.tangent_surfaces += 1
   var material = mesh.surface_get_material(i)
   if material is StandardMaterial3D:
    stats.materials += 1
    if material.normal_enabled and material.normal_texture: stats.normal_textured += 1
    if material.albedo_texture:
     assert(material.albedo_texture.get_width()>0)
   else: stats.missing_materials += 1
 for child in node.get_children(): inspect(child,stats)
