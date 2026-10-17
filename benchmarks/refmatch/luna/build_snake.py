#!/usr/bin/env python3
"""Production snake for Exercise 1 (MODELS) — scripted Blender build.

Run:  blender -b --factory-startup -noaudio --python build_snake.py

Builds three glTF deliverables in this directory:
  snake_segment.glb - one body segment, origin at segment center
  snake_head.glb    - head assembly (skull loft + jaw + eyes + nostrils),
                      origin at the neck so it can pivot on the body chain
  snake_full.glb    - head + 3 segments posed in a slither S-curve

Method: every part is a LOFT — parametric cross-section rings skinned in
order, so topology is clean quad flow along the part (the way a modeler
would box-model it), UVs are analytic (U along length, V around), the
belly gets its own smooth material slot, and shaping (cranium swell,
brow ridges, eye sockets, dorsal ridge, flattened belly) is done by
profile + displacement functions, all reproducible from this file.

Axes: Blender Z-up, part length along +X, head faces +X. glTF export uses
+Y up; in Godot the demo orients instances by basis, see demo notes.
One texture tile = 1.55 world units (see build_textures.py).
"""
import math
import os

import bpy
from mathutils import Euler, Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, "textures")
TILE = 1.55           # world units per texture tile
BELLY_HALF = 0.62      # radians around belly centerline -> belly material

# ---------------------------------------------------------------- materials

def _img(name, colorspace):
    path = os.path.join(TEX, name)
    img = bpy.data.images.load(path)
    img.colorspace_settings.name = colorspace
    return img


def _principled(mat):
    return mat.node_tree.nodes["Principled BSDF"]


def _inp(node, *names):
    for n in names:
        if n in node.inputs:
            return node.inputs[n]
    raise KeyError(names)


def make_plate_material(name, tint=(1.0, 1.0, 1.0)):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = _principled(mat)
    base = nt.nodes.new("ShaderNodeTexImage")
    base.image = _img("snake_albedo.png", "sRGB")
    orm = nt.nodes.new("ShaderNodeTexImage")
    orm.image = _img("snake_orm.png", "Non-Color")
    nrm = nt.nodes.new("ShaderNodeTexImage")
    nrm.image = _img("snake_normal.png", "Non-Color")
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    sep.mode = "RGB"
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nmap.inputs["Strength"].default_value = 1.0
    nt.links.new(base.outputs["Color"], _inp(bsdf, "Base Color"))
    if tint != (1.0, 1.0, 1.0):
        mix = nt.nodes.new("ShaderNodeMixRGB")
        mix.blend_type = "MULTIPLY"
        mix.inputs[0].default_value = 1.0
        mix.inputs[2].default_value = tint + (1.0,)
        nt.links.new(base.outputs["Color"], mix.inputs[1])
        nt.links.new(mix.outputs["Color"], _inp(bsdf, "Base Color"))
    nt.links.new(orm.outputs["Color"], sep.inputs["Color"])
    nt.links.new(sep.outputs["Green"], _inp(bsdf, "Roughness"))
    metal = nt.nodes.new("ShaderNodeMath")
    metal.operation = "MULTIPLY"
    metal.inputs[1].default_value = 0.58
    nt.links.new(sep.outputs["Blue"], metal.inputs[0])
    nt.links.new(metal.outputs[0], _inp(bsdf, "Metallic"))
    nt.links.new(nrm.outputs["Color"], nmap.inputs["Color"])
    nt.links.new(nmap.outputs["Normal"], _inp(bsdf, "Normal"))
    return mat


def make_belly_material():
    mat = bpy.data.materials.new("SnakeBelly")
    mat.use_nodes = True
    bsdf = _principled(mat)
    _inp(bsdf, "Base Color").default_value = (0.10, 0.13, 0.14, 1.0)
    _inp(bsdf, "Metallic").default_value = 0.35
    _inp(bsdf, "Roughness").default_value = 0.52
    return mat


def make_eye_material():
    mat = bpy.data.materials.new("SnakeEye")
    mat.use_nodes = True
    bsdf = _principled(mat)
    _inp(bsdf, "Base Color").default_value = (0.003, 0.009, 0.012, 1.0)
    _inp(bsdf, "Metallic").default_value = 0.42
    _inp(bsdf, "Roughness").default_value = 0.10
    # Dark coated optical glass; the separate sensor core provides the glow.
    _inp(bsdf, "Emission Color", "Emission").default_value = (0.0, 0.025, 0.018, 1.0)
    _inp(bsdf, "Emission Strength").default_value = 0.12
    return mat


