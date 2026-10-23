# STATUS — EDEN-3D-01 — STITCH-BLEND DELIVERED (post-gate, owner-directed). STOPPED for the producer spot re-panel (Cat 1B + Cat 4, 3 judges each).

**Done:**
- Pipeline tail kept; scaled −10%.
- Root blended: a widening skirt saturating at the body surface, seated deeper; old stalk buried; no cork step in the full view.
- Body, mouth and legs byte-identical to 2c25df3.
- 41,692 tris, 9 nodes.
- Fresh full / tail / mouth captures + reference compare.

**Residuals:** a slight rim at the low close-up; old c1 stalk lumps near the hind leg (body geometry, untouched by order). A body-socket feather fixes both, on the owner's word.

**Materials:** PAUSED at b5f72d3 (checkpoint 4f0a58e). Resume needs the producer's explicit go plus a tail-region re-bake on this geometry.

## 20:52 CDT — STITCH-REGEN in progress (owner override)
- The STITCH-BLEND seat (98a44eb) is discarded by owner ruling (lip visible at full-body angle). The base returns to the bace685 body.
- Regenerating the tail WITH its root transition (tail + rear-body margin, two-row lumpy pads, 3 candidates); Hunyuan element; stitch = seat + cut only, no skirt.
- Materials paused again.

## 21:12 CDT — RESTRUCTURE attempt 2, STEP 1 DONE → STANDING BY
Candidates pushed: generated/gen-tail2-cand-01/02/03.png. Element-log entry per candidate (my pick: cand-02). No masking, Hunyuan or stitching in this step. Awaiting the owner's pick and the producer's step-2 go. (The pre-gate attempt-2 run is archived in stitch-regen-attempt2-FAILED/ and is not acted on.)

## 21:20 CDT — STEP 1 (AMENDED: reference crops) DONE → STANDING BY for the owner's pick
- generated/gen-tail2-cand-01/02/03.png are now reference CROPS (pixels untouched, flat-padded). The earlier edit-based files are moved to generated/superseded-edits/.
- **Usability concerns (stated, not acted on):**
  1. The reference shows the tail from a front-left 3/4 angle, not true side-on. Hunyuan will infer the far side.
  2. Every window that holds the root transition must hard-cut the body at the crop edge. This ticket's history (c2/c2b/c3 at gate 1) shows cut body edges grow walls/sheets. Those would fall in the discard zone, but they may distort the transition itself.
  3. The hind-leg shoulder pad overlaps the lower root in any window wider than cand-01.
  - Possible mitigations, for the owner to choose: (a) mask the leg out at prep; (b) outpaint only the cut body margin, keeping tail pixels untouched (flagged regions); (c) use cand-01 and accept a thinner transition.
- No masking, Hunyuan or stitching done in this step.

## 21:24 CDT — STEP 1 FINAL FORM → STANDING BY
Candidates are now pure crops: bare reference rectangles with zero generated pixels and no padding. The mitigation list in my 21:20 note is reduced to non-generative options only: (a) mask/flatten the leg and background at PREP, or (c) use cand-01. Option (b), outpainting, is struck by owner ruling.

## 21:02 CDT — FEED IMAGE SELECTED → continuing (prep → Hunyuan → judge → stitch)
**generated/gen-tail2-cand-02.png**, pure crop (0,560,420,960) of the pack reference. Reason: the most root transition in frame; the leg pad is in the discard margin.
