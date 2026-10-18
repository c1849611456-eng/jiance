import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""六款衣片统一定义库 garments.py（不出图）：
build(style) -> [部件对象]；python garments.py 跑全量自检并打印表。
所有尺寸取自 _bridge/spec/styles.yaml 的关键尺寸（z 以 anny_posed 身高 1.429 m 为基准）。
"""
import math
import bpy, bmesh
from mathutils import Vector
import sys
sys.path.insert(0, str(paths.D3D))
import ghost as G

def _ss(x): return G.smoothstep(x)

def shell(body, name, z_lo, z_hi, **kw):
    ob = G.shell(body, name, z_lo, z_hi, **kw)
    G.drop_islands(ob, min_faces=60); G.solidify(ob); return ob

def cone(name, z0, z1, r0, r1, th0=-math.pi, th1=math.pi, n_th=120, n_z=20):
    bm = bmesh.new(); grid = []
    for i in range(n_z + 1):
        k = i / n_z; z = z0 + (z1 - z0) * k; r = r0 + (r1 - r0) * k
        grid.append([bm.verts.new(Vector((r*math.sin(t), -r*math.cos(t), z)))
                     for t in [th0 + (th1-th0)*j/n_th for j in range(n_th + 1)]])
    for i in range(n_z):
        for j in range(n_th):
            try: bm.faces.new((grid[i][j], grid[i+1][j], grid[i+1][j+1], grid[i][j+1]))
            except ValueError: pass
    bm.normal_update(); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    G.solidify(ob); return ob

# ---------- 各款 ----------
def A1(body):
    zc, zh, zn, zb, za = 0.70, 0.80, 1.26, 1.22, 1.08
    def z_lo(th): return zc + (zh - zc) * math.sin(th) ** 2
    def z_hi(th):
        a = abs(((th + math.pi) % (2*math.pi)) - math.pi)
        if a < math.radians(72): return zn
        if a < math.radians(92): return zn + (za - zn) * _ss((a - math.radians(72)) / math.radians(20))
        return za + (zb - za) * _ss((a - math.radians(92)) / (math.pi - math.radians(92) - math.radians(34)))
    return [shell(body, "A1_body", z_lo, z_hi, n_th=140, n_z=48, r_max=0.30)]

def A2(body):
    zc, zh, zsh, zch = 0.70, 0.81, 1.26, 1.08
    def z_lo(th): return zc + (zh - zc) * math.sin(th) ** 2
    def z_hi(th):
        a = ((th + math.pi) % (2*math.pi)) - math.pi
        if a > math.radians(30): return zsh
        if a > math.radians(-30): return zsh + (zch - zsh) * _ss((math.radians(30) - a) / math.radians(60))
        return zch
    return [shell(body, "A2_body", z_lo, z_hi, n_th=140, n_z=48, r_max=0.30)]

def B1(body):
    outs = [shell(body, "B1_body", lambda th: 0.50, lambda th: 1.28, n_th=140, n_z=48, r_max=0.30)]
    for sx, tag in ((0.19, "L"), (-0.19, "R")):
        outs.append(shell(body, "B1_sleeve_%s" % tag, lambda th: 0.78, lambda th: 1.28,
                          r_max=0.12, n_th=80, n_z=30, offset=0.003, axis_x=sx))
    for sx, tag in ((0.09, "L"), (-0.09, "R")):
        outs.append(shell(body, "B1_knee_%s" % tag, lambda th: 0.28, lambda th: 0.56,
                          r_max=0.14, n_th=80, n_z=24, offset=0.003, axis_x=sx))
    return outs

def B2(body):
    return [shell(body, "B2_top", lambda th: 1.06, lambda th: 1.22, n_th=120, n_z=30, r_max=0.30),
            shell(body, "B2_shorts", lambda th: 0.72, lambda th: 0.96, n_th=120, n_z=36, r_max=0.30),
            cone("B2_robe", 1.36, 0.72, 0.22, 0.30, th0=math.radians(35), th1=math.radians(325))]

def C1(body):
    zc, zh, zn = 0.74, 0.88, 1.24
    def z_lo(th): return zc + (zh - zc) * math.sin(th) ** 2
    def z_hi(th):
        a = abs(((th + math.pi) % (2*math.pi)) - math.pi)
        return zn if a < math.radians(60) else zn - 0.06
    return [shell(body, "C1_body", z_lo, z_hi, n_th=140, n_z=48, r_max=0.30),
            cone("C1_skirt", 0.86, 0.56, 0.185, 0.265)]

def C2(body):
    zc, zh = 0.68, 0.88
    def b_lo(th): return zc + (zh - zc) * math.sin(th) ** 2
    def b_hi(th): return 0.94 if abs(((th+math.pi) % (2*math.pi)) - math.pi) < math.radians(90) else 0.98
    return [shell(body, "C2_top", lambda th: 1.05, lambda th: 1.24, n_th=120, n_z=30, r_max=0.30),
            shell(body, "C2_brief", b_lo, b_hi, n_th=140, n_z=36, r_max=0.30)]

BUILDERS = {"A1": A1, "A2": A2, "B1": B1, "B2": B2, "C1": C1, "C2": C2}

def metrics(ob):
    me = ob.data
    import numpy as np
    vs = np.array([[v.co.x, v.co.y, v.co.z] for v in me.vertices])
    area = sum(p.area for p in me.polygons)
    L = sum(p.area for p in me.polygons if p.center.x > 0); R = sum(p.area for p in me.polygons if p.center.x < 0)
    full = (vs[:,0].min() < -0.05 and vs[:,0].max() > 0.05)
    return dict(name=ob.name, faces=len(me.polygons), area=float(area),
                z=[float(vs[:,2].min()), float(vs[:,2].max())], x=[float(vs[:,0].min()), float(vs[:,0].max())],
                asym=(float(abs(L-R)/max(area,1e-9)) if full else None))

if __name__ == "__main__":
    import json, os
    body = G.open_body()
    rep = {}
    for code, fn in BUILDERS.items():
        parts = fn(body)
        rep[code] = [metrics(o) for o in parts]
        tot = sum(m["area"] for m in rep[code])
        print("%s: %d 件，总面积 %.4f m² -> %s" % (code, len(parts), tot,
              "; ".join("%s %.3f" % (m["name"].split("_", 1)[1], m["area"]) for m in rep[code])))
    out = os.path.join(str(paths.D3D), "garments_all_metrics.json")
    json.dump(rep, open(out, "w"), indent=1)
    print("已写", os.path.basename(out))
