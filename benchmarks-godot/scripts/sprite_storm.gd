extends Node2D
## Benchmark 1 — Sprite Storm.
## A few hundred sprites bounce around the play field, every one moved in
## GDScript each frame and drawn as its own Sprite2D node. Live readouts for
## entity count / FPS / frame time, with − / + buttons to change the load.

const TOP_INSET := 56.0 ## leave room for the navigator top bar
const MIN_COUNT := 0
const MAX_COUNT := 2000
const STEP := 100

var _tex: Texture2D
var _sprites: Array[Sprite2D] = []
var _vels: Array[Vector2] = []
var _count := 300
var _rng := RandomNumberGenerator.new()
var _stat_label: Label
var _count_label: Label
var _stat_timer := 0.0

func _ready() -> void:
	_rng.randomize()
	_tex = _make_dot_texture()
	_build_ui()
	_set_count(_count)

func _make_dot_texture() -> Texture2D:
	var size := 40
	var img := Image.create(size, size, false, Image.FORMAT_RGBA8)
	var center := Vector2(size, size) * 0.5
	var radius := size * 0.46
	for y in size:
		for x in size:
			var d := Vector2(x, y).distance_to(center)
			var a := clampf((radius - d) / 3.0, 0.0, 1.0)
			img.set_pixel(x, y, Color(1, 1, 1, a))
	return ImageTexture.create_from_image(img)

func _field() -> Rect2:
	var vp := get_viewport_rect().size
	return Rect2(0, TOP_INSET, vp.x, vp.y - TOP_INSET)

func _spawn_one() -> void:
	var field := _field()
	var s := Sprite2D.new()
	s.texture = _tex
	s.position = Vector2(
		_rng.randf_range(field.position.x + 20.0, field.end.x - 20.0),
		_rng.randf_range(field.position.y + 20.0, field.end.y - 20.0))
	var speed := _rng.randf_range(60.0, 280.0)
	var angle := _rng.randf_range(0.0, TAU)
	_vels.append(Vector2.RIGHT.rotated(angle) * speed)
	s.modulate = Color.from_hsv(_rng.randf(), 0.65, 1.0)
	var sc := _rng.randf_range(0.5, 1.15)
	s.scale = Vector2(sc, sc)
	add_child(s)
	_sprites.append(s)

func _set_count(n: int) -> void:
	_count = clampi(n, MIN_COUNT, MAX_COUNT)
	while _sprites.size() < _count:
		_spawn_one()
	while _sprites.size() > _count:
		var s: Sprite2D = _sprites.pop_back()
		_vels.pop_back()
		s.queue_free()
	if _count_label:
		_count_label.text = "%d sprites" % _count

func _process(delta: float) -> void:
	var field := _field()
	for i in _sprites.size():
		var s := _sprites[i]
		var v := _vels[i]
		var p := s.position + v * delta
		if p.x < field.position.x + 12.0 or p.x > field.end.x - 12.0:
			v.x = -v.x
			p.x = clampf(p.x, field.position.x + 12.0, field.end.x - 12.0)
		if p.y < field.position.y + 12.0 or p.y > field.end.y - 12.0:
			v.y = -v.y
			p.y = clampf(p.y, field.position.y + 12.0, field.end.y - 12.0)
		s.position = p
		_vels[i] = v
	_stat_timer += delta
	if _stat_timer >= 0.25 and _stat_label:
		_stat_timer = 0.0
		_stat_label.text = "Entities: %d   ·   %d FPS   ·   %.2f ms/frame" % [
			_sprites.size(), Engine.get_frames_per_second(),
			1000.0 / maxf(Engine.get_frames_per_second(), 1.0)]

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
	title.text = "SPRITE STORM"
	title.add_theme_font_size_override("font_size", 14)
	title.add_theme_color_override("font_color", Color("ff7a36"))
	vbox.add_child(title)

	_stat_label = Label.new()
	_stat_label.add_theme_font_size_override("font_size", 17)
	_stat_label.add_theme_color_override("font_color", Color("f3ede1"))
	vbox.add_child(_stat_label)

	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	vbox.add_child(row)

	var minus := Button.new()
	minus.text = "− 100"
	minus.pressed.connect(func() -> void: _set_count(_count - STEP))
	row.add_child(minus)

	_count_label = Label.new()
	_count_label.add_theme_font_size_override("font_size", 17)
	_count_label.add_theme_color_override("font_color", Color("8fb8c2"))
	row.add_child(_count_label)

	var plus := Button.new()
	plus.text = "+ 100"
	plus.pressed.connect(func() -> void: _set_count(_count + STEP))
	row.add_child(plus)
