import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""无模特（幽灵模特）产品图：在 Anny 人体上生成衣片壳，隐藏人体后渲染。
第一版：A1 高领削肩挂脖连体。
"""
import math, os, sys
import bpy, bmesh
from mathutils import Vector

OUT = str(paths.D3D)
BODY_BLEND = str(paths.D3D + '/out' + '/anny_posed.blend')
H = 1.54  # 人体身高（实测）

def srgb(c):
    def f(x): return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4
    return (f(c[0]), f(c[1]), f(c[2]), 1.0)

def hex2rgb(h):
    h = h.lstrip("#")
    return srgb(tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4)))

def open_body():
    bpy.ops.wm.open_mainfile(filepath=BODY_BLEND)
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    body = max(meshes, key=lambda o: len(o.data.vertices))
    for o in list(bpy.data.objects):
        if o is not body and o.type in {'MESH', 'CAMERA', 'LIGHT'}:
            bpy.data.objects.remove(o, do_unlink=True)
    return body

def shell(body, name, z_lo, z_hi, th0=-math.pi, th1=math.pi, n_th=120, n_z=44,
          r_max=0.20, axis_y=0.008, offset=0.004, axis_x=0.0):
    """以人体表面为基准的衣片壳：theta 0 = 正前(-Y)，逆时针为正。"""
    dg = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new()
    grid = []
    for i in range(n_z + 1):
        row = []
        for j in range(n_th + 1):
            th = th0 + (th1 - th0) * j / n_th
            k = i / n_z
            z = z_lo(th) + (z_hi(th) - z_lo(th)) * k
            origin = Vector((axis_x, axis_y, z))
            d = Vector((math.sin(th), -math.cos(th), 0.0))
            hit, loc, nor, idx = body.ray_cast(origin, d, distance=0.60, depsgraph=dg)
            if not hit:
                row.append(None); continue
            r = (loc - origin).length
            if r > r_max:
                row.append(None); continue
            row.append(loc.copy())
        grid.append(row)
    vgrid = []
    for row in grid:
        vr = []
        for p in row:
            if p is None: vr.append(None); continue
            out = Vector((p.x - axis_x, p.y - axis_y, 0.0))
            if out.length > 1e-9: out.normalize()
            vr.append(bm.verts.new(p + out * offset))
        vgrid.append(vr)
    faces = 0
    for i in range(len(vgrid) - 1):
        for j in range(len(vgrid[0]) - 1):
            a, b = vgrid[i][j], vgrid[i + 1][j]
            c, d2 = vgrid[i + 1][j + 1], vgrid[i][j + 1]
            if None in (a, b, c, d2): continue
            try:
                bm.faces.new((a, b, c, d2)); faces += 1
            except ValueError:
                pass
    bm.normal_update()
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    print("  shell %-10s faces=%d" % (name, faces))
    return ob

def drop_islands(ob, min_faces=60):
    """删除连通域中的小岛（射线投射偶尔产生的碎面）"""
    bm = bmesh.new(); bm.from_mesh(ob.data)
    seen = set(); groups = []
    for f in bm.faces:
        if f.index in seen: continue
        stack = [f]; grp = []
        while stack:
            cur = stack.pop()
            if cur.index in seen: continue
            seen.add(cur.index); grp.append(cur)
            for e in cur.edges:
                for nf in e.link_faces:
                    if nf.index not in seen: stack.append(nf)
        groups.append(grp)
    if len(groups) > 1:
        groups.sort(key=len, reverse=True)
        dead = [f for grp in groups[1:] if len(grp) < min_faces for f in grp]
        if dead:
            bmesh.ops.delete(bm, geom=dead, context='FACES')
            print("   drop_islands: 删除 %d 个小岛面（共 %d 岛）" % (len(dead), len(groups)))
    bm.to_mesh(ob.data); bm.free()
    return ob


def solidify(ob, t=0.0015, sub=2):
    so = ob.modifiers.new("S", 'SOLIDIFY'); so.thickness = t; so.offset = 1.0
    ss = ob.modifiers.new("U", 'SUBSURF'); ss.levels = sub; ss.render_levels = sub
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.modifier_apply(modifier="S")
    bpy.ops.object.shade_smooth()
    return ob

def mat_cloth(name, color, rough=0.9, spec=0.12):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = color
    b.inputs["Roughness"].default_value = rough
    for key, val in (("Specular IOR Level", spec), ("Specular", spec), ("IOR", 1.05),
                     ("Sheen Weight", 0.0), ("Coat Weight", 0.0)):
        if key in b.inputs:
            try: b.inputs[key].default_value = val
            except Exception: pass
    return m

def smoothstep(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)

def setup_scene():
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    try:
        a = bpy.context.preferences.addons['cycles'].preferences
        a.compute_device_type = 'OPTIX'; a.get_devices()
        for d in a.devices: d.use = d.type in ('OPTIX', 'CUDA')
        sc.cycles.device = 'GPU'
    except Exception as e: print("gpu warn", e)
    sc.cycles.samples = 64
    try:
        sc.view_settings.view_transform = 'Standard'
        sc.view_settings.look = 'None'
        sc.view_settings.exposure = 0.0
    except Exception as e:
        print("view transform warn", e)
    sc.render.resolution_x, sc.render.resolution_y = 900, 1200
    sc.render.image_settings.file_format = 'PNG'
    w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.63, 0.65, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.22
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
    fl = bpy.context.object; m = mat_cloth("floor", (0.78, 0.78, 0.78, 1), 0.9); fl.data.materials.append(m)
    for loc, en, sz, rot in [((1.6, -2.0, 2.4), 260, 2.0, (52, 0, 38)),
                             ((-1.9, -1.6, 1.3), 140, 2.6, (74, 0, -54)),
                             ((-0.9, 2.1, 1.9), 220, 1.8, (115, 0, 200))]:
        bpy.ops.object.light_add(type='AREA', location=loc)
        L = bpy.context.object; L.data.energy = en; L.data.size = sz
        L.rotation_euler = tuple(math.radians(v) for v in rot)
    return sc

def cam(az_deg, el_deg, target, dist, lens, height=None):
    az, el = math.radians(az_deg), math.radians(el_deg)
    t = Vector(target)
    pos = t + Vector((math.sin(az)*math.cos(el), -math.cos(az)*math.cos(el), math.sin(el))) * dist
    if height is not None: pos.z = height
    bpy.ops.object.camera_add(location=tuple(pos))
    c = bpy.context.object; c.data.lens = lens
    c.rotation_euler = (t - pos).to_track_quat('-Z', 'Y').to_euler()
    return c

def render_views(prefix, body, target=(0, 0, 0.9), dist=3.2, lens=70, views=None):
    sc = bpy.context.scene
    views = views or [("front", 0.0), ("three_quarter", 45.0), ("side", 90.0), ("back", 180.0)]
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    for tag, az in views:
        c = cam(az, 0.0, target, dist, lens)
        sc.camera = c
        sc.render.filepath = os.path.join(OUT, "%s_%s.png" % (prefix, tag))
        bpy.ops.render.render(write_still=True)
        print("  render", tag)
        bpy.data.objects.remove(c, do_unlink=True)

def a1(body):
    """A1 釉面：高领削肩挂脖连体，胸下-胯，高脚。"""
    z_crotch, z_hipside, z_neck, z_back, z_arm = 0.74, 0.88, 1.26, 1.22, 1.11
    def z_lo(th):
        s = math.sin(th) ** 2
        return z_crotch + (z_hipside - z_crotch) * s
    def z_hi(th):
        a = abs(((th + math.pi) % (2 * math.pi)) - math.pi)   # 0=正前
        if a < math.radians(26):      # 正前：挂脖领（窄带）
            return z_neck - 0.012 * (a / math.radians(26)) ** 2
        if a > math.pi - math.radians(34):  # 背面：U 型深开背
            return z_back - 0.05 * (1 - abs(a - math.pi) / math.radians(34))
        if a < math.radians(58):      # 前胸→肩：斜降到胸上（削肩）
            t = smoothstep((a - math.radians(26)) / math.radians(32))
            return z_neck + (z_arm - z_neck) * t
        # 腋下到背面：略回升到背阔
        t = smoothstep((a - math.radians(58)) / (math.pi - math.radians(58) - math.radians(34)))
        return z_arm + (z_back - z_arm) * t
    ob = shell(body, "A1_body", z_lo, z_hi, n_th=140, n_z=48, r_max=0.175)
    solidify(ob)
    ob.data.materials.append(mat_cloth("A1", hex2rgb("#1B3B8F"), 0.9))
    return [ob]

if __name__ == "__main__":
    body = open_body()
    print("body verts", len(body.data.vertices))
    pieces = a1(body)
    # 隐藏人体 -> 幽灵模特
    body.hide_render = True
    setup_scene()
    render_views("A1_ghost", body, target=(0, 0, 1.0), dist=1.75, lens=50)
    print("DONE")
