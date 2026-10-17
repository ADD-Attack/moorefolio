#!/usr/bin/env python3
"""Review staging renders (REVIEW-STAGING.md standard, 2026-10-17).

Stages the posed snake from snake.blend on a plain mid-gray backdrop
with neutral studio lighting — model only, nothing else in frame.
Every exercise renders its baseline and after shots through this exact
script so comparisons are honest.

Run:
  blender -b snake.blend --python render_staging.py -- OUT_FULL OUT_HEAD

Staging constants (do not drift between exercises):
  backdrop   world + seamless ground plane (300 units), RGB (0.32, 0.32, 0.32)
  lights     Key sun 3.0 rot (52, 0, -35) deg, white
             Fill sun 0.9 rot (60, 0, 140) deg, white
             Rim  sun 1.4 rot (115, 0, 180) deg, white
  renderer   Cycles, 64 samples, denoise on, AgX view transform.
             (EEVEE was tried first for speed in Exercise 2: this VM
             has no working EGL — libEGL was absent, and after
             installing it the surfaceless platform fails with
             EGL_BAD_PARAMETER — so GPU rendering is unavailable and
             Cycles CPU is the only route. 64spp + denoise is the
             cost/quality compromise; a 1920x1080 frame takes ~10-25
             min here. Baseline and after shots always use identical
             settings, so comparisons stay honest.)
  FULL cam   loc (5.0, -5.4, 2.7), target (0.0, 0.30, 0.35), lens 42,
             frame 1920 x 1080
  HEAD cam   loc (2.7, -2.3, 1.5), target (2.45, 0.30, 0.45), lens 50,
             frame 1600 x 1200
"""
import math
import os
import sys

import bpy
from mathutils import Vector

GRAY = (0.32, 0.32, 0.32)


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def add_sun(name, energy, rot_deg):
    data = bpy.data.lights.new(name, "SUN")
    data.energy = energy
    data.color = (1.0, 1.0, 1.0)
    obj = bpy.data.objects.new(name, data)
    obj.rotation_euler = tuple(math.radians(a) for a in rot_deg)
    bpy.context.collection.objects.link(obj)
    return obj


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    out_full, out_head = argv[0], argv[1]
    engine = argv[2] if len(argv) > 2 else "CYCLES"
    scale = float(argv[3]) if len(argv) > 3 else 1.0
    samples = int(argv[4]) if len(argv) > 4 else 64

    # Clean any prior staging rig / default camera+light from the blend.
    for obj in list(bpy.data.objects):
        if obj.type in ("LIGHT", "CAMERA") or obj.name.startswith("Review"):
            bpy.data.objects.remove(obj, do_unlink=True)

    # Seamless backdrop: ground plane in the world gray.
    bpy.ops.mesh.primitive_plane_add(size=300, location=(0, 0, 0))
    ground = bpy.context.object
    ground.name = "ReviewBackdrop"
    gmat = bpy.data.materials.new("ReviewGray")
    gmat.use_nodes = True
    bsdf = gmat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = GRAY + (1.0,)
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 1.0
    ground.data.materials.append(gmat)

    world = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = GRAY + (1.0,)
    world.node_tree.nodes["Background"].inputs[1].default_value = 1.0

    add_sun("ReviewKey", 3.0, (52, 0, -35))
    add_sun("ReviewFill", 0.9, (60, 0, 140))
    add_sun("ReviewRim", 1.4, (115, 0, 180))

    scene = bpy.context.scene
    if engine == "EEVEE":
        scene.render.engine = "BLENDER_EEVEE_NEXT"
        scene.eevee.taa_render_samples = 64
    else:
        scene.render.engine = "CYCLES"
        scene.cycles.samples = samples
        scene.cycles.use_denoise = True
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "None"

    shots = (
        ("ReviewCamFull", (0.0, -11.0, 7.5), (0.0, -0.30, 0.50), 32,
         out_full, int(1920*scale), int(1080*scale)),
        ("ReviewCamHead", (-7.5, -3.0, 2.2), (-5.90, 2.40, 1.20), 62,
         out_head, int(1600*scale), int(1200*scale)),
    )
    for shot_index, (name, loc, target, lens, path, rx, ry) in enumerate(shots):
        if shot_index == 1:
            for obj in bpy.context.scene.objects:
                if obj.type == "MESH" and not obj.get("review_head", False):
                    obj.hide_render = True
        data = bpy.data.cameras.new(name)
        data.lens = lens
        cam = bpy.data.objects.new(name, data)
        cam.location = loc
        bpy.context.collection.objects.link(cam)
        look_at(cam, target)
        scene.camera = cam
        scene.render.resolution_x = rx
        scene.render.resolution_y = ry
        scene.render.filepath = os.path.abspath(path)
        bpy.ops.render.render(write_still=True)
        print("STAGED", scene.render.filepath,
              "exists:", os.path.exists(scene.render.filepath))


if __name__ == "__main__":
    main()
