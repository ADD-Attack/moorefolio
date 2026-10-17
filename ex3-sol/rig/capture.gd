extends SceneTree

func _init() -> void:
	var scene = load("res://main.tscn").instantiate()
	root.add_child(scene)
	_run(scene)

func _run(scene) -> void:
	for i in 30:
		await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("/home/hatch/workspace/snake-aaa/shots/w4-title.png")
	scene._start_game()
	scene.set_process(false)
	# Deterministic mid-game composition: S-curve of eats, snake grows to ~19.
	var legs := [[Vector2i.RIGHT, 3], [Vector2i.DOWN, 2], [Vector2i.LEFT, 4], [Vector2i.DOWN, 1], [Vector2i.RIGHT, 2]]
	for leg in legs:
		scene.queued_direction = leg[0]
		for n in leg[1]:
			scene.apple = scene.snake[0] + leg[0]
			scene._advance_snake()
			for i in 4:
				await process_frame
	scene.score = 870
	scene.combo = 3
	scene._update_hud()
	scene.minimap.update_state(scene.snake, scene.apple)
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("/home/hatch/workspace/snake-aaa/shots/w4-play.png")
	print("CAPTURE DONE score=", scene.score, " len=", scene.snake.size(), " state=", scene.state)
	quit()
