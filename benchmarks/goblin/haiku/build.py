"""Procedural goblin hero render for Blender 4.5 (headless).

Run:  blender -b --factory-startup -P build.py -- [render.png] [samples]
Defaults: render.png next to this script, 256 samples.
"""
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT_PATH = ARGS[0] if len(ARGS) > 0 else os.path.join(HERE, "render.png")
SAMPLES = int(ARGS[1]) if len(ARGS) > 1 else 256

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
COLL = scene.collection


def link(obj):
    COLL.objects.link(obj)
    return obj


def make_material(name, base, rough=0.5, metal=0.0, spec=0.5, sss=0.0,
                  sss_radius=(1.0, 0.5, 0.25), var=None, bump=0.0,
                  noise_scale=40.0, coat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nodes, links = nt.nodes, nt.links
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Metallic"].default_value = metal
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Specular IOR Level"].default_value = spec
    bsdf.inputs["Subsurface Weight"].default_value = sss
    bsdf.inputs["Subsurface Radius"].default_value = sss_radius
    bsdf.inputs["Subsurface Scale"].default_value = 0.01
    bsdf.inputs["Coat Weight"].default_value = coat
    bsdf.inputs["Base Color"].default_value = (*base, 1.0)
    if var or bump:
        tc = nodes.new("ShaderNodeTexCoord")
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = noise_scale
        noise.inputs["Detail"].default_value = 8.0
        noise.inputs["Roughness"].default_value = 0.6
        links.new(tc.outputs["Object"], noise.inputs["Vector"])
        if var:
            ramp = nodes.new("ShaderNodeValToRGB")
            ramp.color_ramp.elements[0].position = 0.35
            ramp.color_ramp.elements[0].color = (*var[0], 1.0)
            ramp.color_ramp.elements[1].position = 0.65
            ramp.color_ramp.elements[1].color = (*var[1], 1.0)
            links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
            links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
        if bump:
            bmp = nodes.new("ShaderNodeBump")
            bmp.inputs["Strength"].default_value = bump
            bmp.inputs["Distance"].default_value = 0.01
            links.new(noise.outputs["Fac"], bmp.inputs["Height"])
            links.new(bmp.outputs["Normal"], bsdf.inputs["Normal"])
    return m


SKIN = make_material("goblin_skin", (0.09, 0.2, 0.05), rough=0.45, sss=0.15,
                     sss_radius=(0.9, 0.45, 0.2),
                     var=((0.07, 0.16, 0.035), (0.13, 0.27, 0.06)),
                     bump=0.06, noise_scale=55.0)
EYE_WHITE = make_material("eye_white", (0.9, 0.75, 0.12), rough=0.12, coat=0.3)
IRIS = make_material("iris", (0.85, 0.35, 0.02), rough=0.3)
PUPIL = make_material("pupil", (0.005, 0.005, 0.005), rough=0.2)
IVORY = make_material("ivory", (0.85, 0.8, 0.62), rough=0.35)
CLAW = make_material("claw", (0.16, 0.14, 0.1), rough=0.35)
MOUTH = make_material("mouth", (0.1, 0.02, 0.02), rough=0.4)
LEATHER = make_material("leather", (0.13, 0.07, 0.035), rough=0.55,
                        var=((0.08, 0.04, 0.02), (0.2, 0.12, 0.06)),
                        bump=0.1, noise_scale=30.0)
CLOTH = make_material("cloth", (0.24, 0.17, 0.1), rough=0.85,
                      var=((0.16, 0.11, 0.06), (0.32, 0.24, 0.15)),
                      bump=0.05, noise_scale=20.0)
METAL = make_material("steel", (0.62, 0.62, 0.64), metal=1.0, rough=0.28)
BLADE = make_material("blade", (0.07, 0.07, 0.08), metal=1.0, rough=0.35)
WALL = make_material("studio_gray", (0.18, 0.18, 0.18), rough=0.9, spec=0.2)


class Graph:
    def __init__(self):
        self.nodes = []
        self.edges = []

    def add(self, spec):
        self.nodes.append(spec)
        return len(self.nodes) - 1

    def chain(self, specs):
        ids = [self.add(s) for s in specs]
        self.edges += list(zip(ids, ids[1:]))
        return ids

    def link(self, a, b):
        self.edges.append((a, b))


def N(x, y, z, r, ry=None):
    return ((x, y, z), r, r if ry is None else ry)


def bake(obj, material):
    """Evaluate modifiers into a plain smooth mesh so the render is stable."""
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = bpy.data.meshes.new_from_object(evaluated)
    old = obj.data
    obj.modifiers.clear()
    obj.data = mesh
    bpy.data.meshes.remove(old)
    if not mesh.materials:
        mesh.materials.append(material)
    mesh.shade_smooth()
    return obj


def skin_mesh(name, graph, material, roots, levels=2):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    layer = bm.verts.layers.skin.verify()
    verts = []
    for i, (pos, rx, ry) in enumerate(graph.nodes):
        v = bm.verts.new(pos)
        v[layer].radius = (rx, ry)
        v[layer].use_root = i in roots
        verts.append(v)
    for a, b in graph.edges:
        bm.edges.new((verts[a], verts[b]))
    bm.to_mesh(me)
    bm.free()
    obj = link(bpy.data.objects.new(name, me))
    obj.data.materials.append(material)
    obj.modifiers.new("Skin", "SKIN")
    sub = obj.modifiers.new("Subdivision", "SUBSURF")
    sub.levels = levels
    sub.render_levels = levels
    return bake(obj, material)


def mesh_from_bm(name, bm, material, smooth=True):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = link(bpy.data.objects.new(name, me))
    obj.data.materials.append(material)
    if smooth:
        me.shade_smooth()
    return obj


def ellipsoid(name, loc, scale, material, subdiv=3):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0)
    obj = mesh_from_bm(name, bm, material)
    obj.location = loc
    obj.scale = scale
    return obj


