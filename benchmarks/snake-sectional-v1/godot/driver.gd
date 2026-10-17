extends Node3D
## +X is section-forward. Curve is Godot +Y-up. All section transforms are rigid.
var assembly: Node3D
var path: Path3D
var segments: Array[Node3D] = []
var baseline: Array[Vector3] = []
var pitch: float = 0.0

func _ready() -> void:
	assembly = load("res://snake-sectional.glb").instantiate()
	add_child(assembly)
	path = Path3D.new()
	path.name = "MasterPath3D"
	path.curve = Curve3D.new()
	path.curve.bake_interval = 0.015
	add_child(path)
	var source: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://path.json"))
	for p: Array in source.points:
		baseline.append(Vector3(float(p[0]), float(p[2]), -float(p[1])))
	for i in range(28):
		segments.append(assembly.find_child("Segment_%02d" % i, true, false) as Node3D)
	set_pose(0.0)

func set_pose(phase: float) -> void:
	path.curve.clear_points()
	for i in range(baseline.size()):
		var p := baseline[i]
		# Gentle path deformation, never mesh deformation.
		p.z += sin(float(i) * 0.04 + phase) * 0.10 * sin(float(i) / float(baseline.size()) * PI)
		p.y += sin(float(i) * 0.03 + phase) * 0.035
		path.curve.add_point(p)
	repose()

func frame_at(distance: float) -> Transform3D:
	var length := path.curve.get_baked_length()
	var p := path.curve.sample_baked(clampf(distance, 0.0, length))
	var a := path.curve.sample_baked(clampf(distance - 0.025, 0.0, length))
	var b := path.curve.sample_baked(clampf(distance + 0.025, 0.0, length))
	var x := (b - a).normalized()
	var z := x.cross(Vector3.UP).normalized()
	if z.length_squared() < 0.5:
		z = x.cross(Vector3.FORWARD).normalized()
	var y := z.cross(x).normalized()
	return Transform3D(Basis(x, y, z), p)

func repose() -> void:
	pitch = path.curve.get_baked_length() / 28.0
	for i in range(segments.size()):
		segments[i].transform = frame_at((float(i) + 0.5) * pitch)
		for label in ["Housing", "GlowBars"]:
			var joint := assembly.find_child("Joint_%02d_%s" % [i, label], true, false) as Node3D
			joint.global_transform = global_transform * frame_at(float(i) * pitch)
	(assembly.find_child("Head", true, false) as Node3D).transform = frame_at(0.0)
	(assembly.find_child("Tail", true, false) as Node3D).transform = frame_at(path.curve.get_baked_length())
