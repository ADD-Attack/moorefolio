## Optional runtime driver for snake_full.glb. Attach to a wrapper Node3D.
## Set model to the instanced GLB root, path to a Path3D in meters.
## Author the Curve3D from TAIL toward HEAD. +Z is the asset's model front.
## This replaces the supplied review pose; no Blender rig or animation is needed.
class_name MechanicalSnakeCurveDriver
extends Node3D
@export var model: Node3D
@export var path: Path3D
@export var head_distance_m: float = 28.0
@export var speed_mps: float = 0.8
@export var joint_pitch_m: float = 0.92
@export var loop_path: bool = false
var sections: Array[Node3D] = []
var head: Node3D
var tail: Node3D
func _ready() -> void:
 if not model: return
 head = model.get_node_or_null("Head_Joint") as Node3D
 tail = model.get_node_or_null("Tail_Joint") as Node3D
 for i in range(28):
  var section = model.get_node_or_null("Segment_%02d" % i) as Node3D
  if section: sections.append(section)
func _process(delta: float) -> void:
 if not path or not path.curve or not model: return
 head_distance_m += speed_mps * delta
 pose()
func point(distance: float) -> Vector3:
 var length = path.curve.get_baked_length()
 var d = fposmod(distance,length) if loop_path else clampf(distance,0.0,length)
 return path.to_global(path.curve.sample_baked(d,true))
func pose_node(node: Node3D, distance: float) -> void:
 if not node: return
 var p = point(distance)
 var forward = point(distance+0.02)-point(distance-0.02)
 if forward.length_squared() < 0.0000001: return
 forward = forward.normalized()
 var up = Vector3.UP
 # Explicit fallback prevents a singular frame on near-vertical neck curves.
 if absf(forward.dot(up)) > 0.985: up = Vector3.BACK
 node.global_transform = Transform3D(Basis.looking_at(forward,up,true),p)
func pose() -> void:
 pose_node(head,head_distance_m)
 for i in range(sections.size()): pose_node(sections[i],head_distance_m-i*joint_pitch_m)
 pose_node(tail,head_distance_m-sections.size()*joint_pitch_m)
