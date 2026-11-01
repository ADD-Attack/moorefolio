# Fusion 360 School — drag-and-drop kit

A school for an agent that builds in Fusion 360. Exercises, gates, a judge panel, and a lessons file — packaged so you can hand the whole thing to your agent and it sets itself up.

## Install (60 seconds)

1. Drag this folder into your agent's workspace.
2. Tell your agent: **"Read START-HERE.md and set yourself up."**
3. The agent adopts the charter, starts its lessons file, and attempts Exercise 1.

That's it. No framework, no fine-tuning — files, gates, and verdicts.

## What's inside

| File | For | What it does |
|---|---|---|
| `START-HERE.md` | the agent | Setup steps + how a school rung runs |
| `CHARTER.md` | the agent | Standing rules for a Fusion 360 builder |
| `LESSONS.md` | the agent | Its work manual — starts with seed lessons, grows after every graded attempt |
| `LADDER.md` | both | Six exercises with frozen, measurable pass bars |
| `PANEL.md` | the producer | The blind judge panel protocol (grades renders cold) |
| `templates/` | both | One brief template, one record template |

## The method in one paragraph

The agent works a ladder of exercises, each aimed at a real weakness. Every rung is graded by two gates: **Gate 1** — measured bars a script can check (dimensions, volume, constraint status, interference), verified independently, never from the agent's own numbers; **Gate 2** — a blind panel of three judges grading standard renders as if a human modeled the part. A miss earns one tuned re-run; a second miss closes the rung as failed, and the agent gets a foundation drill on the missing fundamental before re-attempting — rungs are never just dropped. After every graded attempt the agent writes dated lessons into its own `LESSONS.md`. The human's verdict overrules everything and is recorded verbatim.

*Distilled from a school system running in production on several builder agents. This is the starter skeleton — enough to run your first semester.*
