# BRAMBLE — goblin raider

A full-body, stylized character study: a grizzled road warden with a lowered axe, a hand on his belt, and mismatched scavenged equipment.

**Geometry.** Entirely modeled in Python, without external assets. The head and arms use voxel-unified anatomical volumes with subdivision and subtle displacement. Custom meshes form cupped ears, eyelid hoods, tailored leather panels, draped cloth, articulated armor, greaves, and the solid beveled axe. Surface-projected wrinkles and scars follow the head sculpt. Individual fingers, tusks, jewelry, stitches, lacing, rivets, wood grain, and thousands of tapered fur hairs provide secondary detail.

**Materials.** Procedural PBR shaders distinguish mottled, pore-textured olive skin; warmer nose and cheek tissue; distressed hide; woven oxblood cloth; blued iron; exposed steel; antique bronze; and root-darkened ivory. Amber eyes include radial iris fibers, slit pupils, and refractive corneal lenses.

**Lighting and render.** Blender **4.5.14 LTS**, **Cycles / OptiX GPU**, **192 maximum samples**, adaptive threshold **0.008**, denoising, and eight maximum light bounces. A warm 1300 W key, cool 650 W fill, and 1700 W rear rim form the three-point studio setup. Neutral gray seamless floor and world; 66 mm perspective camera; AgX Medium High Contrast. Output: **1920 × 1080 PNG**.

**Reproduce:** `blender -b --factory-startup --python build.py`

The script writes `render.png` beside itself. No downloads, textures, add-ons, or other files are needed. Optional `-- --preview` produces a separate half-resolution development render.