def make_panel_material():
    mat = bpy.data.materials.new("SnakeArmorPanels")
    mat.use_nodes = True
    bsdf = _principled(mat)
    _inp(bsdf, "Base Color").default_value = (0.34, 0.38, 0.39, 1.0)
    _inp(bsdf, "Metallic").default_value = 0.72
    _inp(bsdf, "Roughness").default_value = 0.32
    return mat


def make_eye_core_material():
    mat = bpy.data.materials.new("SnakeEyeCore")
    mat.use_nodes = True
    bsdf = _principled(mat)
    _inp(bsdf, "Base Color").default_value = (0.12, 0.80, 0.67, 1.0)
    _inp(bsdf, "Metallic").default_value = 0.0
    _inp(bsdf, "Roughness").default_value = 0.18
    _inp(bsdf, "Emission Color", "Emission").default_value = (0.12, 0.95, 0.78, 1.0)
    _inp(bsdf, "Emission Strength").default_value = 2.2
    return mat


def make_glow_material():
    """Emissive trim (segment joint rings, head neck ring). Emission
    strength is 1.0 on purpose: the game's ACES tonemapper clips
    saturated emissives toward white above ~2. Exercise 2 (fix #4):
    the emission is textured with snake_glow.png, a falloff gradient
    across the torus tube (bright core, dark rim), and the hue is
    deepened so ACES keeps it green instead of clipping it to mint."""
    mat = bpy.data.materials.new("SnakeGlow")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = _principled(mat)
    _inp(bsdf, "Base Color").default_value = (0.004, 0.03, 0.01, 1.0)
    _inp(bsdf, "Metallic").default_value = 0.0
    _inp(bsdf, "Roughness").default_value = 0.4
    grad = nt.nodes.new("ShaderNodeTexImage")
    grad.image = _img("snake_glow.png", "sRGB")
    nt.links.new(grad.outputs["Color"],
                 _inp(bsdf, "Emission Color", "Emission"))
    # White factor on purpose: the mint tint is baked into the
    # gradient texture. Blender ignores this default once a texture
    # is linked, but glTF multiplies factor x texture — tint in the
    # texture + white factor is the only setup both paths agree on.
    _inp(bsdf, "Emission Color", "Emission").default_value = (1.0, 1.0, 1.0, 1.0)
    _inp(bsdf, "Emission Strength").default_value = 1.0
    return mat


def make_dark_material():
    mat = bpy.data.materials.new("SnakeDark")
    mat.use_nodes = True
    bsdf = _principled(mat)
    _inp(bsdf, "Base Color").default_value = (0.012, 0.016, 0.018, 1.0)
    _inp(bsdf, "Metallic").default_value = 0.2
    _inp(bsdf, "Roughness").default_value = 0.6
    return mat


MATS = {}


def mats():
    if not MATS:
        MATS["plate"] = make_plate_material("SnakePlate")
        MATS["plate_dark"] = make_plate_material(
            "SnakePlateDark", tint=(0.45, 0.5, 0.55))
        MATS["belly"] = make_belly_material()
        MATS["eye"] = make_eye_material()
        MATS["dark"] = make_dark_material()
        MATS["glow"] = make_glow_material()
        MATS["eye_core"] = make_eye_core_material()
        MATS["panel"] = make_panel_material()
    return MATS


def _torus(name, x, major, minor, z_scale, mat, z=0.0):
    bpy.ops.mesh.primitive_torus_add(
        major_segments=12, minor_segments=6,
        major_radius=major, minor_radius=minor, location=(x, 0.0, z))
    t = bpy.context.object
    t.name = name
    t.rotation_euler = (0.0, math.radians(90.0), 0.0)
    # Local X maps to world Z after the Y-rotation, so squash local X
    # to match the segment's elliptical cross-section.
    t.scale = (z_scale, 1.0, 1.0)
    t.data.materials.append(mat)
    return t