def tube(name, a, b, r0, r1, material, segs=10):
    a, b = Vector(a), Vector(b)
    d = b - a
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs,
                          radius1=r0, radius2=r1, depth=d.length)
    obj = mesh_from_bm(name, bm, material)
    obj.location = (a + b) / 2
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    return obj


def blade(name, top, bottom, w, t, material):
    bm = bmesh.new()
    top, bottom = Vector(top), Vector(bottom)
    corners = [top + Vector((sx * w / 2, sy * t / 2, 0.0))
               for sx in (-1, 1) for sy in (-1, 1)]
    bv = [bm.verts.new(p) for p in corners]
    tip = bm.verts.new(bottom)
    bm.faces.new((bv[0], bv[2], bv[3], bv[1]))
    for a, b in ((0, 1), (1, 3), (3, 2), (2, 0)):
        bm.faces.new((bv[a], bv[b], tip))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    return mesh_from_bm(name, bm, material, smooth=False)


# Head: unit sphere displaced by Gaussian bumps (front is -Y), then scaled.
HEAD_CENTER = (0.0, 0.0, 1.20)
HEAD_SCALE = (0.115, 0.125, 0.13)
HEAD_BUMPS = [
    ((0.0, -0.93, 0.14), 0.42, 0.11),     # nose bridge
    ((0.0, -0.98, -0.08), 0.34, 0.10),    # nose bulb
    ((0.0, -0.90, -0.26), 0.20, 0.09),    # nose hook underside
    ((0.0, -0.80, 0.44), 0.16, 0.26),     # brow ridge
    ((-0.40, -0.80, 0.22), -0.10, 0.18),  # eye socket L
    ((0.40, -0.80, 0.22), -0.10, 0.18),   # eye socket R
    ((-0.55, -0.66, -0.12), 0.08, 0.24),  # cheekbone L
    ((0.55, -0.66, -0.12), 0.08, 0.24),   # cheekbone R
    ((0.0, -0.74, -0.80), 0.12, 0.22),    # chin
    ((0.0, -0.40, 0.98), 0.05, 0.40),     # cranium
]


