extends Node
## Benchmark navigator — the picker lives inside the engine.
## Shows a menu of model-benchmark slots; selecting one loads its scene into
## the host node under a persistent top bar (back button + perf HUD).

const BENCHMARKS := [
	{
		"name": "Sprite Storm",
		"slot": "Model benchmark slot 01",
		"desc": "A few hundred bouncing sprites, moved and drawn live. Push the count until the frame rate bends.",
		"scene": "res://scenes/sprite_storm.tscn",
	},
	{
		"name": "Path Grid",
		"slot": "Model benchmark slot 02",
		"desc": "Forty agents A*-pathfinding around obstacles on a grid, repathing the moment they arrive.",
		"scene": "res://scenes/path_grid.tscn",
	},
	{
		"name": "Swarm — Luna · Run 1",
		"slot": "Same prompt, three models",
		"desc": "GPT-6 Luna · max effort · ~3m 20s · in 1,963 / out 911 tokens · est. $0.0007\nAs submitted: script error — enemies don't render",
		"scene": "res://swarm_luna/swarm_luna.tscn",
	},
	{
		"name": "Swarm — Sol · Run 1",
		"slot": "Same prompt, three models",
		"desc": "GPT-6.1 Sol · low effort · ~1m 43s · in 31,331 / out 2,726 tokens · est. $0.0899",
		"scene": "res://swarm_sol/swarm_sol.tscn",
	},
	{
		"name": "Swarm — Opus 5.5 · Run 1",
		"slot": "Same prompt, three models",
		"desc": "Claude Opus 5.5 · low effort · ~1m 06s · 62,727 total tokens · est. $0.25–$1.25",
		"scene": "res://swarm_opus/swarm_opus.tscn",
	},
	{
		"name": "Swarm — Luna · Run 2",
		"slot": "Same prompt, three models",
		"desc": "GPT-6 Luna · max effort · ~4m 28s · in 82,571 / out 18,229 tokens · est. $0.0174\nRunning total: ~7m 48s · in 84,534 / out 19,140 tokens · est. $0.018\nRun 2 did not fix the Run 1 mesh bug",
		"scene": "res://swarm_luna_r2/swarm_luna.tscn",
	},
	{
		"name": "Swarm — Sol · Run 2",
		"slot": "Same prompt, three models",
		"desc": "GPT-6.1 Sol · low effort · ~3m 32s · in 47,309 / out 7,438 tokens · est. $0.1690\nRunning total: ~5m 15s · in 78,640 / out 10,164 tokens · est. $0.2589",
		"scene": "res://swarm_sol_r2/swarm_sol.tscn",
	},
	{
		"name": "Swarm — Opus 5.5 · Run 2",
		"slot": "Same prompt, three models",
		"desc": "Claude Opus 5.5 · low effort · ~2m 25s · 73,193 total tokens · est. $0.29–$1.46\nRunning total: ~3m 31s · 135,920 total tokens · est. $0.54–$2.72",
		"scene": "res://swarm_opus_r2/swarm_opus.tscn",
	},
]

const BG := Color("10131a")
const PANEL := Color("1a1e28")
const INK := Color("f3ede1")
const MUTED := Color("a99e8c")
const RUST := Color("ff7a36")
const TEAL := Color("8fb8c2")

var host: Node
var menu_root: Control
var top_bar: PanelContainer
var bench_title: Label
var hud_fps: Label
var hud_ms: Label
var current: Node = null
var _ms_ema := 16.6

func _ready() -> void:
	host = Node.new()
	host.name = "BenchmarkHost"
	add_child(host)

	var layer := CanvasLayer.new()
	layer.layer = 10
	add_child(layer)

	_build_top_bar(layer)
	_build_menu(layer)

	# Headless self-test: "-- --bench-test" launches each benchmark briefly.
	if "--bench-test" in OS.get_cmdline_user_args():
		_run_self_test()
	# Screenshot pass (Xvfb): "-- --shot-test" saves menu + both benchmarks.
	if "--shot-test" in OS.get_cmdline_user_args():
		_run_shot_test()

func _process(delta: float) -> void:
	if delta > 0.0:
		_ms_ema = lerpf(_ms_ema, delta * 1000.0, 0.05)
	if top_bar.visible:
		hud_fps.text = "%d FPS" % Engine.get_frames_per_second()
		hud_ms.text = "%.1f ms" % _ms_ema

# ---------------------------------------------------------------- menu

