# Goblin bake-off — opus

Everything in `render.png` is built by `build.py`, headless:

```
blender -b --factory-startup --python build.py -- <abs\path\render.png>
```

(Add `preview` for a fast 30% / 32-sample check. Add `head` for a 200 mm face close-up.)

## Geometry
- **Anatomy from metaballs, then converted to a mesh.** The body is one metaball family of about 150
  elements (balls, ellipsoids, capsules), sized from a measured calibration: visible radius = 0.575 ×
  influence radius. It covers a hunched rib cage, pot belly, wiry arms, bony knees, and long splayed
  three-toed feet. The head has a large cranium, a heavy angry brow, a hooked nose with nostrils, cheekbones,
  an underbite jaw and warts. Negative elements carve the eye sockets, nostrils, navel and the sneering
  mouth slit. Each ear is a chain of 22 flattened, rotated ellipsoids with negative ellipsoids for the
  inner concavity. The family is evaluated through the depsgraph, converted with `new_from_object`,
  smooth-shaded and given a light Smooth modifier.
- **Hands are a second, finer metaball family.** A procedural finger rig places each knuckle chain from
  per-joint curl angles in a wrist frame. The right hand is a fist closed around the dagger grip. The left
  hand is an open, hooked claw. Leather wraps hide the seams at the wrists.
- **Props are bmesh, fitted to the body.** Curved claws, tusks, teeth and the fang necklace are swept
  tubes along Bézier paths. The ragged burlap kilt and the belt are lofted from the converted body's own
  cross-sections, so they sit right on the skin. Their radius per angle comes from numpy slices of the
  body verts, with fold waves and a noisy hem added. Other props: wrist and ankle wraps (sized to the limb),
  a riveted pauldron and chest strap, a pouch, and a curved dagger (diamond-section blade, guard, wrapped
  grip, pommel).
- **Scene size:** about 122k faces.

## Materials (all procedural, Cycles nodes)
- **Skin:** Principled BSDF with random-walk (skin) subsurface (weight 0.1, red-heavy radius). The olive
  base is a noise ramp with Voronoi mottling. Pointiness adds a warm tint on edges, and an AO node darkens
  cavities. Roughness is broken up with noise. Three chained bump layers give pores, cellular skin and
  wrinkles. A thin coat adds sheen.
- **Eyes:** an amber iris with a dark limbal ring and a vertical slit pupil, computed from object-space
  coordinates. A faint iris emission and a full clear coat give a wet look.
- **Other surfaces:**
  - Bone/teeth and keratin claws: subsurface with bump.
  - Leather and leather wraps: wave-texture wrap pattern.
  - Burlap: a cross-weave from two band waves, plus sheen and hem grime.
  - Iron, and rust-flecked blade steel: metallic with noise roughness.

## Lighting & camera
- **Three-point studio lighting** with rectangular area lights:
  - Key: warm, 720 W, 1.4 m, front-left-high.
  - Fill: cool, 160 W, 2.2 m, front-right-low.
  - Rim: 650 W, 0.6 × 1.6 m strip, back-right.
- **Background:** a seamless neutral-gray cyclorama (albedo 0.07), plus a dim gray world (0.6) for ambient.
- **Camera:** 66 mm lens, 14° three-quarter yaw, slightly above waist height. f/11 depth of field
  focused on the face.

## Render settings
- **Engine:** Cycles on the GPU (OptiX, RTX 3070 Ti), 1920×1080.
- **Samples:** 1024 max, adaptive (threshold 0.0025, minimum 256), OpenImageDenoise.
- **Bounces:** 12 max (diffuse 4, glossy 6). Caustics off.
- **Color:** AgX view, Medium High Contrast look, exposure −0.35.
- **Output:** 8-bit PNG with dither.
- **Render time:** about 36 s.