def make_head():
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=5, radius=1.0)
    for v in bm.verts:
        n = v.co.normalized()
        p = v.co.copy()
        if p.z < -0.2:
            p.x *= 1.0 - 0.22 * min(1.0, (-0.2 - p.z) / 0.8)
        push = 0.0
        for c, amp, sig in HEAD_BUMPS:
            push += amp * math.exp(-(p - Vector(c)).length_squared / (2 * sig * sig))
        v.co = p + n * push
    obj = mesh_from_bm("goblin_head", bm, SKIN)
    obj.location = HEAD_CENTER
    obj.scale = HEAD_SCALE
    return obj


def make_body():
    g = Graph()
    pelvis, waist, belly, chest, upper, neck_b, neck_t = g.chain([
        N(0, 0, 0.66, 0.128, 0.10),
        N(0, 0, 0.76, 0.098, 0.088),
        N(0, -0.015, 0.84, 0.118, 0.10),
        N(0, 0, 0.92, 0.15, 0.11),
        N(0, 0, 0.99, 0.13, 0.10),
        N(0, 0.005, 1.04, 0.065, 0.06),
        N(0, 0.01, 1.10, 0.06, 0.058),
    ])

    # Hero arm: hand on hip (+X side).
    sh_l = g.add(N(0.165, 0.0, 0.97, 0.068, 0.062))
    el_l = g.add(N(0.235, -0.03, 0.80, 0.05, 0.046))
    wr_l = g.add(N(0.165, -0.05, 0.69, 0.034, 0.028))
    g.link(upper, sh_l)
    g.link(sh_l, el_l)
    g.link(el_l, wr_l)
    palm_l = g.add(N(0.165, -0.06, 0.67, 0.03, 0.022))
    g.link(wr_l, palm_l)
    thumb_l = g.chain([N(0.190, -0.085, 0.69, 0.014), N(0.195, -0.108, 0.675, 0.009)])
    g.link(palm_l, thumb_l[0])
    for i in range(4):
        z = 0.655 - 0.012 * i
        f = g.chain([N(0.172, -0.088, z, 0.011, 0.011), N(0.170, -0.108, z - 0.012, 0.0075)])
        g.link(palm_l, f[0])

    # Dagger arm (-X side), hanging, fist around the grip.
    sh_r = g.add(N(-0.165, 0.0, 0.97, 0.068, 0.062))
    el_r = g.add(N(-0.225, -0.03, 0.78, 0.05, 0.046))
    wr_r = g.add(N(-0.228, -0.035, 0.57, 0.034, 0.028))
    palm_r = g.add(N(-0.232, -0.04, 0.535, 0.032, 0.024))
    g.link(upper, sh_r)
    g.link(sh_r, el_r)
    g.link(el_r, wr_r)
    g.link(wr_r, palm_r)
    thumb_r = g.chain([N(-0.255, -0.045, 0.545, 0.011), N(-0.262, -0.06, 0.52, 0.009)])
    g.link(palm_r, thumb_r[0])
    for i in range(4):
        z = 0.530 - 0.011 * i
        f = g.chain([N(-0.252, -0.062, z, 0.011), N(-0.250, -0.080, z - 0.006, 0.008)])
        g.link(palm_r, f[0])

    for s in (1, -1):
        yk = -0.02 if s == 1 else -0.06
        hip = g.add(N(s * 0.095, 0.0, 0.64, 0.10, 0.095))
        knee = g.add(N(s * 0.105, yk, 0.36, 0.075, 0.068))
        ankle = g.add(N(s * 0.10, 0.0, 0.08, 0.05, 0.045))
        toe = g.chain([N(s * 0.10, -0.06, 0.05, 0.05, 0.035),
                       N(s * 0.10, -0.13, 0.04, 0.04, 0.026)])
        g.link(pelvis, hip)
        g.link(hip, knee)
        g.link(knee, ankle)
        g.link(ankle, toe[0])

    return skin_mesh("goblin_body", g, SKIN, roots=[pelvis])