def glow_ring(name, x, major, minor, z_scale=0.9, z=0.0):
    """Emissive band seated in a segment pinch groove (axis along +X).

    Exercise 2 (fix #4): the bare torus read as a pasted-on flat band.
    The emissive core is now slimmer and recessed below the surface,
    flanked by two dark housing rims that sit proud — a light in a
    machined channel. Returns [glow, housing, housing]."""
    glow = _torus(name, x, major, minor * 0.86, z_scale, mats()["glow"], z)
    parts = [glow]
    for s in (-1.0, 1.0):
        parts.append(_torus(name + "Housing", x + s * minor * 1.30,
                            major, minor * 1.30, z_scale, mats()["dark"], z))
    return parts

# ---------------------------------------------------------------- loft core

def _section_point(wr, hr, theta, zoff, flatten_top):
    """One cross-section point. theta=0 is the belly centerline, pi the
    dorsal centerline. Returns (y, z) in the ring plane."""
    y = wr * math.sin(theta)
    z = -hr * math.cos(theta)
    belly_z = -hr * 0.72
    if z < belly_z:  # flattened belly so the snake sits on the floor
        z = belly_z + (z - belly_z) * 0.30
    if z > 0.0:  # low dorsal ridge along the top centerline
        z += 0.030 * math.exp(-((y / 0.13) ** 2)) * (z / hr)
    if flatten_top and z > hr * 0.55:  # cranium plate: flatten the skull top
        over = z - hr * 0.55
        z = hr * 0.55 + over * 0.72
    return y, z + zoff


