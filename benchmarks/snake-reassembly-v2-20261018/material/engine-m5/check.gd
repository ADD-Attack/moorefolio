extends SceneTree
var total := 0
var meshes := 0
func walk(n: Node):
    if n is MeshInstance3D:
        meshes += 1
        for s in range(n.mesh.get_surface_count()):
            var ix = n.mesh.surface_get_array_index_len(s)
            total += int((ix if ix > 0 else n.mesh.surface_get_array_len(s)) / 3)
    for c in n.get_children():
        walk(c)
func _initialize():
    var packed = load("res://snake-p8-material.glb")
    if packed == null:
        push_error("GLB failed to load")
        quit(1)
        return
    var root = packed.instantiate()
    walk(root)
    print("P8_IMPORT meshes=", meshes, " triangles=", total)
    var f = FileAccess.open("res://import-report.json", FileAccess.WRITE)
    f.store_string(JSON.stringify({"meshes":meshes,"triangles":total,"pass":meshes==61 and total==57006}))
    root.free()
    quit(0 if meshes==61 and total==57006 else 1)
