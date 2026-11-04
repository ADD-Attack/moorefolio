// W-Ex11-X presets (shared by the page and the QA harness).
(function (root) {
  const W = [1, 1, 1], deg = a => a * Math.PI / 180;
  const grey = () => ({ floor: { refl: 0.45, color: W }, right: { refl: 0.8, color: W }, ceiling: { refl: 0.85, color: W }, left: { refl: 0.8, color: W } });
  const PRESETS = {
    original: { name: 'Original room', surfaces: grey(), lamps: [{ type: 'panel', patch: 16, color: W, brightness: 1 }] },
    bleed: { name: 'Colour bleed', surfaces: { floor: { refl: 0.6, color: W }, right: { refl: 0.8, color: W }, ceiling: { refl: 0.85, color: W }, left: { refl: 0.95, color: [1, 0.12, 0.08] } },
      lamps: [{ type: 'bulb', pos: [5.6, 3.2], color: W, brightness: 1 }] },
    mixed: { name: 'Mixed lamps', surfaces: grey(),
      lamps: [{ type: 'spotlight', pos: [1.3, 0.9], aim: deg(48), color: [1, 0.25, 0.15], brightness: 1.2 },
              { type: 'laser', pos: [6.6, 4.1], aim: deg(205), color: [0.2, 0.45, 1], brightness: 1 },
              { type: 'bulb', pos: [4.6, 2.6], color: [0.35, 1, 0.45], brightness: 0.6 }] },
    split: { name: 'Channels split', surfaces: { floor: { refl: 1.1, color: [1, 0.8, 0.55] }, right: { refl: 1.1, color: [1, 0.8, 0.55] }, ceiling: { refl: 1.1, color: [1, 0.8, 0.55] }, left: { refl: 1.1, color: [1, 0.8, 0.55] } },
      lamps: [{ type: 'bulb', pos: [4, 2.5], color: W, brightness: 1 }] },
  };
  if (typeof module !== 'undefined') module.exports = PRESETS; else root.LAMP_PRESETS = PRESETS;
})(typeof window !== 'undefined' ? window : globalThis);
