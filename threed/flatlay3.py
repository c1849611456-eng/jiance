import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""平铺产品图 v3（稳版）：衣片壳 -> 按表面弧长展开成纸样 -> 前/后片并排平铺 -> 正交俯视渲染。
只做几何与渲染，所有 None 都显式过滤。"""
import math, os, sys
import bpy, bmesh
from mathutils import Vector
sys.path.insert(0, str(paths.D3D))
import ghost as G

OUT = str(paths.D3D)
LOG = open(os.path.join(OUT, "flatlay_log.txt"), "w", encoding="utf-8")
def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); LOG.write(s + "\n"); LOG.flush()

def sample(body, z_lo, z_hi, th0, th1, n_th=90, n_z=48, r_max=0.175, axis_y=0.008):
    dg = bpy.context.evaluated_depsgraph_get()
    grid = []
    for i in range(n_z + 1):
        row = []
        for j in range(n_th + 1):
            th = th0 + (th1 - th0) * j / n_th
            k = i / n_z
            z = z_lo(th) + (z_hi(th) - z_lo(th)) * k
            o = Vector((0.0, axis_y, z)); d = Vector((math.sin(th), -math.cos(th), 0.0))
            hit, loc, nor, idx = body.ray_cast(o, d, distance=0.6, depsgraph=dg)
            ok = hit and (loc - o).length <= r_max
            row.append(loc.copy() if ok else None)
        grid.append(row)
    return grid

def longest_run(row):
    best = (0, -1); cur = None
    for j in range(len(row) + 1):
        ok = j < len(row) and row[j] is not None
        if ok and cur is None: cur = j
        if not ok and cur is not None:
            if j - cur > best[1] - best[0] + 1: best = (cur, j - 1)
            cur = None
    keep = set(range(best[0], best[1] + 1)) if best[1] >= best[0] else set()
    return [row[j] if j in keep else None for j in range(len(row))]

def unroll(grid):
    """返回 [[(x, z) or None, ...], ...]：x 为该行累计弧长（居中）"""
    out = []
    for row in grid:
        row = longest_run(row)
        xs = [0.0]
        for j in range(1, len(row)):
            a, b = row[j - 1], row[j]
            xs.append(xs[-1] + (0.0 if (a is None or b is None) else float((b - a).length)))
        idxs = [j for j in range(len(row)) if row[j] is not None]
        if idxs:
            mid = (xs[idxs[0]] + xs[idxs[-1]]) / 2.0
        else:
            mid = xs[-1] / 2.0
        out.append([((xs[j] - mid, float(row[j].z)) if row[j] is not None else None) for j in range(len(row))])
    return out

def bbox(rows):
    pts = [p for row in rows for p in row if p is not None]
    if not pts: return None
    xs = [p[0] for p in pts]; zs = [p[1] for p in pts]
    return min(xs), max(xs), min(zs), max(zs)

def build(rows, name, dx=0.0, dz=0.0):
    bm = bmesh.new(); vg = []
    for row in rows:
        vr = []
        for p in row:
            vr.append(bm.verts.new(Vector((p[0] + dx, p[1] + dz, 0.0))) if p is not None else None)
        vg.append(vr)
    faces = 0
    for i in range(len(vg) - 1):
        for j in range(len(vg[0]) - 1):
            a, b, c, d = vg[i][j], vg[i + 1][j], vg[i + 1][j + 1], vg[i][j + 1]
            if None in (a, b, c, d): continue
            try: bm.faces.new((a, b, c, d)); faces += 1
            except ValueError: pass
    bm.normal_update()
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    log("  panel %s faces=%d" % (name, faces))
    return ob

def drape(ob, sub=1, noise=0.0022):
    ss = ob.modifiers.new("U", 'SUBSURF'); ss.levels = sub; ss.render_levels = sub
    tx = ob.modifiers.new("T", 'DISPLACE')
    tex = bpy.data.textures.new("wr", 'CLOUDS'); tex.noise_scale = 0.05; tex.noise_depth = 2
    tx.texture = tex; tx.strength = noise; tx.mid_level = 0.5
    so = ob.modifiers.new("S", 'SOLIDIFY'); so.thickness = 0.0012
    bpy.context.view_layer.objects.active = ob
    for m in ("U", "T", "S"):
        try: bpy.ops.object.modifier_apply(modifier=m)
        except Exception as e: log("   apply", m, "warn", e)
    bpy.ops.object.shade_smooth()

def a1_fns():
    z_crotch, z_hipside, z_neck, z_back, z_arm = 0.74, 0.88, 1.26, 1.22, 1.11
    def z_lo(th): return z_crotch + (z_hipside - z_crotch) * math.sin(th) ** 2
    def z_hi(th):
        a = abs(((th + math.pi) % (2 * math.pi)) - math.pi)
        if a < math.radians(26): return z_neck - 0.012 * (a / math.radians(26)) ** 2
        if a > math.pi - math.radians(34): return z_back - 0.05 * (1 - abs(a - math.pi) / math.radians(34))
        if a < math.radians(58):
            t = G.smoothstep((a - math.radians(26)) / math.radians(32)); return z_neck + (z_arm - z_neck) * t
        t = G.smoothstep((a - math.radians(58)) / (math.pi - math.radians(58) - math.radians(34)))
        return z_arm + (z_back - z_arm) * t
    return z_lo, z_hi

def main():
    body = G.open_body()
    z_lo, z_hi = a1_fns()
    front = unroll(sample(body, z_lo, z_hi, math.radians(-90), math.radians(90)))
    back  = unroll(sample(body, z_lo, z_hi, math.radians(90), math.radians(270)))
    bf, bb = bbox(front), bbox(back)
    log("  bbox front", bf, "back", bb)
    if not bf or not bb:
        log("  empty panel, abort"); return
    gap = 0.07
    wf = bf[1] - bf[0]; wb = bb[1] - bb[0]
    dx_f = -(wf + gap) / 2.0 - bf[0]
    dx_b = (wb + gap) / 2.0 - bb[0]
    zc = (min(bf[2], bb[2]) + max(bf[3], bb[3])) / 2.0
    dz = -zc
    of = build(front, "A1_front", dx_f, dz)
    ob = build(back, "A1_back", dx_b, dz)
    body.hide_render = True
    for o in (of, ob):
        drape(o)
        o.data.materials.append(G.mat_cloth("A1", G.hex2rgb("#1B3B8F"), 0.9))
    # 场景
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    try:
        a = bpy.context.preferences.addons['cycles'].preferences
        a.compute_device_type = 'OPTIX'; a.get_devices()
        for d in a.devices: d.use = d.type in ('OPTIX', 'CUDA')
        sc.cycles.device = 'GPU'
    except Exception as e: log("gpu warn", e)
    sc.cycles.samples = 96
    sc.view_settings.view_transform = 'Standard'
    sc.render.resolution_x, sc.render.resolution_y = 2200, 1500
    sc.render.image_settings.file_format = 'PNG'
    w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.94, 0.94, 0.94, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.5
    bpy.ops.mesh.primitive_plane_add(size=8, location=(0, 0, -0.012))
    bpy.context.object.data.materials.append(G.mat_cloth("paper", (0.97, 0.97, 0.97, 1), 0.95))
    bpy.ops.object.light_add(type='AREA', location=(0.5, -0.8, 1.8))
    L = bpy.context.object; L.data.energy = 130; L.data.size = 1.8
    L.rotation_euler = (math.radians(25), 0, math.radians(18))
    total_w = (bf[1] - bf[0]) + (bb[1] - bb[0]) + gap
    total_h = max(bf[3] - bf[2], bb[3] - bb[2])
    ortho = max(total_w * 1.22, total_h * 1.45)
    bpy.ops.object.camera_add(location=(0, 0, 3.0), rotation=(0, 0, 0))
    c = bpy.context.object; c.data.type = 'ORTHO'; c.data.ortho_scale = ortho
    sc.camera = c
    log("  layout: total_w=%.3f total_h=%.3f ortho=%.3f" % (total_w, total_h, ortho))
    sc.render.filepath = os.path.join(OUT, "A1_flatlay_final.png")
    bpy.ops.render.render(write_still=True)
    log("DONE")

main()
