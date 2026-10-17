extends SceneTree
## Exercise 1 (MODELS) demo capture: the game's own primitive snake on the
## left of the arena, the production glTF snake (head + segments) posed on
## the right, shot at the shipping camera; then a beauty close-up of the
## production head. Follows harness conventions: the game process is
## frozen after setup, so _process-fed UI (HUD, minimap) is fed manually.

const OUT_DIR := "/home/hatch/workspace/snake-aaa-modeling/captures"
const TILE := 1.2

var prod_head_pos := Vector3.ZERO
var prod_head_dir := Vector3.RIGHT


func _init() -> void:
	var scene = load("res://main.tscn").instantiate()
	root.add_child(scene)
	_run(scene)


func _basis_along(d: Vector3) -> Basis:
	var x := d.normalized()
	var z := x.cross(Vector3.UP).normalized()
	var y := z.cross(x).normalized()
	return Basis(x, y, z)


func _run(scene) -> void:
	for i in 30:
		await process_frame
	scene._start_game()
	scene.set_process(false)

	# --- Primitive snake: fixed S-curve, left half (the game's renderer).
	var path: Array[Vector2i] = [
		Vector2i(-2, -2), Vector2i(-3, -2), Vector2i(-4, -2),
		Vector2i(-4, -1), Vector2i(-4, 0), Vector2i(-3, 0),
		Vector2i(-2, 0), Vector2i(-2, 1), Vector2i(-2, 2),
	]
	scene.snake = path
	scene.direction = Vector2i.RIGHT
	scene.queued_direction = Vector2i.RIGHT
	scene._render_snake()

	# Park the apple mid-arena so it cannot overlap either snake.
	var target_cell := Vector2i(0, 6)
	var delta := Vector3(
		float(target_cell.x - scene.apple.x) * TILE, 0.0,
		float(target_cell.y - scene.apple.y) * TILE)
	scene.apple_root.position += delta
	scene.apple = target_cell

	# --- Production snake: glTF head + segments on a Curve3D spine, right.
	var head_scene: PackedScene = load("res://models/snake_head.glb")
	var seg_scene: PackedScene = load("res://models/snake_segment.glb")
	var prod := Node3D.new()
	prod.name = "ProductionSnake"
	scene.add_child(prod)

	var curve := Curve3D.new()
	for p in [Vector3(3.2, 0, -3.6), Vector3(4.5, 0, -2.7),
			Vector3(5.5, 0, -1.4), Vector3(5.9, 0, 0.0),
			Vector3(5.5, 0, 1.4), Vector3(4.5, 0, 2.7),
			Vector3(3.5, 0, 3.5)]:
		curve.add_point(p)
	var baked := curve.get_baked_points()
	# Walk the spine from the head end backwards in ~segment steps.
	var step := 1.03
	var walked := 0.0
	var seg_centers: Array[Vector3] = []
	var i := baked.size() - 1
	var prev := baked[i]
	while i > 0 and seg_centers.size() < 5:
		i -= 1
		walked += prev.distance_to(baked[i])
		prev = baked[i]
		if walked >= step:
			seg_centers.append(baked[i])
			walked = 0.0
	var head_end := baked[baked.size() - 1]
	var head_tan := (head_end - baked[baked.size() - 4]).normalized()
	prod_head_pos = head_end + Vector3(0, 0.34, 0)
	prod_head_dir = head_tan

	var head := head_scene.instantiate()
	head.position = prod_head_pos
	head.basis = _basis_along(head_tan)
	prod.add_child(head)
	var prev_c := head_end
	for c in seg_centers:
		var tan: Vector3 = prev_c - c
		tan.y = 0.0
		var seg := seg_scene.instantiate()
		seg.position = c + Vector3(0, 0.30, 0)
		seg.basis = _basis_along(tan.normalized())
		prod.add_child(seg)
		prev_c = c

	# Manual feeds for the frozen _process UI (harness convention).
	scene.score = 870
	scene._update_hud()
	scene.minimap.update_state(scene.snake, scene.apple)
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(OUT_DIR + "/side-by-side2.png")
	print("CAPTURE side-by-side done")

	# --- Beauty shot: close on the production head.
	var cam: Camera3D = scene.camera
	cam.position = prod_head_pos + Vector3(-1.6, 1.05, 2.4)
	cam.look_at(prod_head_pos + Vector3(-0.4, 0.1, 0.3), Vector3.UP)
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(OUT_DIR + "/beauty2.png")
	print("CAPTURE beauty done")
	quit()
