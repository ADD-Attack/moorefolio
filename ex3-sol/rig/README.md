# TRIPLE AAA SNAKE
# TRIPLE AAA SNAKE

A self-contained Godot 4.7 3D grid snake game.

- Run `project.godot` to boot directly into the title screen.
- Arrow keys or WASD steer. The snake cannot reverse into itself.
- Esc or P pauses. Enter or click starts/restarts.
- Collect 15 apples to complete level 1 and continue into the faster level 2.
- High score is stored in `user://highscore.cfg`.

The arena, snake, crates, apple, lighting, and HUD are built procedurally in `main.gd`.

## Exercise 3 lighting study

- `lighting/staging.tscn`: isolated neutral-gray review stage.
- `lighting/ingame_study.tscn`: fixed evidence arrangement at the shipping camera, with the same rig's arena variant. Not a replacement game mode.
- `lighting/mood_rig.gd`: shared key, fill, rim, environment and collar spill.
- `lighting/studio_reflections.gdshader`: off-camera reflection softboxes; never applied to the snake.

Run an editor import before rendering. From the exercise root:

```sh
godot --headless --editor --path game-demo --import --quit
DISPLAY=:0 godot --path game-demo --audio-driver Dummy --resolution 1920x1080 --script res://lighting/capture_study.gd
```

The capture script writes four raw viewport PNGs and light inventories to `../deliverables/`. It manually refreshes the HUD and minimap after freezing the evidence scene. See `../deliverables/BUILD-NOTE.md` for the complete setup.
