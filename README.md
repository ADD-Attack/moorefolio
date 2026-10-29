# Backpack straps that don't twist — a small UE5 demo + recipe

A rigged character that runs, jumps and crouches — with a backpack whose shoulder straps **never twist, stretch or pop off**. Built as a demo for a fellow dev who'd spent days fighting exactly this problem.

**Start with [TECHNIQUE.md](TECHNIQUE.md)** — the full recipe, engine-agnostic (Unreal, Unity, Godot, your own), including *why* straps twist in the first place.

## The one-sentence version

Don't simulate the straps and don't skin them like clothing: **every strap piece follows exactly one bone** (segmented rigid pieces in-engine, or hard 100%-to-one-bone weights in a DCC), the pack is a rigid prop socketed to the back, and the only motion you add is pack sway **clamped to ±7°**.

## What's in here

- `TECHNIQUE.md` — the recipe: both build variants step by step, the overlap rule, why the clothing-collision problem disappears, and an honest note on don/doff animations.
- `Source/` — the demo's code. `BackpackRig` builds the segmented strap assembly (front panels → upper chest, shoulder bridges → clavicles, back panels → upper spine, pack → mid-back socket) plus the clamped spring sway and the equip/unequip beat. `BPDemoGameMode` runs the autoplay capture loop.
- `BackpackLedger.txt` — the measured run log from the demo's standalone autoplay pass: every beat (run / jump / crouch / back view / unequip / equip) with seam-drift and sway numbers. Worst seam drift: **5.58 cm** in the jump, hidden by the segment overlap.
- `BackpackDemo.uproject` + `Config/` — project shell (UE 5.0, Third Person template content required for the mannequin).

## Honest stand-ins

- The crouch uses the template's capsule crouch with a torso-pitch stand-in pose — the template ships no crouch animation. The straps' behavior under the bend is the point of that beat.
- The demo's segment overlap is 6 cm against a measured 5.6 cm worst drift — close. For a real asset, use 8 cm (the writeup says why).

## Screenshots

The capture set (front run, jump, crouch, back view, unequipped) is in the Reddit thread this was made for, and in the short video alongside it — image files aren't in this repo, the code and numbers are.
