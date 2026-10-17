extends RefCounted
## Fit the actual imported bounds, never infer framing from authored origins.
static func bounds_of(model: Node3D) -> AABB:
	var bounds := AABB()
	var first := true
	for n in model.find_children("*", "MeshInstance3D", true, false):
		var box: AABB = n.global_transform * n.get_aabb()
		bounds = box if first else bounds.merge(box)
		first = false
	return bounds
static func fit(camera: Camera3D, model: Node3D, direction: Vector3, occupancy: float = 0.82) -> void:
	var box := bounds_of(model)
	var center := box.get_center()
	var back := direction.normalized()
	var right := Vector3.UP.cross(back).normalized()
	var up := back.cross(right).normalized()
	var aspect := camera.get_viewport().get_visible_rect().size.aspect()
	var tangent := tan(deg_to_rad(camera.fov * 0.5))
	var distance := 0.0
	for i in 8:
		var p := box.get_endpoint(i) - center
		distance = maxf(distance, absf(p.dot(right)) / (tangent * aspect * occupancy) + p.dot(back))
		distance = maxf(distance, absf(p.dot(up)) / (tangent * occupancy) + p.dot(back))
	camera.position = center + back * distance
	camera.look_at(center)
	print("FRAMING position=", camera.position, " target=",center," fov=",camera.fov)
