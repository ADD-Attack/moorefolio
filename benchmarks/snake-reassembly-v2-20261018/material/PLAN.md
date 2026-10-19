# Material plan — P8 geometry frozen

1. Assign shader regions to existing polygons/components; preserve mesh and instance fingerprints.
2. Worn warm gunmetal plates, per-plate palette and .35–.55 roughness; dark steel housings, recesses and grilles; polished hardware; brighter worn edges; restrained directional micro-scratches and rust/grime. No text/decals or extra glow.
3. Segmented bars teal-mint #71CCBD. Eye follows REFERENCE-SPEC radial profile: white-hot core → pale mint → teal rim → dark bezel/groove → machined lip/housing. Existing optical mesh only.
4. UVs and baked base-color, tangent normal, packed ORM (AO R, roughness G, metalness B), emission where applicable. Canonical export materials separate from review AO multiplication.
5. Cycles preview full/head/module/tail before judged capture. Keep P8/P7 cameras, lights, catcher and #C1C1BF staging; enable tight subtle glare via Blender 4.5 node inputs.
6. Independent GLB maps/hierarchy/budget inspection; source mesh fingerprints unchanged. Production captures 1920×1080 / Cycles 256-class adaptive denoise. Same-angle reference comparisons; render-only full scorecard and explicit unreviewed flags.
