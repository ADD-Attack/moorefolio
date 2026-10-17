extends SceneTree
var failures: Array[String] = []
var poses: Array[Dictionary] = []
func check(value: bool, message: String) -> void:
	if not value:
		failures.append(message)

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	# Inspect the exported rest pose before the driver can correct it.
	var rest: Node3D = load("res://snake-sectional.glb").instantiate()
	root.add_child(rest)
	var rest_head := rest.find_child("Head",true,false) as Node3D
	var first_joint := rest.find_child("Joint_00_Housing",true,false) as Node3D
	check(rest_head.global_position.distance_to(first_joint.global_position)<0.001,"Exported neck joint escaped head socket")
	check(rest.find_children("Lens_*_ring_0","MeshInstance3D",true,false).size()==1,"Expected exactly one complete lens assembly")
	for i in range(28):
		var section := rest.find_child("Segment_%02d" % i,true,false) as Node3D
		var joint := rest.find_child("Joint_%02d_Housing" % i,true,false) as Node3D
		check(section.global_position.distance_to(joint.global_position)<0.55,"Exported joint escaped segment %d" % i)
	rest.queue_free()
	var driver = load("res://driver.tscn").instantiate()
	root.add_child(driver)
	await process_frame
	check(driver.segments.size() == 28, "Expected 28 rigid sections")
	var meshes: Array = driver.assembly.find_children("*", "MeshInstance3D", true, false)
	var triangles := 0
	var surfaces := 0
	for mi: MeshInstance3D in meshes:
		for s in range(mi.mesh.get_surface_count()):
			var arr := mi.mesh.surface_get_arrays(s)
			triangles += arr[Mesh.ARRAY_INDEX].size() / 3 if arr[Mesh.ARRAY_INDEX] != null else arr[Mesh.ARRAY_VERTEX].size() / 3
			surfaces += 1
			check(arr[Mesh.ARRAY_TANGENT] != null and arr[Mesh.ARRAY_TANGENT].size() > 0, "%s surface %d lacks tangents" % [mi.name, s])
			var mat := mi.mesh.surface_get_material(s) as StandardMaterial3D
			check(mat != null, "%s lacks material" % mi.name)
			if mat != null and "Gunmetal" in mat.resource_name:
				check(mat.albedo_texture != null and mat.normal_texture != null and mat.ao_texture != null and mat.roughness_texture != null and mat.metallic_texture != null, "%s missing PBR texture slots" % mi.name)
	check(triangles >= 30000 and triangles <= 60000, "Assembly budget failed: %d" % triangles)
	for pose in range(120):
		driver.set_pose(float(pose) * TAU / 120.0)
		var max_error := 0.0
		for i in range(28):
			var section: Node3D = driver.segments[i]
			check(section != null, "Missing segment %d" % i)
			if section == null:
				continue
			check(section.transform.is_finite(), "Pose %d nonfinite segment %d" % [pose, i])
			check(absf(section.basis.determinant() - 1.0) < 0.0001, "Pose %d nonrigid frame %d" % [pose, i])
			for label in ["Housing","GlowBars"]:
				var joint := driver.assembly.find_child("Joint_%02d_%s" % [i,label],true,false) as Node3D
				check(joint.global_position.distance_to(driver.path.curve.sample_baked(float(i)*driver.pitch))<0.001,"Pose %d joint placement %d" % [pose,i])
			var expected: Vector3 = driver.path.curve.sample_baked((float(i) + 0.5) * driver.pitch)
			max_error = maxf(max_error, section.position.distance_to(expected))
		check(max_error < 0.0001, "Pose %d arc placement error" % pose)
		poses.append({"pose": pose, "max_arc_position_error": max_error, "sections": 28})
	# Independent straight-path spacing and handedness assertion.
	driver.path.curve.clear_points()
	driver.path.curve.add_point(Vector3.ZERO)
	driver.path.curve.add_point(Vector3(28.0, 0.0, 0.0))
	driver.repose()
	for i in range(28):
		check(driver.segments[i].position.distance_to(Vector3(float(i) + 0.5, 0.0, 0.0)) < 0.001, "Straight-path spacing %d" % i)
	var standalone = load("res://head.glb").instantiate()
	root.add_child(standalone)
	check(standalone.find_child("Head", true, false) != null, "Standalone head did not instantiate")
	var report := {"engine": Engine.get_version_info(), "poses_tested": poses.size(), "triangles": triangles, "mesh_nodes": meshes.size(), "surfaces": surfaces, "failures": failures, "poses": poses, "pass": failures.is_empty()}
	FileAccess.open("res://selftest-result.json", FileAccess.WRITE).store_string(JSON.stringify(report, "\t"))
	print("SECTIONAL_SELFTEST ", "PASS" if failures.is_empty() else "FAIL", " poses=", poses.size(), " triangles=", triangles, " failures=", failures)
	standalone.queue_free()
	driver.queue_free()
	await process_frame
	quit(0 if failures.is_empty() else 1)