def make_boots():
    g = Graph()
    roots = []
    for s in (1, -1):
        ids = g.chain([
            N(s * 0.105, 0.0, 0.20, 0.070, 0.068),
            N(s * 0.10, 0.0, 0.09, 0.058, 0.055),
            N(s * 0.10, -0.07, 0.05, 0.066, 0.058),
            N(s * 0.10, -0.16, 0.045, 0.054, 0.04),
        ])
        roots.append(ids[0])
    return skin_mesh("goblin_boots", g, LEATHER, roots=roots)


def make_ears():
    g = Graph()
    roots = []
    for s in (1, -1):
        ids = g.chain([
            N(s * 0.10, 0.005, 1.205, 0.030, 0.040),
            N(s * 0.17, 0.025, 1.245, 0.022, 0.020),
            N(s * 0.255, 0.040, 1.275, 0.004, 0.006),
        ])
        roots.append(ids[0])
    return skin_mesh("goblin_ears", g, SKIN, roots=roots)


def make_loincloth():
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=14, y_segments=10, size=1.0)
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    for v in bm.verts:
        u = (v.co.x - x0) / (x1 - x0)
        w = (v.co.y - y0) / (y1 - y0)
        x = (u - 0.5) * 0.19
        z = 0.735 - w * (0.25 + 0.03 * abs(math.sin(u * math.pi * 4)))
        y = -0.112 - 0.010 * math.sin(u * math.pi * 3) * (0.4 + w) - 0.004 * w
        v.co = Vector((x, y, z))
    obj = mesh_from_bm("goblin_loincloth", bm, CLOTH, smooth=False)
    sol = obj.modifiers.new("Solidify", "SOLIDIFY")
    sol.thickness = 0.006
    sub = obj.modifiers.new("Subdivision", "SUBSURF")
    sub.levels = 2
    sub.render_levels = 2
    return bake(obj, CLOTH)


def make_dagger():
    gx, gy = -0.237, -0.045
    tube("dagger_grip", (gx, gy, 0.55), (gx, gy, 0.488), 0.0105, 0.0105, LEATHER, segs=12)
    ellipsoid("dagger_pommel", (gx, gy, 0.555), (0.011, 0.011, 0.011), METAL, subdiv=2)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(gx, gy, 0.484))
    guard = bpy.context.active_object
    guard.name = "dagger_guard"
    guard.scale = (0.04, 0.012, 0.009)
    guard.data.materials.append(METAL)
    blade("dagger_blade", (gx, gy, 0.478), (gx - 0.003, gy - 0.005, 0.27), 0.034, 0.008, BLADE)


def make_belt():
    bpy.ops.mesh.primitive_torus_add(major_radius=0.122, minor_radius=0.017,
                                     major_segments=64, minor_segments=16,
                                     location=(0, 0, 0.745))
    belt = bpy.context.active_object
    belt.name = "belt"
    belt.scale = (1.0, 0.86, 1.0)
    belt.data.materials.append(LEATHER)
    belt.data.shade_smooth()

    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.106, 0.745))
    buckle = bpy.context.active_object
    buckle.name = "buckle"
    buckle.scale = (0.024, 0.006, 0.02)
    buckle.data.materials.append(METAL)

    bpy.ops.mesh.primitive_cube_add(size=1, location=(0.12, -0.035, 0.71))
    pouch = bpy.context.active_object
    pouch.name = "pouch"
    pouch.scale = (0.045, 0.028, 0.04)
    pouch.data.materials.append(LEATHER)
    bev = pouch.modifiers.new("Bevel", "BEVEL")
    bev.width = 0.008
    bev.segments = 3
    pouch.data.shade_smooth()


