extends "res://main.gd"
## Evidence scene only. The playable scene's mechanics and geometry are unchanged.
var production_model: Node3D
func _ready() -> void:
	super._ready()
	_start_game()
	set_process(false)
	var path: Array[Vector2i] = [Vector2i(-2,-2), Vector2i(-3,-2), Vector2i(-4,-2), Vector2i(-4,-1), Vector2i(-4,0), Vector2i(-3,0), Vector2i(-2,0), Vector2i(-2,1), Vector2i(-2,2)]
	snake = path
	_render_snake()
	var target := Vector2i(0,6)
	apple_root.position += Vector3(float(target.x-apple.x)*TILE,0,float(target.y-apple.y)*TILE)
	apple = target
	production_model = preload("res://models/snake_full.glb").instantiate()
	production_model.name = "ProductionSnake_LightingEvidence"
	add_child(production_model)
	production_model.rotation_degrees.y = -20.0
	production_model.position = Vector3(1.5,0,0.5)
	get_node("InGameMoodRig").add_collar_spill(production_model)
	score = 870
	high_score = 870
	elapsed = 42.0
	combo = 3
	last_apple_time = 40.0
	_update_hud()
	minimap.update_state(snake,apple)
func frame_head() -> void:
	var target := production_model.to_global(Vector3(2.45,0.63,-0.22))
	camera.position = target + Vector3(3.25,1.85,4.1)
	camera.look_at(target)
	camera.fov = 30.0
	hud_layer.visible = false