def loft(name, rings, radial=24, flatten_top=False, displace=None,
         default_mat=0, subdiv=2):
    """rings: list of (x, width_radius, height_radius, z_offset).
    Returns a Mesh object with analytic UVs and two material slots
    (0 = default/plate, 1 = belly). `displace(t, theta, Vector)` may
    reshape vertices; t is x normalized by total length."""
    total_len = rings[-1][0] - rings[0][0] or 1.0
    verts, faces, face_mat = [], [], []
    ring_start = []
    for (x, wr, hr, zoff) in rings:
        ring_start.append(len(verts))
        for i in range(radial):
            theta = 2.0 * math.pi * i / radial
            y, z = _section_point(wr, hr, theta, zoff, flatten_top)
            p = [x, y, z]
            if displace:
                t = (x - rings[0][0]) / total_len
                p = list(displace(t, theta, p))
            verts.append(tuple(p))
    for r in range(len(rings) - 1):
        a0, b0 = ring_start[r], ring_start[r + 1]
        for i in range(radial):
            j = (i + 1) % radial
            quad = (a0 + i, b0 + i, b0 + j, a0 + j)
            faces.append(quad)
            th = 2.0 * math.pi * (i + 0.5) / radial
            belly = min(th, 2.0 * math.pi - th) < BELLY_HALF
            face_mat.append(1 if belly else default_mat)
    # End caps: slightly domed center points + triangle fans.
    for end, (x, wr, hr, zoff) in ((0, rings[0]), (1, rings[-1])):
        cx = x + (-0.07 if end == 0 else 0.07)
        ci = len(verts)
        verts.append((cx, 0.0, zoff))
        start = ring_start[0] if end == 0 else ring_start[-1]
        for i in range(radial):
            j = (i + 1) % radial
            faces.append((ci, start + j, start + i) if end == 0
                         else (ci, start + i, start + j))
            face_mat.append(default_mat)

    mesh = bpy.data.meshes.new(name)
    # UVs first (from_pydata clears nothing, but build them explicitly).
    uvs = []
    for vi, (x, y, z) in enumerate(verts):
        ring_i = min(vi // radial, len(rings) - 1) if vi < radial * len(rings) else -1
        if ring_i >= 0:
            i = vi % radial
            theta = 2.0 * math.pi * i / radial
            uvs.append((x / TILE, theta / (2.0 * math.pi) * 2.0))
        else:
            uvs.append((x / TILE, 1.0))
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(mats()["plate"] if default_mat == 0 else mats()["plate_dark"])
    mesh.materials.append(mats()["belly"])
    for poly, m in zip(mesh.polygons, face_mat):
        poly.material_index = m
        poly.use_smooth = True
    uv_layer = mesh.uv_layers.new(name="UVMap")
    for loop in mesh.loops:
        uv_layer.data[loop.index].uv = uvs[loop.vertex_index]
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    # Subdivision: the manufactured bevel read comes from here.
    mod = obj.modifiers.new("Subsurf", "SUBSURF")
    mod.levels = subdiv
    mod.render_levels = subdiv
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    if subdiv:
        bpy.ops.object.modifier_apply(modifier=mod.name)
    else:
        obj.modifiers.remove(mod)
    obj.select_set(False)
    return obj

# ---------------------------------------------------------------- head

HEAD_LEN = 1.70
HEAD_RINGS = [
    (0.00, 0.44, 0.40, 0.00),
    (0.17, 0.50, 0.44, 0.01),
    (0.48, 0.55, 0.48, 0.02),
    (0.77, 0.58, 0.51, 0.03),
    (0.99, 0.56, 0.50, 0.03),
    (1.22, 0.50, 0.45, 0.02),
    (1.46, 0.42, 0.39, 0.005),
    (1.62, 0.33, 0.32, -0.005),
    (1.70, 0.20, 0.22, -0.01),
]


def _angdiff(a, b):
    d = (a - b) % (2.0 * math.pi)
    return d - 2.0 * math.pi if d > math.pi else d


def head_displace(t, theta, p):
    x, y, z = p
    for side_theta in (2.0, 2.0 * math.pi - 2.0):
        dth = _angdiff(theta, side_theta)
        # Brow ridge: raised plate over each eye, strong enough to break
        # the silhouette and throw a shadow line over the socket.
        g = math.exp(-(((t - 0.57) / 0.075) ** 2)) * math.exp(-((dth / 0.40) ** 2))
        radial = 0.115 * g
        y += math.sin(theta) * radial
        z += -math.cos(theta) * radial + 0.034 * g
        # Eye socket: a real dip under the brow so the eye sits IN the head.
        g2 = math.exp(-(((t - 0.60) / 0.055) ** 2)) * math.exp(-(((dth - 0.22) / 0.30) ** 2))
        y -= math.sin(theta) * 0.045 * g2
        z -= -math.cos(theta) * 0.045 * g2
    return (x, y, z)


def build_head():
    head = loft("SnakeHead", HEAD_RINGS, radial=18, flatten_top=True,
                displace=head_displace, subdiv=2)
    # Jaw: darker plate loft hugging the head's underside.
    jaw_rings = []
    for (x, wr, hr, zoff) in HEAD_RINGS:
        if x < 0.12 or x > 1.64:
            continue
        belly_z = zoff - hr * 0.72
        jaw_rings.append((x, wr * 0.86, 0.085, belly_z - 0.048))
    # Chin: one extra ring carries the jaw past the snout's underside so
    # the jaw line breaks the silhouette instead of ending flush.
    lx, lwr, lhr, lz = jaw_rings[-1]
    jaw_rings.append((1.76, lwr * 0.94, lhr, lz - 0.012))
    jaw = loft("SnakeJaw", jaw_rings, radial=14, default_mat=0, subdiv=2)
    jaw.data.materials[0] = mats()["plate_dark"]
    ring = glow_ring("SnakeHeadRing", 0.12, 0.465, 0.028, z=0.005)
    # ring is now [glow, housing, housing] (Exercise 2).
    # Dorsal crest: four beveled plates along the skull top — the head's
    # silhouette signature from any high angle.
    crest = []
    for cx, ch in ((0.30, 0.09), (0.58, 0.115), (0.86, 0.11), (1.14, 0.085)):
        top = max(r[2] + r[3] for r in HEAD_RINGS if abs(r[0] - cx) < 0.3)
        bpy.ops.mesh.primitive_cube_add(location=(cx, 0.0, top * 0.93 - 0.01))
        plate = bpy.context.object
        plate.name = "SnakeCrest"
        plate.scale = (0.030, 0.130, ch)
        plate.rotation_euler = (0.0, -0.38, 0.0)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        bev = plate.modifiers.new("Bevel", "BEVEL")
        bev.width = 0.014
        bev.segments = 2
        bpy.context.view_layer.objects.active = plate
        bpy.ops.object.modifier_apply(modifier=bev.name)
        plate.data.materials.append(mats()["belly"])
        crest.append(plate)
    # Camera-eye assembly: dark recessed optical glass behind a raised bezel,
    # with six individually modeled iris blades around a central aperture.
    eyes = []
    for sign in (1.0,):
        n = Vector((0.0, sign * 0.909, 0.416)).normalized()
        xa = Vector((1.0, 0.0, 0.0)).cross(n).normalized()
        ya = n.cross(xa).normalized()
        socket = Vector((1.00, sign * 0.528, 0.2659))
        lens_center = socket - n * 0.112
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=32, ring_count=20, radius=0.092, location=lens_center)
        eye = bpy.context.object
        eye.name = "SnakeEyeRecessedOpticalGlass"
        eye.scale = (1.30, 0.66, 0.88)
        eye.rotation_euler = (0.0, 0.0, sign * -0.18)
        eye.data.materials.append(mats()["eye"]); eyes.append(eye)
        bpy.ops.mesh.primitive_torus_add(
            major_segments=32, minor_segments=10, major_radius=0.100,
            minor_radius=0.027, location=socket)
        bezel = bpy.context.object; bezel.name = "SnakeEyeBezelHousing"
        bezel.matrix_world = Matrix(((xa.x,ya.x,n.x,bezel.location.x),
            (xa.y,ya.y,n.y,bezel.location.y),(xa.z,ya.z,n.z,bezel.location.z),
            (0.0,0.0,0.0,1.0)))
        bezel.data.materials.append(mats()["dark"]); eyes.append(bezel)
        optical = socket + n * 0.002
        bpy.ops.mesh.primitive_torus_add(major_segments=32, minor_segments=8,
            major_radius=0.073, minor_radius=0.006, location=optical)
        retainer = bpy.context.object; retainer.name = "SnakeEyeOpticalRetainer"
        retainer.matrix_world = Matrix(((xa.x,ya.x,n.x,retainer.location.x),
            (xa.y,ya.y,n.y,retainer.location.y),(xa.z,ya.z,n.z,retainer.location.z),
            (0.0,0.0,0.0,1.0)))
        retainer.data.materials.append(mats()["glow"]); eyes.append(retainer)
        # Six solid swept iris vanes overlap slightly, leaving a small hexagonal
        # aperture. Every vane is actual closed mesh geometry, not a texture.
        for i in range(6):
            ang = 2.0 * math.pi * i / 6.0
            span = math.radians(43.0)
            pts = []
            for radius, theta in ((0.024,ang-span/2),(0.064,ang+span/2),
                                  (0.064,ang+span/2+0.20),(0.027,ang-span/2+0.20)):
                pts.append(optical + (xa*math.cos(theta)+ya*math.sin(theta))*radius + n*0.008)
            verts = [tuple(q - n*0.003) for q in pts] + [tuple(q + n*0.003) for q in pts]
            faces = [(0,1,2,3),(7,6,5,4)]
            for j in range(4): faces.append((j,(j+1)%4,(j+1)%4+4,j+4))
            mesh = bpy.data.meshes.new("IrisVaneMesh"); mesh.from_pydata(verts,[],faces); mesh.update()
            vane = bpy.data.objects.new("SnakeEyeIrisBlade_%02d" % (i+1),mesh)
            bpy.context.collection.objects.link(vane); vane.data.materials.append(mats()["panel"] if i%2==0 else mats()["dark"])
            eyes.append(vane)
        # A recessed dark aperture is framed by a thin illuminated sensor ring.
        pupil_pos = socket + n * 0.014
        bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12,
            radius=0.023, location=pupil_pos)
        pupil=bpy.context.object; pupil.name="SnakeEyeAperture"
        pupil.scale=(1.0,0.35,1.0); pupil.data.materials.append(mats()["dark"]); eyes.append(pupil)
        bpy.ops.mesh.primitive_torus_add(major_segments=24,minor_segments=6,
            major_radius=0.015,minor_radius=0.003,location=socket+n*0.023)
        sensor=bpy.context.object; sensor.name="SnakeEyeSensorRing"
        sensor.matrix_world=Matrix(((xa.x,ya.x,n.x,sensor.location.x),
            (xa.y,ya.y,n.y,sensor.location.y),(xa.z,ya.z,n.z,sensor.location.z),
            (0.0,0.0,0.0,1.0)))
        sensor.data.materials.append(mats()["glow"]); eyes.append(sensor)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=10,
            radius=0.008,location=socket+n*0.026)
        core=bpy.context.object; core.name="SnakeEyeSensorCore"
        core.scale=(1.0,0.4,1.0); core.data.materials.append(mats()["eye_core"]); eyes.append(core)
    # Nostrils: small dark dimples on the snout top.
    for sign in (-1.0, 1.0):
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=0.021, location=(1.545, sign * 0.105, 0.325))
        n = bpy.context.object
        n.name = "SnakeNostril"
        n.scale = (1.4, 0.8, 0.55)
        n.data.materials.append(mats()["dark"])
        eyes.append(n)
    return [head, jaw] + ring + crest + eyes

