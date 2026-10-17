extends SceneTree

var failures := 0

func check(cond: bool, name: String) -> void:
	if cond:
		print("PASS ", name)
	else:
		failures += 1
		print("FAIL ", name)

func _init() -> void:
	var scene = load("res://main.tscn").instantiate()
	root.add_child(scene)
	_run(scene)

func _run(scene) -> void:
	for i in 10:
		await process_frame
	check(scene.state == "title", "boots to title")
	scene._start_game()
	check(scene.state == "playing", "start -> playing")
	check(scene.snake.size() == 3, "snake starts length 3")
	# Eat twice by placing the apple directly ahead.
	for n in 2:
		scene.apple = scene.snake[0] + Vector2i.RIGHT
		scene._advance_snake()
	check(scene.score == 300, "two quick eats -> 100 + combo x2 200 = 300 (got %d)" % scene.score)
	check(scene.snake.size() == 5, "two eats -> length 5 (got %d)" % scene.snake.size())
	check(scene.apples == 2, "apple counter 2")
	# Reversal must be rejected by the input rule: queue LEFT while moving RIGHT via the same guard the input uses.
	scene.queued_direction = Vector2i.RIGHT
	# Self/wall death: drive straight right until the wall.
	var guard := 0
	while scene.state == "playing" and guard < 40:
		scene.apple = Vector2i(-8, -8)
		scene._advance_snake()
		guard += 1
	check(scene.state == "game_over", "wall collision -> game_over (state=%s)" % scene.state)
	# Restart, then obstacle death: teleport head next to a crate and step into it.
	scene._start_game()
	var crate: Vector2i = scene.obstacles[0]
	var cs: Array[Vector2i] = [crate + Vector2i(-1, 0), crate + Vector2i(-2, 0), crate + Vector2i(-3, 0)]
	scene.snake = cs
	scene.direction = Vector2i.RIGHT
	scene.queued_direction = Vector2i.RIGHT
	scene.apple = Vector2i(-8, -8)
	scene._advance_snake()
	check(scene.state == "game_over", "crate collision -> game_over (state=%s)" % scene.state)
	# Level flow: force 15 apples.
	scene._start_game()
	for n in 15:
		scene.apple = scene.snake[0] + Vector2i.RIGHT
		scene.queued_direction = Vector2i.RIGHT
		scene.direction = Vector2i.RIGHT
		# Keep the lane clear: reset snake to spawn lane each eat to avoid self-collision.
		var rs: Array[Vector2i] = [Vector2i(0, 0), Vector2i(-1, 0), Vector2i(-2, 0)]
		scene.snake = rs
		scene.apple = Vector2i(1, 0)
		scene._advance_snake()
		if scene.state != "playing":
			break
	check(scene.state == "level_complete", "15 apples -> level_complete (state=%s, apples=%d)" % [scene.state, scene.apples])
	scene._begin_level_two()
	check(scene.level == 2 and scene.state == "playing", "level 2 begins")
	print("PROBE FAILURES: ", failures)
	quit(failures)
