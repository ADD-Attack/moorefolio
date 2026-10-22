# element-log — EDEN-3D-01 aliens_b

Engine: ComfyUI 0.41.0, hunyuan_3d_v2.1 fp16, octree 256, 30 steps, cfg 5, surface net threshold 0.6.
Source: crops of aliens-b-3d-reference.png only (bg sampled at (228,228,228)), padded square, resized to 1024. No 2D art fed.

| time CDT | id | crop | seed | action | reason |
|---|---|---|---|---|---|
| 13:32 | — | c3-tail v1 (0,500,330,940) | — | DECLINED crop pre-send | a body/leg mass sat on the right crop edge, which would grow attached anatomy (framing law) |
| 13:33 | — | c3-tail v2 (0,600,262,900) | — | crop accepted for send | single tail unit, clear on all sides |
| 13:37 | c1-wholebody-s42 | c1 (0,20,1420,1168) whole creature, straight-on 3/4 side | 42 | SENT | base-mass candidate: body + plates + legs + tail in one formed mesh |
| 13:37 | c2-mouth-s42 | c2 (1060,250,1420,950) mouth + collar | 42 | SENT | signature feature at higher resolution; needs lip ring + cavity |
| 13:37 | c3-tail-s42 | c3 v2 | 42 | SENT | segmented tail at resolution for ≥3 rigid segments |
| 13:37 | c1-wholebody-s42 (prompt 92f9ec6c) | c1 | 42 | returned 13:40 | 686k tris, closed-reading body |
| 13:40 | c2-mouth-s42 | c2 | 42 | SENT | (c3 send deferred until after the c2 verdict, sequential foreground runs) |
| 13:44 | c1-wholebody-s42 | c1 | 42 | **APPROVED (base mass)** | the 3 dorsal plate bands, the flank plate row, 4 two-part legs and a ringed tail all formed and read right in both previews; the mouth end is shallow → mouth comes from a separate element |
| 13:44 | c2-mouth-s42 (prompt b8c4ec1c) | c2 | 42 | **DECLINED** | an open half-shell with heavy voxel stair-stepping; the cropped body edge became a flat sheet; the lip ring only partly formed |
| 13:44 | c2b-mouth | re-request: wider crop with the whole mouth + collar + a band of forehead, centred | 7 | RE-REQUEST queued | give the encoder a closed volume to read rather than a cut edge |
