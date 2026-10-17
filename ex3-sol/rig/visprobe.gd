extends SceneTree
## Visibility probe: places ONE magenta emissive box at a time at each position in
## PROBES, renders a frame per position, and saves /tmp/visprobe_<i>.png.
## vischeck.py then reports VISIBLE / NOT VISIBLE per index.
## Purpose: prove a planned art element is inside the camera frustum BEFORE
## building it (Snake AAA lesson, 2026-10-16: the back wall's visible slice is
## only y <= ~2.65 for the shipping camera; higher placements are invisible).

const PROBES := [
	Vector3(0, 5.6, -16.6),
	Vector3(0, 1.55, -16.68),
	Vector3(3.0, 1.0, 3.0),
]

func _init() -> void:
	var scene = load("res://main.tscn").instantiate()
	root.add_child(scene)
	_run(scene)

func _run(scene) -> void:
	for i in 10:
		await process_frame
	# Play state, not title: the title screen's dim overlay darkens the 3D view
	# and would mute the probe color below the checker's thresholds.
	scene._start_game()
	scene.set_process(false)
	for i in 4:
		await process_frame
	for idx in PROBES.size():
		var mat := StandardMaterial3D.new()
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mat.albedo_color = Color(1, 0, 1)
		var mesh := BoxMesh.new()
		mesh.size = Vector3(0.6, 0.6, 0.6)
		var node := MeshInstance3D.new()
		node.mesh = mesh
		node.material_override = mat
		node.position = PROBES[idx]
		scene.add_child(node)
		for i in 4:
			await process_frame
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png("/tmp/visprobe_%d.png" % idx)
		node.queue_free()
		print("VISPROBE ", idx, " at ", PROBES[idx], " saved")
	quit()
