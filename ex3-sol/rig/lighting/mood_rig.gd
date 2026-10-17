extends Node3D
## Shared lighting study: the arena is a lower-energy adaptation of this rig.
@export var in_game := false
var environment: Environment

func _ready() -> void:
	name = "InGameMoodRig" if in_game else "StagingMoodRig"
	var world := WorldEnvironment.new()
	world.name = "StudioEnvironment"
	environment = Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color("#65676b") if not in_game else Color("#101a23")
	var sky := Sky.new()
	var sky_material := ShaderMaterial.new()
	sky_material.shader = preload("res://lighting/studio_reflections.gdshader")
	sky.sky_material = sky_material
	sky.radiance_size = Sky.RADIANCE_SIZE_512
	sky.process_mode = Sky.PROCESS_MODE_QUALITY
	environment.sky = sky
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	environment.ambient_light_energy = 0.50 if not in_game else 0.38
	environment.ambient_light_sky_contribution = 1.0
	environment.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	environment.background_energy_multiplier = 0.75 if not in_game else 0.60
	environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	environment.tonemap_exposure = 1.0
	environment.tonemap_white = 4.0
	environment.glow_enabled = true
	environment.glow_normalized = true
	environment.glow_intensity = 0.16 if not in_game else 0.22
	environment.glow_strength = 0.75
	environment.glow_bloom = 0.0
	environment.glow_hdr_threshold = 0.8
	environment.glow_hdr_scale = 1.0
	environment.glow_blend_mode = Environment.GLOW_BLEND_MODE_ADDITIVE
	environment.set_glow_level(0, 0.0)
	environment.set_glow_level(1, 0.5)
	environment.set_glow_level(2, 0.35)
	environment.set_glow_level(3, 0.15)
	for i in range(4,7): environment.set_glow_level(i, 0.0)
	environment.ssao_enabled = true
	environment.ssao_radius = 0.22
	environment.ssao_intensity = 0.6
	environment.ssao_power = 1.25
	environment.ssao_light_affect = 0.0
	environment.fog_enabled = false
	world.environment = environment
	add_child(world)
	_directional("Key_SoftWarm", Vector3(-48,-32,0), Color("#fff1df"), 1.6 if not in_game else 1.25, true, 8.0)
	_directional("Fill_Cool", Vector3(-24,58,0), Color("#d3e3f4"), 0.38 if not in_game else 0.32, false, 0.0)
	_directional("Rim_Silver", Vector3(-32,155,0), Color("#d9efff"), 1.8 if not in_game else 1.45, true, 5.0)

func _directional(label: String, angles: Vector3, color: Color, energy: float, shadows: bool, angular: float) -> void:
	var light := DirectionalLight3D.new()
	light.name = label
	light.position = Vector3(0,8,0)
	light.rotation_degrees = angles
	light.light_color = color
	light.light_energy = energy
	light.light_angular_distance = angular
	light.shadow_enabled = shadows
	light.shadow_bias = 0.03
	light.shadow_normal_bias = 0.5
	light.directional_shadow_max_distance = 55.0
	light.directional_shadow_blend_splits = true
	add_child(light)

## Emission is not GI. Two tiny practical lights per collar give nearby
## housing/floor a soft mint bounce, without changing the glTF materials.
func add_collar_spill(model: Node3D) -> void:
	for node in model.get_children():
		if node is Node3D and (String(node.name).begins_with("SnakeSegRing") or String(node.name) == "SnakeHeadRing") and not "Housing" in String(node.name):
			for side in [-1.0,1.0]:
				var light := OmniLight3D.new()
				light.name = "CollarBounce_%s_%s" % [node.name, str(side)]
				model.add_child(light)
				light.position = node.position + Vector3(0, 0.05, 0.47 * side)
				light.light_color = Color("#7affbf")
				light.light_energy = 0.035 if not in_game else 0.045
				light.omni_range = 0.75
				light.omni_attenuation = 1.5
				light.light_size = 0.16
				light.light_specular = 0.25
				light.shadow_enabled = false
