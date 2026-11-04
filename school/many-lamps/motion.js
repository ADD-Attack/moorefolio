// W-Ex11-X2 §K — the Extravaganza preset and its lamp motion. Additive: presets.js stays frozen; this adds one key.
// Motion is a pure function of an integer tick t: the phase uses (t mod period)/period, so the angle never grows
// and nothing accumulates. Same t → same lamps, bit for bit.
(function (root) {
  'use strict';
  const TWO_PI = 2 * Math.PI, deg = a => a * Math.PI / 180;
  const phaseAt = (t, period) => TWO_PI * (((t % period) + period) % period) / period;

  //   orbit — position on an ellipse about (cx, cy): pos = (cx + rx cos θ, cy + ry sin θ), θ = phase + 2π·(t mod P)/P
  //   spin  — fixed position, aim turns full circles: aim = aim0 + dir·2π·(t mod P)/P
  //   sweep — fixed position, aim swings: aim = aim0 + amp·sin(2π·(t mod P)/P)
  function poseAt(m, t) {
    const th = phaseAt(t, m.period);
    if (m.kind === 'orbit') { const a = (m.phase || 0) + (m.dir || 1) * th;
      const o = { pos: [m.cx + m.rx * Math.cos(a), m.cy + m.ry * Math.sin(a)] };
      if (m.aimFollows) o.aim = a + Math.PI; return o; }
    if (m.kind === 'spin') return { aim: m.aim0 + (m.dir || 1) * th };
    if (m.kind === 'sweep') return { aim: m.aim0 + m.amp * Math.sin(th) };
    return {};
  }

  // Saturated lamps, coloured walls: every channel's reflectivity ≤ 0.9, so every channel settles with the clamp off.
  const EXTRAVAGANZA = { name: 'Extravaganza',
    surfaces: { floor: { refl: 0.5, color: [1, 0.7, 0.15] }, right: { refl: 0.9, color: [0.1, 0.45, 1] },
      ceiling: { refl: 0.6, color: [0.75, 0.3, 1] }, left: { refl: 0.9, color: [1, 0.12, 0.3] } },
    lamps: [
      { type: 'bulb', pos: [6.6, 2.5], color: [1, 0.1, 0.85], brightness: 1.6, motion: { kind: 'orbit', cx: 4, cy: 2.5, rx: 2.6, ry: 1.35, period: 360, phase: 0 } },
      { type: 'bulb', pos: [2.2, 2.5], color: [0.1, 0.85, 1], brightness: 1.4, motion: { kind: 'orbit', cx: 4, cy: 2.5, rx: 1.8, ry: 0.9, period: 270, phase: Math.PI, dir: -1 } },
      { type: 'spotlight', pos: [2, 1.2], aim: deg(40), color: [1, 0.78, 0.08], brightness: 0.5, motion: { kind: 'spin', aim0: deg(40), period: 240 } },
      { type: 'laser', pos: [6.5, 3.9], aim: deg(215), color: [0.15, 1, 0.3], brightness: 0.22, motion: { kind: 'sweep', aim0: deg(225), amp: deg(55), period: 200 } },
      { type: 'spotlight', pos: [6.1, 1.1], aim: deg(120), color: [0.6, 0.2, 1], brightness: 0.45, motion: { kind: 'spin', aim0: deg(120), period: 300, dir: -1 } },
    ] };
  // A preset's lamps sit at their tick-0 pose, so the frozen preset and the motion agree at t = 0.
  for (const L of EXTRAVAGANZA.lamps) Object.assign(L, poseAt(L.motion, 0));

  const api = { poseAt, phaseAt, EXTRAVAGANZA, CAP_PER_FRAME: 3 };
  if (root.LAMP_PRESETS) root.LAMP_PRESETS.extravaganza = EXTRAVAGANZA;
  if (typeof module !== 'undefined') module.exports = api; else root.Motion = api;
})(typeof window !== 'undefined' ? window : globalThis);