# ---------------------------------------------------------------- segment

SEG_RINGS = [
    (-0.60, 0.416, 0.368, 0.0),
    (-0.565, 0.489, 0.432, 0.0),
    (-0.42, 0.520, 0.460, 0.0),
    (0.00, 0.536, 0.474, 0.0),
    (0.42, 0.520, 0.460, 0.0),
    (0.565, 0.489, 0.432, 0.0),
    (0.60, 0.416, 0.368, 0.0),
]


def build_segment():
    seg = loft("SnakeSegment", SEG_RINGS, radial=16, subdiv=0)
    ring = glow_ring("SnakeSegRing", -0.50, 0.472, 0.030)
    details = []
    def beveled_box(name, loc, dims, material, bevel):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
        obj = bpy.context.object
        obj.name = name
        obj.scale = dims
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        mod = obj.modifiers.new("MachinedEdge", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
        obj.data.materials.append(material)
        details.append(obj)
        return obj
    # Raised dorsal cover, paired cheek guards, and recessed-looking vent slots.
    panel = mats()["panel"]
    dark = mats()["dark"]
    for loc, dims in [((0.0, 0.0, 0.460), (0.78, 0.58, 0.060)),
                      ((0.0, -0.465, 0.035), (1.02, 0.075, 0.36)),
                      ((0.0, 0.465, 0.035), (1.02, 0.075, 0.36))]:
        beveled_box("SnakeSegmentArmor", loc, dims, panel, 0.035)
    for x in (-0.18, -0.06, 0.06, 0.18):
        beveled_box("SnakeSegmentVent", (x, 0.0, 0.497), (0.035, 0.34, 0.018), dark, 0.008)
    # Two low-profile circular fasteners per cheek (both flanks get a pair).
    for side in (-1.0, 1.0):
        for x in (-0.25, 0.25):
            bpy.ops.mesh.primitive_uv_sphere_add(
                segments=6, ring_count=4, radius=0.035,
                location=(x, side * 0.515, 0.12))
            bolt = bpy.context.object
            bolt.name = "SnakeSegmentFastener"
            bolt.scale = (1.0, 0.38, 1.0)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            bolt.data.materials.append(panel)
            details.append(bolt)
    return [seg] + ring + details

# ---------------------------------------------------------------- export

def reset_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.curves):
        pass  # keep materials cached in MATS