func _build_menu(layer: CanvasLayer) -> void:
	menu_root = Control.new()
	menu_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	layer.add_child(menu_root)

	var bg := ColorRect.new()
	bg.color = BG
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	menu_root.add_child(bg)

	var margin := MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	margin.add_theme_constant_override("margin_left", 64)
	margin.add_theme_constant_override("margin_right", 64)
	margin.add_theme_constant_override("margin_top", 48)
	margin.add_theme_constant_override("margin_bottom", 40)
	menu_root.add_child(margin)

	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 14)
	margin.add_child(vbox)

	var kicker := _label("MOOREFOLIO — MODEL BENCHMARKS", 15, RUST)
	vbox.add_child(kicker)

	var title := _label("Benchmarks", 56, INK)
	vbox.add_child(title)

	var sub := _label(
		"Small playable Godot scenes — one per model build. Pick one; it runs right here, inside the engine.",
		19, MUTED)
	sub.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	sub.custom_minimum_size = Vector2(0, 30)
	vbox.add_child(sub)

	var spacer := Control.new()
	spacer.custom_minimum_size = Vector2(0, 10)
	vbox.add_child(spacer)

	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	vbox.add_child(scroll)

	var cards := VBoxContainer.new()
	cards.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	cards.add_theme_constant_override("separation", 14)
	scroll.add_child(cards)

	for i in BENCHMARKS.size():
		cards.add_child(_make_card(i))

	var foot := _label(
		"Built with Godot 4.7 · The picker, the HUD and the benchmarks are all one embedded app.",
		14, MUTED)
	vbox.add_child(foot)

func _make_card(index: int) -> PanelContainer:
	var data: Dictionary = BENCHMARKS[index]
	var card := PanelContainer.new()
	var style := StyleBoxFlat.new()
	style.bg_color = PANEL
	style.corner_radius_top_left = 14
	style.corner_radius_top_right = 14
	style.corner_radius_bottom_left = 14
	style.corner_radius_bottom_right = 14
	style.content_margin_left = 22
	style.content_margin_right = 22
	style.content_margin_top = 16
	style.content_margin_bottom = 16
	card.add_theme_stylebox_override("panel", style)

	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 18)
	card.add_child(row)

	var texts := VBoxContainer.new()
	texts.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	texts.add_theme_constant_override("separation", 2)
	row.add_child(texts)

	var slot := _label(str(data["slot"]).to_upper(), 12, TEAL)
	texts.add_child(slot)
	var name_label := _label(str(data["name"]), 27, INK)
	texts.add_child(name_label)
	var desc := _label(str(data["desc"]), 15, MUTED)
	desc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	texts.add_child(desc)

	var launch := Button.new()
	launch.text = "Launch ›"
	launch.custom_minimum_size = Vector2(120, 46)
	launch.add_theme_font_size_override("font_size", 16)
	launch.pressed.connect(_launch.bind(index))
	row.add_child(launch)
	return card

# ---------------------------------------------------------------- top bar / HUD

func _build_top_bar(layer: CanvasLayer) -> void:
	top_bar = PanelContainer.new()
	top_bar.set_anchors_preset(Control.PRESET_TOP_WIDE)
	var style := StyleBoxFlat.new()
	style.bg_color = Color("161a23")
	style.content_margin_left = 14
	style.content_margin_right = 14
	style.content_margin_top = 8
	style.content_margin_bottom = 8
	top_bar.add_theme_stylebox_override("panel", style)
	layer.add_child(top_bar)

	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 16)
	top_bar.add_child(row)

	var back := Button.new()
	back.text = "‹ Benchmarks"
	back.add_theme_font_size_override("font_size", 16)
	back.pressed.connect(_go_home)
	row.add_child(back)

	bench_title = _label("", 18, INK)
	row.add_child(bench_title)

	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(spacer)

	hud_fps = _label("— FPS", 16, TEAL)
	row.add_child(hud_fps)
	hud_ms = _label("— ms", 16, TEAL)
	row.add_child(hud_ms)

	top_bar.visible = false

# ---------------------------------------------------------------- navigation

func _launch(index: int) -> void:
	_go_home()
	var data: Dictionary = BENCHMARKS[index]
	var packed: PackedScene = load(str(data["scene"]))
	current = packed.instantiate()
	host.add_child(current)
	bench_title.text = "Model benchmark — %s" % str(data["name"])
	menu_root.visible = false
	top_bar.visible = true

func _go_home() -> void:
	if current != null:
		current.queue_free()
		current = null
	top_bar.visible = false
	menu_root.visible = true

func _label(text: String, size: int, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	return l

# ---------------------------------------------------------------- self test

func _run_self_test() -> void:
	await get_tree().create_timer(0.5).timeout
	for i in BENCHMARKS.size():
		_launch(i)
		await get_tree().create_timer(2.5).timeout
		print("SELFTEST ok: ", BENCHMARKS[i]["name"], " fps=", Engine.get_frames_per_second())
		_go_home()
	print("SELFTEST DONE")
	get_tree().quit()

func _snap(name: String) -> void:
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	DirAccess.make_dir_recursive_absolute("/tmp/shots")
	img.save_png("/tmp/shots/%s.png" % name)

func _run_shot_test() -> void:
	await get_tree().create_timer(1.2).timeout
	await _snap("menu")
	_launch(0)
	await get_tree().create_timer(2.0).timeout
	await _snap("sprite_storm")
	_go_home()
	_launch(1)
	await get_tree().create_timer(2.0).timeout
	await _snap("path_grid")
	print("SHOTS DONE")
	get_tree().quit()