def make_head_details():
    for s in (1, -1):
        x = s * 0.046
        ellipsoid(f"eye_white_{s}", (x, -0.100, 1.228), (0.031, 0.028, 0.031), EYE_WHITE)
        ellipsoid(f"iris_{s}", (x, -0.124, 1.228), (0.017, 0.010, 0.017), IRIS)
        ellipsoid(f"pupil_{s}", (x, -0.131, 1.228), (0.005, 0.006, 0.014), PUPIL)
        tube(f"fang_{s}", (s * 0.030, -0.108, 1.115), (s * 0.028, -0.113, 1.145),
             0.0085, 0.0008, IVORY, segs=8)
    ellipsoid("mouth", (0.0, -0.104, 1.13), (0.05, 0.006, 0.006), MOUTH)


def make_claws():
    tips = [((0.170, -0.108, 0.655 - 0.012 * i - 0.012), (0.0, -1.0, -0.3)) for i in range(4)]
    for i, (tip, d) in enumerate(tips):
        tip = Vector(tip)
        tube(f"claw_{i}", tip, tip + Vector(d).normalized() * 0.022, 0.0065, 0.0008, CLAW, segs=6)


def make_cyc():
    prof = [(-9.0 + 10.0 * i / 23, 0.0) for i in range(24)]
    for i in range(1, 13):
        t = -math.pi / 2 + (math.pi / 2) * i / 12
        prof.append((1.0 + 2.5 * math.cos(t), 2.5 + 2.5 * math.sin(t)))
    for z in (4.0, 6.0, 9.0):
        prof.append((3.5, z))
    bm = bmesh.new()
    rows = [[bm.verts.new((x, y, z)) for x in (-12.0, 12.0)] for (y, z) in prof]
    for a, b in zip(rows, rows[1:]):
        bm.faces.new((a[0], a[1], b[1], b[0]))
    return mesh_from_bm("studio_cyc", bm, WALL)


def add_area_light(name, loc, target, watts, size, color):
    ld = bpy.data.lights.new(name, "AREA")
    ld.energy = watts
    ld.size = size
    ld.color = color
    ob = link(bpy.data.objects.new(name, ld))
    ob.location = loc
    d = Vector(target) - Vector(loc)
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = Vector((0, 0, -1)).rotation_difference(d.normalized())


def configure_render():
    prefs = bpy.context.preferences.addons["cycles"].preferences
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    for dtype in ("OPTIX", "CUDA"):
        prefs.compute_device_type = dtype
        gpus = prefs.get_devices_for_type(dtype)
        if gpus:
            for d in gpus:
                d.use = True
            scene.cycles.device = "GPU"
            break

    scene.cycles.samples = SAMPLES
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.01
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
    scene.cycles.max_bounces = 12

    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"

    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0

    world = bpy.data.worlds.new("Studio World")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.2, 0.2, 0.2, 1.0)
    bg.inputs["Strength"].default_value = 0.6
    scene.world = world


def main():
    configure_render()

    make_cyc()
    make_head()
    make_ears()
    make_body()
    make_boots()
    make_head_details()
    make_loincloth()
    make_belt()
    make_dagger()
    make_claws()

    # Three-point studio lighting.
    target = (0.0, 0.0, 0.7)
    add_area_light("key", (-1.6, -3.6, 2.8), target, 650.0, 1.6, (1.0, 0.96, 0.9))
    add_area_light("fill", (2.8, -2.6, 1.4), target, 130.0, 2.2, (0.85, 0.92, 1.0))
    add_area_light("rim", (0.9, 0.9, 2.6), (0.0, 0.0, 0.95), 420.0, 0.8, (1.0, 1.0, 1.0))

    cam_data = bpy.data.cameras.new("Camera")
    cam_data.lens = 50.0
    cam_data.sensor_width = 36.0
    cam = link(bpy.data.objects.new("Camera", cam_data))
    cam.location = (0.0, -4.15, 0.67)
    cam.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    scene.camera = cam

    scene.render.filepath = OUT_PATH
    bpy.ops.render.render(write_still=True)
    print("WROTE", OUT_PATH)


main()
