extends Node3D
const Framing = preload("res://lighting/framing.gd")
var camera: Camera3D
var model: Node3D
var rig: Node3D
func _ready() -> void:
	rig = preload("res://lighting/mood_rig.gd").new()
	add_child(rig)
	model = preload("res://models/snake_full.glb").instantiate()
	add_child(model)
	rig.add_collar_spill(model)
	camera = Camera3D.new()
	add_child(camera)
	camera.current = true
	camera.fov = 33.7
	frame_full()
func frame_full() -> void:
	Framing.fit(camera, model, Vector3(0.35,0.46,1.0), 0.84)
func frame_head() -> void:
	var head_transform: Transform3D = model.get_node("SnakeHead").transform
	model.queue_free()
	model = preload("res://models/snake_head.glb").instantiate()
	model.transform = head_transform
	add_child(model)
	rig.add_collar_spill(model)
	camera.fov = 30.0
	Framing.fit(camera, model, Vector3(0.65,0.36,1.0), 0.78)
