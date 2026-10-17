# Goblin build note (haiku)

Scene is generated entirely by `build.py` (Blender 4.5.14 LTS, headless). No imported assets.

Run: `blender -b --factory-startup -P build.py -- [render.png] [samples]` (defaults: `render.png` next to the script, 256 samples).

## Geometry

- **Body:** Skin-modifier graphs (per-vertex radii) with Subdivision Surface (2 levels), evaluated into a plain mesh and smooth-shaded. Torso, arms, legs, and fingers are all skin graphs.
- **Head:** icosphere (subdiv 5) displaced by sum-of-Gaussian bumps for nose, brow, eye sockets, cheekbones, chin, and cranium, with a jaw taper below the cheeks.
- **Ears:** skinned chains, pointed outward and up.
- **Boots:** skinned chains (ankle to toe).
- **Loincloth:** subdivided grid, Solidify (0.006) plus Subdivision.
- **Belt:** torus with a cube pouch.
- **Dagger:** tube grip, cube guard, tapered blade.
- **Eyes, teeth, claws:** primitive ellipsoids and cones.
- **Backdrop:** cyc built from a profile curve (floor sweeping into a wall), smooth-shaded to avoid faceting bands.

## Materials

All Principled BSDF, procedural (no image textures).

- **Skin:** dark olive base with noise-driven color variation (ColorRamp into Base Color) and a noise bump for mottling. Subsurface 0.15.
- **Leather / cloth:** roughness-heavy Principled with noise bump.
- **Blade:** dark iron, metallic 1.0, roughness 0.35. A steel-gray blade reflected the backdrop and vanished, so it was darkened.
- **Eyes, teeth, claws:** simple Principled surfaces (eye whites coated).

## Lighting

Three-point area lights aimed at a point near chest height (0, 0, 0.7):

- **Key:** upper left front, 650 W, size 1.6.
- **Fill:** right front, 130 W, size 2.2.
- **Rim:** above and behind right, 420 W, size 0.8, aimed at the head/shoulder line.

The rim light was placed high and behind on purpose. A lower rim produced a diagonal bright/dark wedge across the upper backdrop. Fill and rim were A/B tested with throwaway copies to isolate it.

## Render settings

- Engine: Cycles, GPU via OPTIX (CUDA fallback, CPU if neither is available). Hardware: RTX 3070 Ti.
- Samples: 256, adaptive sampling with threshold 0.01.
- Denoiser: OpenImageDenoise.
- Max bounces: 12.
- Resolution: 1920x1080 at 100%. Output: PNG, RGB, 8-bit.
- View transform: AgX, look None, exposure 0.
- Film: opaque. World: flat gray, strength 0.6.
- Camera: 50 mm lens, 36 mm sensor width, straight-on, at (0, -4.15, 0.67). The full figure fits and is centered.
- Render time at 256 samples: about 22 s.

## Limitations

- Stylized and procedural. The figure is a static, symmetric standing pose.
- No hair or cloth simulation.
- Head is a smooth, egg-like form; facial features read at a distance but are simple.
- Fingers are simplified.
- Legs are mannequin-like tubes.
- Skin mottling and the key-to-wall falloff are acceptable but not refined.
