# Backpacks on animated characters: straps that don't twist

This is a recipe that works in any engine (Unreal, Unity, Godot, your own). It comes with a small Unreal 5.0 demo. In the demo, a mannequin runs, jumps, crouches and takes the pack on and off. The screenshots in this folder come from that demo.

If you've spent days fighting this, you're not doing anything unusual. Twisting straps are one of the most common problems in character work. The fix is mostly about *not* doing the obvious thing.

---

## (a) Why the straps twist

Two things usually cause it, and they often show up together.

1. **Smooth skin weights across joints.** If a strap is skinned like clothing, it gets weights blended over several bones: spine, clavicle, upper arm, chest. When those bones rotate, each vertex lands somewhere between them. A flat strap then gets a "candy wrapper" twist where the bone influences cross, and it stretches and pinches around the shoulder. This is what skinning is *supposed* to do to skin. It's wrong for a stiff piece of webbing.
2. **Cloth or physics fighting the animation.** A simulated strap is pulled by gravity and pushed by collision against a body that teleports a few centimetres every frame. Run, jump and crouch are exactly the fast, bendy motions where the solver loses. You get jitter, popping and straps sinking into or flying off the shoulder. Tuning collision against the clothing then becomes an endless loop.

Real backpack straps are stiff bands that ride on the shoulder. They don't need to deform at all. They need to *follow* the body.

## (b) The fix: make every strap piece follow exactly one bone

There are two ways to build it. Both use the same rule: **each piece of strap is driven 100% by one bone, never a blend.** A piece that follows one bone moves rigidly with it, so it can't twist or stretch.

### Variant 1: segmented rigid straps (built in-engine, what the demo uses)

Cut each strap into short pieces and parent each piece to one bone:

| Piece | Parent bone (Unreal mannequin names) |
|---|---|
| Front strap panel (shoulder down the chest) | upper chest / `spine_05` |
| Shoulder bridge (over the top of the shoulder) | `clavicle_l` / `clavicle_r` |
| Back strap panel (shoulder blade down to the pack) | upper back / `spine_05`* |
| Pack body | a socket on the mid back / `spine_03` |

\*The demo first parented the back panels to `spine_03`, the same bone as the pack. During a jump, the gap between the shoulder bridge and the back panel then opened by **7.5 cm**: the clavicle moves a lot relative to the mid spine. Moving the back panels to the upper spine bone brought the worst case to about **4.6–5.6 cm**, and the overlap below hides that. The lesson is general: **put each piece on the bone that moves least relative to its neighbours.**

Steps:

1. Pose the character in its bind/rest pose (or a neutral idle).
2. Build the strap pieces so they sit **just on top of the torso silhouette**, a few millimetres to about 1 cm off the surface. Thin flat boxes are fine to start with.
3. **Overlap the pieces where they meet.** The shoulder bridge should run past the ends of the front and back panels by a few centimetres. The demo uses 6 cm, and it measured the seams drifting up to about 5.6 cm during jumps, so the overlap always covers the gap. Tuck the bottom of the back panel a few centimetres under the pack's lid as well.
4. Parent each piece to its bone (in Unreal: attach to the skeletal mesh at the bone name, keeping the world transform). Don't skin them.

That's the whole strap system. The demo's ledger checks every beat that each piece is still on its bone with its original relative transform, and it always is. That's the "can't twist by construction" part.

### Variant 2: one skinned strap mesh with hard weights (built in your 3D package)

If you'd rather have a single continuous strap mesh, you can. Just weight it differently from the body:

1. Model the strap in your DCC (Blender, Maya, etc.) over the bind pose, slightly off the surface.
2. Split it into the same regions as above: chest section, shoulder section, back section.
3. Give every vertex **100% weight to one bone**, with no blending. Chest-section vertices go to the chest bone, shoulder-section vertices to the clavicle, back-section vertices to the upper spine.
4. Where two regions meet, add a small overlap or a fold (a strap passing under a buckle or a slider). That hides the hard break, the same trick as the overlap in Variant 1.
5. Export it with the character and keep it on the same skeleton.

Hard weights give you exactly the rigid behaviour of the segmented version inside one mesh. (The demo didn't build this variant, because no 3D package was available on the build machine. The steps are the standard workflow.)

## (c) The pack itself: a socket plus bounded sway

1. **Make the pack a rigid prop**, not part of the skinned character. Attach it to a socket on the mid/upper spine (`spine_03` in the demo), placed where the pack rests against the back.
2. **Put the pivot at the top-front edge** where the pack rests on the back, so any sway swings the bottom of the pack.
3. **Add a small spring lag, and clamp it.** Each frame, read the acceleration of the socket bone, turn it into a small target pitch/roll, and run a damped spring toward it. Then **clamp the result**; the demo uses ±7°. Running starts, stops and landings give the pack a little life. The clamp stops it from ever flapping into the body.
4. Don't use a physics body for the pack. A simulated pack fights the animation for the same reasons simulated straps do.

In the demo the sway hits the 7° clamp on run starts and landings and settles back. That's bounded by design, not simulated.

## (d) Why you don't need strap-to-clothing collision

Collision is the thing people usually try to tune, and it's the thing this approach makes unnecessary.

- Each strap piece rides *on the same bone* as the body surface under it, so the gap between strap and body doesn't change when that bone moves. If it starts 5 mm off the shirt, it stays 5 mm off the shirt.
- The only relative motion is at the seams between pieces on different bones, and the overlap hides it.
- So there's nothing for collision to do. The demo turns collision **off** on every strap and pack piece, and nothing clips through the body in run, jump or crouch.

If clipping does show up somewhere (a big shoulder deformation, say, or a bulky jacket), first move the strap slightly further out from the surface, or move that piece to a better bone. Only add more pieces if that doesn't work. Don't reach for collision.

## (e) Putting it on and taking it off

Fully animated donning and doffing (an arm through one strap, swinging the pack round, the second arm in) is the expensive path. It needs hand-keyed animation, often with straps that are animated or swapped mid-move. Most shipped games don't do it, and the ones that do treat it as a special animated sequence. They don't simulate the straps for it.

The practical game approach, which the demo uses (key **E**):

- Toggle the pack and straps on or off with a short **0.25 s** "beat". The demo scales the pieces down/up, and a fade or a particle puff works just as well.
- Cover it with a quick generic arm gesture if you like.
- The pieces stay attached to their bones the whole time, so re-equipping always lands exactly right.

If you later want the full animated version, build it as a one-off animation with its own strap pieces animated by hand. Keep the rigid setup above for all normal gameplay.

---

## Quick checklist

- [ ] No cloth, no physics on straps.
- [ ] Every strap piece (or every strap vertex) is driven 100% by one bone.
- [ ] Pieces sit just off the body surface in bind pose.
- [ ] Pieces overlap at the shoulders; the back strap tucks under the pack lid.
- [ ] The pack is a rigid prop on a spine socket, with a clamped spring sway.
- [ ] Collision on straps and pack is off.
- [ ] Equip/unequip is a quick visual beat, not a simulation.

Good luck. Once the straps stop being cloth, this problem mostly goes away.
