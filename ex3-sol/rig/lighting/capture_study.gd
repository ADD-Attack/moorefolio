extends SceneTree
var output_root: String
func _init() -> void:
	var parent := ProjectSettings.globalize_path("res://..").simplify_path()
	output_root = parent if DirAccess.dir_exists_absolute(parent.path_join("captures")) else parent.path_join("deliverables")
	DirAccess.make_dir_recursive_absolute(output_root.path_join("captures"))
	call_deferred("run")
func settle(frames: int = 12) -> void:
	for i in frames: await process_frame
	await RenderingServer.frame_post_draw
func save(label: String) -> void:
	var path := output_root.path_join("captures").path_join(label + ".png")
	var img := root.get_texture().get_image()
	var err := img.save_png(path)
	assert(err == OK, "Capture could not be saved: " + path)
	print("CAPTURE ", label, " ", img.get_size(), " result=", err)
func check_materials(model: Node3D) -> void:
	var textured := 0
	for mesh in model.find_children("*", "MeshInstance3D", true, false):
		for s in mesh.mesh.get_surface_count():
			var mat = mesh.mesh.surface_get_material(s)
			assert(mat != null,"Null imported material")
			if mat.resource_name == "SnakePlate" or mat.resource_name == "SnakePlateDark":
				assert(mat.albedo_texture != null, "Missing albedo after import")
				assert(mat.normal_texture != null, "Missing normal after import")
				assert(mat.roughness_texture != null, "Missing roughness after import")
				textured += 1
	assert(textured > 0,"No plate textures found")
	print("MATERIAL CHECK: ", textured, " textured plate surfaces; original materials intact")
func record_lights(scene: Node, label: String) -> void:
	var data: Array = []
	for light in scene.find_children("*", "Light3D", true, false):
		var entry := {"path": str(scene.get_path_to(light)), "type": light.get_class(), "color_srgb": light.light_color.to_html(false), "energy": light.light_energy, "position_world": str(light.global_position), "rotation_degrees_world": str(light.global_rotation_degrees), "shadows": light.shadow_enabled, "specular": light.light_specular}
		if light is OmniLight3D:
			entry["range"] = light.omni_range
			entry["attenuation"] = light.omni_attenuation
			entry["size"] = light.light_size
		else: entry["angular_distance"] = light.light_angular_distance
		data.append(entry)
	var file := FileAccess.open(output_root.path_join(label + "-lights.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(data,"\t")+"\n")
func run() -> void:
	var staging = load("res://lighting/staging.tscn").instantiate()
	root.add_child(staging)
	check_materials(staging.model)
	await settle(24)
	record_lights(staging,"staging")
	save("staging-full")
	staging.frame_head()
	await settle()
	record_lights(staging,"staging-head")
	save("staging-head")
	staging.queue_free()
	await process_frame
	var scene = load("res://lighting/ingame_study.tscn").instantiate()
	root.add_child(scene)
	check_materials(scene.production_model)
	await settle(24)
	record_lights(scene,"ingame")
	save("ingame-full")
	scene.frame_head()
	await settle()
	save("ingame-head")
	quit()
