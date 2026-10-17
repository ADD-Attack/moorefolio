extends SceneTree
## Evidence-only native capture fixture. Not the Path3D driver implementation.
func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	root.content_scale_size = Vector2i(1920,1080)
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_VIEWPORT
	var stage := Node3D.new()
	root.add_child(stage)
	var environment := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.32, 0.32, 0.32)
	var sky := Sky.new()
	var sky_mat := ProceduralSkyMaterial.new()
	sky_mat.sky_top_color = Color(0.46,0.49,0.52)
	sky_mat.sky_horizon_color = Color(0.68,0.68,0.68)
	sky_mat.ground_bottom_color = Color(0.22,0.23,0.25)
	sky_mat.ground_horizon_color = Color(0.65,0.65,0.65)
	sky.sky_material = sky_mat
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	env.ambient_light_energy = 0.55
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	environment.environment = env
	stage.add_child(environment)
	for spec in [[Vector3(-4,8,6), 1.8, Color(1,.96,.91)], [Vector3(5,6,-4), 1.0, Color(.88,.94,1)]]:
		var light := DirectionalLight3D.new()
		stage.add_child(light)
		light.position = spec[0]
		light.light_energy = spec[1]
		light.light_color = spec[2]
		light.look_at(Vector3(0,1.5,0))
	var camera := Camera3D.new()
	stage.add_child(camera)
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.current = true
	var driver = load("res://driver.tscn").instantiate()
	stage.add_child(driver)
	await process_frame
	fit(camera, driver.assembly, Vector3(-7,7,12))
	await settle()
	assert(root.get_texture().get_image().get_size() == Vector2i(1920,1080))
	var err := root.get_texture().get_image().save_png("res://godot-full-body.png")
	assert(err == OK)
	driver.queue_free()
	await process_frame
	var head: Node3D = load("res://head.glb").instantiate()
	stage.add_child(head)
	fit(camera, head, Vector3(-2,1.0,5))
	await settle()
	err = root.get_texture().get_image().save_png("res://godot-head-closeup.png")
	assert(err == OK)
	print("NATIVE_CAPTURE_PASS viewport=",root.get_texture().get_image().get_size()," renderer=",RenderingServer.get_current_rendering_method())
	quit()

func settle() -> void:
	for i in range(12):
		await process_frame
	await RenderingServer.frame_post_draw

func fit(camera: Camera3D, model: Node3D, direction: Vector3) -> void:
	var bounds := AABB()
	var first := true
	for mi: MeshInstance3D in model.find_children("*","MeshInstance3D",true,false):
		var box: AABB = mi.global_transform * mi.get_aabb()
		bounds = box if first else bounds.merge(box)
		first = false
	var center := bounds.get_center()
	camera.position = center + direction.normalized() * 20.0
	camera.look_at(center)
	var xmin := INF
	var xmax := -INF
	var ymin := INF
	var ymax := -INF
	for mi: MeshInstance3D in model.find_children("*","MeshInstance3D",true,false):
		for surf in range(mi.mesh.get_surface_count()):
			var vertices: PackedVector3Array = mi.mesh.surface_get_arrays(surf)[Mesh.ARRAY_VERTEX]
			for v in vertices:
				var local := camera.global_transform.affine_inverse() * (mi.global_transform * v)
				xmin = minf(xmin, local.x)
				xmax = maxf(xmax, local.x)
				ymin = minf(ymin, local.y)
				ymax = maxf(ymax, local.y)
	camera.position += camera.basis.x * ((xmin+xmax)*0.5) + camera.basis.y * ((ymin+ymax)*0.5)
	camera.size = maxf(ymax-ymin, (xmax-xmin)/(1920.0/1080.0)) * 1.12
	print("CAMERA center=",center," position=",camera.position," ortho_height=",camera.size)