def export_glb(objects, filename):
    bpy.ops.object.select_all(action="DESELECT")
    saved = {o: o.matrix_world.copy() for o in objects}
    # Source geometry is authored along Blender +X for an easy path build.
    # Export-only -90° Z rotation aligns its front to Blender -Y, which the
    # +Y-up glTF conversion maps to Godot's model-front +Z.
    axis_fix = Matrix.Rotation(math.radians(-90.0), 4, "Z")
    for o in objects:
        o.select_set(True)
        o.matrix_world = axis_fix @ o.matrix_world
    bpy.ops.export_scene.gltf(
        filepath=os.path.join(HERE, filename),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_materials="EXPORT",
        export_tangents=True,
    )
    for o, matrix in saved.items():
        o.matrix_world = matrix
    print("EXPORTED", filename)


def place(obj, pos, yaw_deg=0.0, pitch_deg=0.0):
    """Move a built part onto the spine, COMPOSING the part transform
    with each object's own local transform.

    Exercise 1 overwrote location/rotation outright, which was fine
    for the lofts (their shape lives in the vertices, origin at zero)
    but destroyed every primitive-built part whose offset lives in
    its object transform: in the posed full snake the eyes, bezels
    and crest plates collapsed into the head's center (buried,
    invisible) and the segment glow rings sat inside the segment
    barrels instead of in their pinch grooves. The Exercise 2 review
    staging exposed this; composing the matrices fixes the assembly
    without touching any part's own geometry."""
    rot = Euler((0.0, math.radians(pitch_deg), math.radians(yaw_deg)))
    part_m = Matrix.Translation(Vector(pos)) @ rot.to_matrix().to_4x4()
    obj.matrix_world = part_m @ obj.matrix_world


