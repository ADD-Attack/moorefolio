extends Node2D
## Benchmark 2 — Path Grid.
## ~40 agents continuously A*-pathfind to random targets on an obstacle
## grid, repathing the moment they arrive. Readout: paths computed/sec, FPS.

const COLS := 53
const ROWS := 27
const CELL := 24.0
const OBSTACLE_FRACTION := 0.12

var _astar := AStarGrid2D.new()
var _origin := Vector2.ZERO
var _agents: Array[Dictionary] = []
var _agent_count := 40
var _rng := RandomNumberGenerator.new()
var _paths_window := 0
var _paths_per_sec := 0
var _window_timer := 0.0
var _stat_label: Label
var _agent_label: Label

const AGENT_COLORS := [
	Color("ff7a36"), Color("8fb8c2"), Color("e0a83e"), Color("f3ede1"),
	Color("7ac74f"), Color("c678dd"), Color("56b6f1"), Color("ef596f"),
]

func _ready() -> void:
	_rng.randomize()
	_origin = Vector2(
		(get_viewport_rect().size.x - COLS * CELL) * 0.5,
		maxf(60.0, (get_viewport_rect().size.y - ROWS * CELL) * 0.5 + 14.0))

	_astar.region = Rect2i(0, 0, COLS, ROWS)
	_astar.cell_size = Vector2(CELL, CELL)
	_astar.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES
	_astar.update()
	for x in COLS:
		for y in ROWS:
			if _rng.randf() < OBSTACLE_FRACTION:
				_astar.set_point_solid(Vector2i(x, y), true)

	_build_ui()
	_set_agent_count(_agent_count)

func _cell_center(cell: Vector2i) -> Vector2:
	return _origin + (Vector2(cell) + Vector2(0.5, 0.5)) * CELL

func _random_free_cell() -> Vector2i:
	for attempt in 200:
		var c := Vector2i(_rng.randi_range(0, COLS - 1), _rng.randi_range(0, ROWS - 1))
		if not _astar.is_point_solid(c):
			return c
	return Vector2i(1, 1)

func _give_new_path(agent: Dictionary) -> void:
	var from_cell := Vector2i((agent["pos"] - _origin) / CELL)
	var target := _random_free_cell()
	var id_path := _astar.get_id_path(from_cell, target)
	var points: Array[Vector2] = []
	for cell in id_path:
		points.append(_cell_center(cell))
	agent["path"] = points
	agent["step"] = 0
	_paths_window += 1

func _make_agent() -> Dictionary:
	var cell := _random_free_cell()
	var a := {
		"pos": _cell_center(cell),
		"path": [] as Array[Vector2],
		"step": 0,
		"speed": _rng.randf_range(90.0, 170.0),
		"color": AGENT_COLORS[_rng.randi_range(0, AGENT_COLORS.size() - 1)],
	}
	_give_new_path(a)
	return a

func _set_agent_count(n: int) -> void:
	_agent_count = clampi(n, 1, 200)
	while _agents.size() < _agent_count:
		_agents.append(_make_agent())
	while _agents.size() > _agent_count:
		_agents.pop_back()
	if _agent_label:
		_agent_label.text = "%d agents" % _agents.size()

func _process(delta: float) -> void:
	for a in _agents:
		var path: Array = a["path"]
		var step: int = a["step"]
		if step >= path.size():
			_give_new_path(a)
			continue
		var target: Vector2 = path[step]
		var to := target - (a["pos"] as Vector2)
		var dist := to.length()
		var move := (a["speed"] as float) * delta
		if dist <= move:
			a["pos"] = target
			a["step"] = step + 1
		else:
			a["pos"] = (a["pos"] as Vector2) + to / dist * move
	_window_timer += delta
	if _window_timer >= 1.0:
		_paths_per_sec = _paths_window
		_paths_window = 0
		_window_timer = 0.0
		if _stat_label:
			_stat_label.text = "Paths computed: %d / sec   ·   %d FPS   ·   grid %d×%d" % [
				_paths_per_sec, Engine.get_frames_per_second(), COLS, ROWS]
	queue_redraw()

func _draw() -> void:
	var grid_size := Vector2(COLS, ROWS) * CELL
	draw_rect(Rect2(_origin, grid_size), Color("141824"), true)
	# Obstacles.
	for x in COLS:
		for y in ROWS:
			if _astar.is_point_solid(Vector2i(x, y)):
				draw_rect(Rect2(_origin + Vector2(x, y) * CELL + Vector2(1, 1),
					Vector2(CELL - 2, CELL - 2)), Color("2c3247"), true)
	# Grid lines.
	var line_col := Color(1, 1, 1, 0.05)
	for x in COLS + 1:
		draw_line(_origin + Vector2(x * CELL, 0), _origin + Vector2(x * CELL, grid_size.y), line_col, 1.0)
	for y in ROWS + 1:
		draw_line(_origin + Vector2(0, y * CELL), _origin + Vector2(grid_size.x, y * CELL), line_col, 1.0)
	# A few agents get their route drawn, faintly.
	for i in mini(_agents.size(), 6):
		var a := _agents[i]
		var path: Array = a["path"]
		var step: int = a["step"]
		if step < path.size():
			var pts := PackedVector2Array()
			pts.append(a["pos"])
			for j in range(step, path.size()):
				pts.append(path[j])
			if pts.size() > 1:
				draw_polyline(pts, Color(a["color"], 0.35), 1.5)
	# Agents.
	for a in _agents:
		draw_circle(a["pos"], 6.0, a["color"])
		draw_circle(a["pos"], 2.4, Color(0, 0, 0, 0.55))

func _build_ui() -> void:
	var layer := CanvasLayer.new()
	layer.layer = 1
	add_child(layer)

	var panel := PanelContainer.new()
	panel.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	panel.position = Vector2(16, -16)
	panel.grow_vertical = Control.GROW_DIRECTION_BEGIN
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.09, 0.11, 0.16, 0.88)
	style.corner_radius_top_left = 12
	style.corner_radius_top_right = 12
	style.corner_radius_bottom_left = 12
	style.corner_radius_bottom_right = 12
	style.content_margin_left = 16
	style.content_margin_right = 16
	style.content_margin_top = 12
	style.content_margin_bottom = 12
	panel.add_theme_stylebox_override("panel", style)
	layer.add_child(panel)

	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 8)
	panel.add_child(vbox)

	var title := Label.new()
	title.text = "PATH GRID — A*"
	title.add_theme_font_size_override("font_size", 14)
	title.add_theme_color_override("font_color", Color("ff7a36"))
	vbox.add_child(title)

	_stat_label = Label.new()
	_stat_label.text = "Paths computed: — / sec"
	_stat_label.add_theme_font_size_override("font_size", 17)
	_stat_label.add_theme_color_override("font_color", Color("f3ede1"))
	vbox.add_child(_stat_label)

	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	vbox.add_child(row)

	var minus := Button.new()
	minus.text = "− 10"
	minus.pressed.connect(func() -> void: _set_agent_count(_agents.size() - 10))
	row.add_child(minus)

	_agent_label = Label.new()
	_agent_label.add_theme_font_size_override("font_size", 17)
	_agent_label.add_theme_color_override("font_color", Color("8fb8c2"))
	row.add_child(_agent_label)

	var plus := Button.new()
	plus.text = "+ 10"
	plus.pressed.connect(func() -> void: _set_agent_count(_agents.size() + 10))
	row.add_child(plus)
