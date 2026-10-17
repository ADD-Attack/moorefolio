extends SceneTree
func _init(): call_deferred("run")
func run():
 var model = load("res://models/snake_full.glb").instantiate()
 root.add_child(model)
 var path = Path3D.new()
 path.curve = Curve3D.new()
 path.curve.add_point(Vector3(-20,2,0))
 path.curve.add_point(Vector3(20,2,0))
 root.add_child(path)
 var driver = load("res://animate_curve.gd").new()
 driver.model=model
 driver.path=path
 driver.head_distance_m=36
 root.add_child(driver)
 driver.set_process(false)
 assert(driver.sections.size()==28)
 assert(driver.head!=null and driver.tail!=null)
 driver.pose()
 for i in range(27):
  assert(absf(driver.sections[i].global_position.distance_to(driver.sections[i+1].global_position)-0.92)<0.002)
  assert(absf(driver.sections[i].global_basis.determinant()-1.0)<0.0001)
 print("CURVE_CHECK straight: 28 joint pivots at 0.92m spacing, positive orthonormal frames PASS")
 # Recover the raised review path from source node transforms, then pose it live.
 var staged=load("res://models/snake_full.glb").instantiate()
 root.add_child(staged)
 path.curve.clear_points()
 path.curve.add_point(staged.get_node("Tail_Joint").global_position)
 for i in range(27,-1,-1): path.curve.add_point(staged.get_node("Segment_%02d"%i).global_position)
 staged.queue_free()
 for frame in range(120):
  driver.head_distance_m=path.curve.get_baked_length()-0.02-frame*0.002
  driver.pose()
  for section in driver.sections:
   assert(section.global_position.is_finite())
   assert(absf(section.global_basis.determinant()-1.0)<0.0001)
 print("CURVE_CHECK raised 3D path: 120 deterministic poses, all 28 segment transforms finite and right-handed PASS")
 print("ANIMATION_RESULT PASS")
 quit()
