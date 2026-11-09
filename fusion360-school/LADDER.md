# The ladder — Fusion 360 school, semester 1

Six rungs, easiest first. Every rung: Gate 1 bars are **frozen** (set before the attempt, verified independently by the producer) and Gate 2 is the blind panel on the standard renders (`PANEL.md`). Pass = both gates. Miss = one tuned re-run, then the rung closes FAILED and a foundation drill is designed against the convergent fault. The capstone needs the owner's verdict.

All dimensions mm. "Target" values come from the brief's spec sheet, issued with each rung.

---

## Ex1 — The constrained plate

A mounting plate from a spec sheet: outline, hole pattern, edge fillets.

**Gate 1**
- Every sketch fully constrained (0 DOF)
- All driving dimensions are named user parameters
- Bounding box within ±0.1 of spec; hole positions within ±0.1
- Volume within ±1% of the spec-computed target
- Timeline: 0 errors, 0 unresolved warnings

## Ex2 — The flex test

A bracket-style part, fully parametric — then prove it.

**Gate 1**
- Ex1's discipline bars, plus:
- Change 3 driving parameters by ±20% (producer picks which): rebuild with 0 errors
- Post-flex volume tracks the recomputed target within ±2%
- Reset to spec values: model returns clean

## Ex3 — Match the drawing

Reproduce a part from three orthographic views (supplied as the brief's input).

**Gate 1**
- Bounding box within ±0.2 on all axes
- Hole/feature positions within ±0.15
- Volume within ±1.5% of the reference part
- Gate 2 panel grades the match against the reference renders

## Ex4 — Assembly with joints

A 3-component assembly (base, arm, slider or wheel) with real motion.

**Gate 1**
- Components and joints only — no eye-balled placement
- Degrees of freedom exactly as spec'd
- Joint limits set to spec
- Interference check: 0 clashes across the full joint-range sweep

## Ex5 — The form part

A grip/handle-class part built with sweep or loft through station profiles.

**Gate 1**
- Section profiles at the spec'd stations within ±0.3
- Volume within ±3%
- No self-intersections; surface passes a curvature/zebra sanity read for the panel set

## Ex6 — Print-ready

A functional part under manufacturing constraints (wall minimum, overhang limit, mass budget) from the brief.

**Gate 1**
- Exported mesh watertight and manifold
- Minimum wall ≥ spec everywhere (measured, not sampled once)
- Mass ≤ budget; bounding box within the printer envelope in the brief

## Capstone — the commission

A small multi-part product from a one-paragraph commission (the owner's pick — a toy car with rolling wheels is a fine first subject). All prior disciplines apply. **Owner verdict required** — gates and panel advise; the owner decides.

---

## Foundation drills (the producer assigns these when a rung fails twice)

- **Constraint drill** — five sketches, each constrained three different ways; bar: 0 DOF, every time, no redundant-constraint warnings.
- **Flex drill** — take a supplied fragile model, make it survive ±25% parameter changes; bar: 0 rebuild errors.
- **Measurement drill** — model three parts to spec and report every Gate 1 number *before* the producer measures; bar: your numbers and the producer's agree within measurement noise. (This drill exists because self-measurement drift is the most common silent failure.)
- **Timeline drill** — rebuild a supplied messy design cleanly; bar: same geometry, ≤ half the features, 0 warnings.
