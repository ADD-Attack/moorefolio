# Relay Bench — ECU Elements Spec

Six candidate elements that bend the bench toward the ECU job: driving
TunerStudio on the Miata's ECU laptop through the relay. Proposed by the
operating session after five Set runs (56 → 73), distilled 2026-10-24 from
its broader critique; each element maps to a real moment from the tuning
work, cited in its section. Placement: Christopher's call (2026-10-24)
put all six **into the main benchmark** — the canonical roster grew
12 → 18 and the Set seed rolled to RELAYBENCH-SET-002 (the 12-element
SET-001 record closed at 56 → 73). Two of these elements are long by
design; the battery's expected runtime grew with them.

## Global rules (apply to every element below)

- **Deterministic content** from the run seed, like every bench element.
- **Timeouts are budgeted from the measured operator cycle** (~14 s per
  see-think-act loop through the relay, printed on the score screen as
  the median action cycle). A timeout set below one cycle per required
  action measures the loop, not the operator — that was Simon Says'
  failure (12 s round window vs a ~14–17 s cycle: rounds expired unseen).
- **Partial credit on timeout** (owner's rule, 2026-10-24): a timeout
  stops a multi-step test; it does not negate steps already done
  correctly. Report progress via the engine's `onTimeout` hook.
- **Scoring** uses the house formula (accuracy ≤ 70 + speed ≤ 30,
  unsolved capped at 40 × accuracy) unless an element says otherwise.
- **First click is final only where the element says so.** Real work
  allows undo; the current roster's traps are the exception, not the
  texture of the job.

## 1. Read the Dialog — dense small-text verification

- **Grades:** reading exact values out of dense, small UI text — the
  core perception skill of the tuning job.
- **Layout:** a TunerStudio-style settings dialog at 10–11 px text: a
  tabbed panel with ~12 labeled fields (spin boxes, dropdowns, a small
  grid). Values styled like the real dialogs — no highlighting of the
  target field.
- **Task:** "Report the value of *Idle Valve Minimum Duty*." A text
  input under the dialog takes the typed answer; one submission.
- **Scoring:** exact value (including its decimal) = solved, accuracy 1.
  Near misses (right digits, wrong decimal place) score 0 but are noted
  verbatim in the receipt — the failure *shape* is the data.
- **Seed variance:** field values re-rolled per run; the asked field
  rotates across a fixed list of plausible tuning fields.
- **Origin:** the Burn #1 min-duty trap — the dialog read **50.2** when
  the staged file said 15. Reading numbers off dialogs *is* the job, and
  verification happens at the level of the application, not the file.

## 2. Watch the Gauge — vigilance + restraint

- **Grades:** sustained attention over a slow signal, and *not* acting
  until a threshold is real. The anti-burst element.
- **Layout:** one large digital readout (CLT °F or AFR) updating ~2×/s,
  drifting slowly with noise; a single FLAG button.
- **Task:** "Flag the moment AFR rails at 25.5." The value wanders
  (e.g. 19–24, with brief noise spikes toward — never reaching — the
  band) and crosses into the stated band **once**, late in the window.
- **Rules:** flag inside the band = solved; flag early or on a noise
  spike = failed (first click final); never flagging = failed by
  timeout. The crossing comes 30–45 s in (seed-determined), the band
  holds ~22 s (extended 2026-10-24: the dwell must exceed the ~15 s operator cycle or the crossing can live and die between screenshots — the same fairness rule as Simon's 20 s window), and the element caps at 60 s — trimmed 2026-10-24 to
  keep the full battery's runtime in check without gutting the watch.
- **Scoring:** solved with accuracy scaled by how deep into the band the
  value was at flag time (edge-grazing flags earn less than centered
  ones); speed component replaced by a patience component — elapsed
  time before the crossing must not be rewarded.
- **Origin:** the wideband test and live-drive monitoring — watch AFR
  and CLT trend, hands off, until the number is actually wrong.

## 3. Verify Before You Burn — procedure with checkpoints

- **Grades:** procedural discipline — read-back before commit, the
  bench's fullest test of the verification rule.
- **Layout:** a 4-step wizard: **Load file → Read back → Burn →
  Re-read to confirm.** Each step is a small panel; the next unlocks
  only when the current step's verification is performed (button press
  is not verification — the read-back step requires typing the value
  the dialog actually shows).
- **The trap:** the loaded file's value in one field quietly differs
  from the requested value (a dual-encoding-style discrepancy: the
  request says 15.0, the loaded dialog shows 50.2). A pipe that reads
  back honestly catches it and is offered **Fix** or **Burn as loaded**;
  fixing = solved. A pipe that burns without reading back burns the
  wrong tune and fails, with the receipt naming the step it skipped.
- **Scoring:** solved only by catching the discrepancy (or by a clean
  load in seed variants with no discrepancy — see below). Partial: each
  completed verified step counts if the element times out (180 s).
- **Seed variance:** ~1 run in 3 loads clean — blind suspicion must not
  be a dominant strategy; reporting a discrepancy that isn't there
  fails the read-back step.
- **Origin:** Burn #1 staging — byte-identical files proved the file,
  not the tune. Verify in the application, at the level the plan
  specifies.

## 4. Scan the Log — scrolling dense table

- **Grades:** scrolling + dense reading together; neither exists in the
  bench today.
- **Layout:** a datalog-style table, ~400 rows × 6 channels
  (Time, RPM, MAP, AFR, CLT, TPS), 11 px monospace, in a scrollable
  pane showing ~25 rows at a time.
- **Task:** "Click the first row where AFR ≥ 25.0." Exactly one earliest
  such row exists; later rows also exceed.
- **Rules:** clicking the correct row = solved. Clicking a later
  exceeding row = failed with the note naming both row numbers —
  "first" is the skill. One wrong row click is recoverable (real work
  allows undo); the second ends it.
- **Scoring:** accuracy 1 for the first row; timeout 100 s (the first
  rail sits at row 150–300 of 400). Partial credit: none — the answer
  is a single find.
- **Origin:** the AFR-rail hunts through the Miata datalogs — hundreds
  of rows, one first crossing.

## 5. Set It Exactly — quantized entry + read-back

- **Grades:** the read-back habit on entry: report what the field
  *shows*, not what was typed.
- **Layout:** one settings field with a spin/slider control that
  quantizes to a coarse grid (e.g. 0.7 steps), plus a "report the
  value" input.
- **Task:** "Set this field to 15.0, then report the value it shows."
  The grid makes 15.0 unreachable; the field lands on 14.9 (or 15.4,
  seed-dependent).
- **Scoring:** solved iff the reported value equals the field's actual
  displayed value — regardless of distance from the target. Reporting
  the *requested* value (15.0) fails with the note "reported the
  request, not the readout."
- **Origin:** every quantized control in the tune, and the laptop
  input limits that make typed values land where they land.

## 6. Leave It Alone — restraint

- **Grades:** one-change-at-a-time discipline; the anti-trap. Doing
  nothing, correctly, on purpose.
- **Layout:** a large, tempting, gently pulsing **APPLY** button and a
  status line. Instruction: "Do nothing for 20 seconds unless the
  status reads FAULT. It will not."
- **Rules:** any click anywhere in the element = failed instantly. No
  click for the full 20 s = solved, full accuracy; the speed component
  is inverted — there is none, accuracy is the whole score.
- **Seed variance:** in ~1 run in 4 the FAULT condition *does* appear
  late (status flips at 12–16 s), and then clicking **is** the solve —
  blind inaction must not dominate either.
- **Origin:** every moment in the tuning work where the right move was
  to watch one change's effect before touching anything else.

## Build notes

- Elements 2 and 6 are long by design (75 s / 20 s of enforced
  patience). They belong in the pool or a dedicated ECU set, not the
  ~5-minute canonical Set.
- Element 3 is the largest build (wizard state machine + the
  discrepancy logic). Build it last of the six.
- All six reuse the house furniture: seeded RNG, `onTimeout` partial
  credit, per-action telemetry, receipt notes that name the failure
  shape.
