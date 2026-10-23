# STITCH-REGEN attempt 2 — ACCEPTANCE FAILED → STOPPED (per order item 6). Forge, 2026-10-22 21:10 CDT

**Result:** the regenerated element is good: two-row lumpy pads, with the root transition formed by Hunyuan. It **cannot be seated without a visible lip/gap.** Across three seat depths/scales, either the element's open cut or its transition edge shows at the top of the root (captures/rg-*, rg2-*).

**Build of record is unchanged:** the folder-root GLB/blend is still STITCH-BLEND 98a44eb (which the owner has ruled against). Materials remain paused.

**Diagnosis (why it fails):** Hunyuan formed the transition for its *own* closed rear-body blob. That contour (blob size, how high the tail exits, the plate edges above it) doesn't match our bace685 rear. Wherever the two surfaces disagree, cutting off the blob leaves an exposed edge. Moving the transition into the generated form only works if the generated body contour **is our body's contour**.

**Proposals (not applied; owner/producer to choose):**
1. **Generate from our own body (recommended).** Edit source = a render of our bace685 clay's rear, not the pack image. Ask the image model to add the reference-anatomy tail growing out of *that* rear, then run Hunyuan on it. The transition would then be formed against our actual contour, and the blob would coincide with our body, so the cut sits on matching surfaces.
   - Fence note: this is derived from our model, which is itself derived from the pack reference. The pack reference stays MATCH ground truth. I would treat this as within fence 1 but want the owner's OK, since it changes the edit source.
2. **Junction remesh in Blender.** Union the tail root with the body locally and voxel-remesh/smooth only the socket zone. That is a Blender seat fix and a body edit, so I won't do it without an explicit ruling.
3. **Revert to the GATE-RETRY v2 seat (2c25df3).** It is the panel-passed state: plug read, no gap.

**Contract of the failed attempt (for the record):** 41,893 tris, 9 nodes; body/mouth/legs untouched.
