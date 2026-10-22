# STATUS — EDEN-3D-01 — GATE-RETRY v2 DELIVERED (operative). STOPPED for the producer re-panel (Cat 4 + Cat 1B). The gate stands FAILED until re-tried. No materials.

**Done:**
- Regenerated tail reference (gpt-image-1.5, reference-derived, self-approved) → Hunyuan tail element (c4b, prompt 7e640c0c, approved) → Blender stitch replacing tail_01..03 only.
- bace685 body/mouth/legs verified byte-identical.
- 41,694 tris, 9 nodes.
- Fresh full / mouth / tail captures + reference compare; element-log, NOTE, STATUS.

**Superseded:** GATE-RETRY v1 (a834870, hand-modelled tail + ×4 grooves). Kept for the record; not in the GLB.

**Residuals:**
- Tail rings are single-row (the reference has two-row pads).
- Body seams are U-channels with slight waviness (bace685 state, unchanged by order).

## Variant labels (per Muse's operative order)
- **OPERATIVE gate retry:** `2c25df3`. Pipeline tail (regenerated ref → Hunyuan c4b → stitch) on the bace685 base. This is the GLB/blend at the folder root.
- **FALLBACK only, not the retry:** the Blender clay tail variants, 5e83668 (TAIL-PASS) and a834870 (GATE-RETRY v1, hand-modelled + ×4 grooves). Their captures are in `captures/FALLBACK-clay-tail/`; their GLBs live in those commits.

## How I see this method working (Forge, my own read)
**The plan as run:**
1. Regenerate one *isolated whole unit* (the tail alone, side view, exaggerated) as an edit of the pack ref.
2. Mask it to a flat background.
3. Run Hunyuan on that.
4. Convert the element to a clean manifold before decimating.
5. Scale and seat it to the socket.
6. Cut it into the 3-node chain.
7. Hash-verify that every other node is untouched.

**Why it works:** the strongest lesson of this ticket is that Hunyuan forms *whole, isolated units* cleanly and melts anything cut from a larger image. The generator lets us manufacture exactly that kind of input: a view the pack never had. That is the real gain of the capability, more than "exaggeration".

**Concerns:**
1. **Two inventive steps.** The image model simplified the reference's two-row lumpy pads into single-row rings. Exaggeration requests push it toward a generic "segmented tail". MATCH could drop on F5 even as QUALITY rises.
2. **Image hygiene matters more than the prompt.** The first Hunyuan send grew slabs from the generated drop shadow. Generated refs need masking/flattening as a standard step.
3. **Scale and seat are still my judgment calls** (length 0.42, ×1.45 thickness). The image fixes the form, not the size relative to the body.
4. **The joint is a plug, not a blend.** The tail seats into the socket rather than flowing from it as in the reference. That's fine for a rigid tail chain, but visible up close.
5. **Cat 4 isn't moved by this.** The gate's blocking number is body detail QUALITY, and this method by design changes only the tail.

**Better ideas, for the owner's consideration:**
- **Use the same route for the body detail gap:** regenerate a reference with crisper plate seams and send a whole-body pass, then transfer only the seam relief onto the bace685 body (projection/shrinkwrap of the detail, keeping the form). That attacks Cat 4 with the pipeline instead of hand-tuning.
- **Ask the image model for "two rows of lumpy pads, as in the reference"** rather than generic rings, and generate 2–3 candidates to pick from. That's cheap, and it protects MATCH.
- **Standardize the generated-ref prep:** saturation mask → flat bg → square pad.
