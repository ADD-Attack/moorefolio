# Reference-Match Build — Mechanical Snake (Sol run, 2026-10-17)

You are the builder for this job. This brief is the complete instruction
set. Work only from this brief and the files in the input package. Do not
contact the producer during the run; if something in the package is
missing or corrupt, say exactly what in NOTE.md and do the best complete
job possible with what is present.

## Input package

Download `refmatch-input.zip` from branch `refmatch-sol-input-20261017`
of `ADD-Attack/moorefolio`, folder `benchmarks/refmatch/sol-input/`
(clone the branch or fetch the raw file). Verify before anything else:

    sha256sum refmatch-input.zip
    = 61625934b41126627cd6e1422bf1f491ac19ed250adc785f6e65d59f7ba82e49

If the SHA does not match, STOP and say so in NOTE.md. After unzipping,
also run `sha256sum -c MANIFEST.sha256` inside `refmatch-input/` — every
line must say OK.

The package contains: `REFERENCE.png` (the target), `DOSSIER.md` (the
method source — its export contract, topology, texturing, and rigging
standards govern this build wherever it speaks), `REVIEW-STAGING.md`
(governs the review captures), `assets/` (the Exercise-2 model: GLBs +
textures — your starting base), `base/` (the Exercise-2 build scripts),
and `game-demo/` (the Godot project for the import check). The BRIEF.md
inside the package states the same mission; where it names a delivery
branch or folder, THIS brief's delivery section supersedes it.

## Mission

Rebuild the mechanical snake so it matches `REFERENCE.png` as closely as
possible. Reuse what serves the match from the Exercise-2 base; rebuild
whatever falls short.

## The target (REFERENCE.png)

Study the reference image before building and re-check it as you work:

- A long segmented serpent of overlapping gunmetal armor plates, worn
  and scratched, with real edge wear, seam grime, rivets and fasteners,
  panel lines, and vent grilles on the segments.
- A glowing teal-mint ring recessed into every joint between segments,
  sitting in a dark housing — a light band, not a painted stripe.
- The head is an armored, slightly elongated serpent head carrying ONE
  large circular eye. Crest fins rise from the top of the head, mounted
  in sockets.
- The body tapers toward a finned tail tip.
- In the reference the snake is posed in a raised S-curve with the head
  up. Your staging pose echoes that presentation.

### Owner design notes (requirements, not suggestions)

1. **The eye is a camera eye.** Model it as real lens geometry: an
   outer bezel/housing, a recessed lens, and visible internal
   iris/aperture structure with a bright emissive core. It must NOT be
   a flat emissive texture, a plain dome, or a decal. (The Exercise-2
   model's known defect was exactly a flat lens with no internal
   structure — do not inherit it.)
2. **Texture and detail carry the match.** The result is judged on the
   reference's surface work:
   - per-plate tone and roughness variation in brushed, worn gunmetal —
     no two plates identical;
   - scratches, chips, and bright edge wear on plate edges;
   - grime / AO settled into seams and recesses;
   - vent grilles, and visible rivets, bolts, and fasteners;
   - plate seams with actual depth, and overlapping plate layout;
   - the joint glow rings as SEGMENTED emissive bars — bright
     teal-cyan light segments recessed between dark housing rings —
     at EVERY joint, not a smooth tube of light and not dim;
   - crest fins as thin, detailed metal fins seated in sockets, not
     plain matte blocks.

## Hard contract (game usability — all of these are requirements)

1. Export format: glTF 2.0 binary (`.glb`), +Y up, Apply Modifiers on
   export, tangents exported (a normal map is present), Draco OFF,
   Principled BSDF materials only.
2. Textures: ORM-packed (R = ambient occlusion, G = roughness,
   B = metallic). Albedo and emission textures are sRGB; normal, ORM,
   and other data textures are linear / Non-Color.
3. Triangle budgets: head GLB between 10,000 and 18,000 triangles;
   full assembled snake GLB at or under 60,000 triangles total.
4. Animatable: the body must articulate so the game can pose it along a
   curve. Use ONE of these two rig designs:
   - a skinned mesh driven by a bone chain, at most 4 bone influences
     per vertex, weights normalized; or
   - per-segment rigid meshes, each segment its own mesh with its pivot
     at the joint, so a chain/curve system can pose segment after
     segment.
   The head may be a single static mesh, attached at the neck joint so
   it follows the body. NOTE.md must explain exactly how the game
   animates the model (bone names and count, or the segment pivot
   scheme, and how a pose along a curve is produced).
5. Game check: import the delivered GLBs into the included `game-demo/`
   Godot project (editor import pass) or a scratch Godot 4.7 project,
   confirm the import completes with no errors and the materials
   resolve, and state the result in NOTE.md.

## Your machine

You are running on the Windows host Abraham, inside the WSL distro.
Blender 4.5.14: `/mnt/c/Users/Moore/Blender/blender-4.5.14-windows-x64/blender.exe`
Godot 4.7.2 console: `/mnt/c/Users/Moore/Godot/Godot_v4.7.2-stable_win64_console.exe`

## Working rules

- Open `REFERENCE.png` and your own renders as often as you need and
  iterate inside this run until the match is as close as you can make
  it or the deadline arrives.
- Work only on this job. Do not fetch or read any other build's
  branches, workspaces, or deliverables.
- Deadline: 90 minutes from the dispatch message that sent you here.
  If the deadline approaches with work unfinished, push what is
  complete and state in NOTE.md exactly what is missing.

## Deliverables

Push these files to branch `refmatch-sol-20261017` in the GitHub repo
`ADD-Attack/moorefolio`, in the folder `benchmarks/refmatch/sol/` —
this git push is the one and only delivery channel:

- `snake.blend` — the working Blender file.
- The build script(s) you used (`.py`).
- `snake_head.glb`, `snake_segment.glb`, `snake_full.glb` — the full
  one is the complete assembled, rigged snake.
- The texture PNGs the GLBs use.
- `staging-full.png` — the full snake staged per REVIEW-STAGING.md:
  plain neutral background, neutral studio lighting, nothing else in
  frame, whole snake visible.
- `staging-head.png` — same staging, head close-up, framed so surface
  detail and the eye assembly are judgeable.
- `NOTE.md` — what you built and how; triangle counts for each GLB;
  the texture list; exactly how the model animates; the Godot import
  check result; and your self-assessed gaps versus the reference,
  honestly listed.

Commit with a clear message and push. Delivery is complete when the
branch contains all of the files above.
