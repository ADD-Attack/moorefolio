import unreal, json
fbx = r"G:\UnrealProjects\TorchVizDemo\DemoData\forge_snake_rigged.fbx"
opt = unreal.FbxImportUI()
opt.import_mesh = True; opt.import_as_skeletal = True; opt.import_materials = True; opt.import_textures = True
opt.import_animations = False; opt.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
opt.skeletal_mesh_import_data.set_editor_property("import_morph_targets", False)
t = unreal.AssetImportTask(); t.filename = fbx; t.destination_path = "/Game/RigCheck"; t.automated = True; t.save = True; t.replace_existing = True; t.options = opt
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
res = {"imported": list(t.imported_object_paths)}
for p in t.imported_object_paths:
    a = unreal.load_asset(p); res.setdefault("classes", {})[p] = a.get_class().get_name()
    if isinstance(a, unreal.SkeletalMesh):
        b = a.get_bounds(); ib = a.get_imported_bounds()
        res["bounds_origin"] = [b.origin.x, b.origin.y, b.origin.z]; res["bounds_extent"] = [b.box_extent.x, b.box_extent.y, b.box_extent.z]
        res["imported_extent"] = [ib.box_extent.x, ib.box_extent.y, ib.box_extent.z]; res["imported_origin"]=[ib.origin.x, ib.origin.y, ib.origin.z]
        sk = a.skeleton; res["skeleton"] = sk.get_path_name() if sk else None
        res["materials"] = len(a.materials)
        lod = unreal.EditorSkeletalMeshLibrary if hasattr(unreal, "EditorSkeletalMeshLibrary") else None
        try: res["lod0_tris"] = a.get_editor_subsystem if False else unreal.SkeletalMeshEditorSubsystem and None
        except Exception: pass
unreal.EditorAssetLibrary.save_directory("/Game/RigCheck")
a = unreal.load_asset("/Game/RigCheck/forge_snake_rigged")
sk = a.skeleton
res["skeleton"] = sk.get_path_name() if sk else None
try: res["lod0_verts"] = unreal.EditorSkeletalMeshLibrary.get_num_verts(a, 0)
except Exception as e: res["lod0_verts"] = str(e)
open(r"C:\Users\Moore\AppData\Local\Temp\ScratchRigCheck\rigcheck.json","w").write(json.dumps(res, indent=1))