def tail_parts():
    # Tapered rigid tail cap. Local +X is toward the head; its tip extends -X.
    rings = [(-0.82, 0.045, 0.050, 0.0), (-0.68, 0.13, 0.12, 0.0),
             (-0.42, 0.23, 0.21, 0.0), (-0.10, 0.31, 0.28, 0.0),
             (0.22, 0.38, 0.34, 0.0), (0.58, 0.43, 0.38, 0.0)]
    body = loft("SnakeTail", rings, radial=16, subdiv=1)
    ring = glow_ring("SnakeTailRing", 0.42, 0.39, 0.022, z_scale=0.9)
    fins = []
    for side in (-1.0, 1.0):
        bpy.ops.mesh.primitive_cube_add(location=(-0.57, side * 0.105, 0.12))
        fin = bpy.context.object
        fin.name = "SnakeTailFin"
        fin.scale = (0.24, 0.035, 0.16)
        fin.rotation_euler[1] = math.radians(-22.0)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        bevel = fin.modifiers.new("TailFinBevel", "BEVEL")
        bevel.width = 0.025
        bevel.segments = 2
        bpy.context.view_layer.objects.active = fin
        bpy.ops.object.modifier_apply(modifier=bevel.name)
        fin.data.materials.append(mats()["plate_dark"])
        fins.append(fin)
    return [body] + ring + fins


def main():
    mats()
    reset_scene()
    export_glb(build_segment(), "snake_segment.glb")
    reset_scene()
    export_glb(build_head(), "snake_head.glb")

    # Full rigid instance chain. Each segment object is centered on its cell
    # pivot; local +X points toward the head. Sample a broad, raised S-curve.
    reset_scene()
    head_parts = build_head()
    head_pos = Vector((-5.00, 2.40, 1.12))
    head_yaw = 180.0
    for o in head_parts:
        o["review_head"] = True
        place(o, head_pos, yaw_deg=head_yaw, pitch_deg=-8.0)
    full = list(head_parts)
    path = [
        (-4.45, 2.00, .78), (-3.30, 1.65, .43), (-2.40, .70, .34),
        (-2.10, -.50, .34), (-2.90, -1.50, .34), (-4.20, -1.90, .34),
        (-5.40, -1.50, .34), (-6.00, -.30, .34), (-5.80, .90, .34),
        (-4.80, 1.90, .34), (-3.50, 2.30, .34), (-2.30, 1.90, .34),
        (-1.40, 1.00, .34), (-.70, -.10, .34), (.10, -1.00, .34),
        (1.30, -1.40, .34), (2.60, -1.20, .30), (3.80, -.50, .25),
        (4.80, .50, .20), (5.20, 1.70, .16),
    ]
    path = [(x, y * 1.25, z) for x, y, z in path]
    # Even 1.00 m rigid-cell spacing follows the hand-shaped S path while
    # preserving overlap through tight turns and avoiding axial gaps.
    control = [Vector(p) for p in path]
    body = [control[0]]
    carry = 1.00
    for a, b in zip(control, control[1:]):
        delta = b - a
        length = delta.length
        if length < 1e-6:
            continue
        cursor = carry
        while cursor <= length:
            body.append(a + delta * (cursor / length))
            cursor += 1.00
        carry = cursor - length
    centers = [head_pos] + body
    for i, pos in enumerate(centers[1:-1], start=1):
        toward_head = centers[i-1] - centers[i+1]
        yaw = math.degrees(math.atan2(toward_head.y, toward_head.x))
        taper = 1.0 if i < 11 else max(.52, 1.0 - (i-10) * .065)
        parts = build_segment()
        for part in parts:
            part.scale = (1.0, taper, taper)
            place(part, pos, yaw_deg=yaw)
            full.append(part)
    tail_pos = centers[-1]
    toward_head = centers[-2] - centers[-1]
    tail_yaw = math.degrees(math.atan2(toward_head.y, toward_head.x))
    for part in tail_parts():
        place(part, tail_pos, yaw_deg=tail_yaw)
        full.append(part)
    export_glb(full, "snake_full.glb")
    for image in bpy.data.images:
        if image.source == "FILE" and not image.packed_file:
            image.pack()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "snake.blend"))
    print("BUILD_DONE", len(full), "objects")


if __name__ == "__main__":
    main()
