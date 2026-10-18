import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""补齐 B1 袖片/膝套 与 B2 三件（不出图，纯几何自检）。"""
import math, os, sys, json
import numpy as np
import bpy, bmesh
from mathutils import Vector
sys.path.insert(0, str(paths.D3D))
import ghost as G
OUT = str(paths.D3D)

def build_shell(body, name, fns, r_max=0.30, n_th=120, n_z=40, off=0.004, axis_x=0.0):
    ob = G.shell(body, name, fns[0], fns[1], n_th=n_th, n_z=n_z, r_max=r_max, offset=off, axis_x=axis_x)
    G.drop_islands(ob, min_faces=60); G.solidify(ob); return ob

def cone(name, z0, z1, r0, r1, th0=-math.pi, th1=math.pi, n_th=120, n_z=20, cx=0.0, cy=0.0):
    bm = bmesh.new(); grid = []
    for i in range(n_z + 1):
        k = i / n_z; z = z0 + (z1 - z0) * k; r = r0 + (r1 - r0) * k
        row = [bm.verts.new(Vector((cx + r*math.sin(t), cy - r*math.cos(t), z)))
               for t in [th0 + (th1-th0)*j/n_th for j in range(n_th + 1)]]
        grid.append(row)
    for i in range(n_z):
        for j in range(n_th):
            try: bm.faces.new((grid[i][j], grid[i+1][j], grid[i+1][j+1], grid[i][j+1]))
            except ValueError: pass
    bm.normal_update(); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    G.solidify(ob); return ob

def metrics(ob):
    me = ob.data
    vs = np.array([[v.co.x, v.co.y, v.co.z] for v in me.vertices])
    area = sum(p.area for p in me.polygons)
    L = sum(p.area for p in me.polygons if p.center.x > 0); R = sum(p.area for p in me.polygons if p.center.x < 0)
    return dict(faces=len(me.polygons), area=float(area), z=[float(vs[:,2].min()), float(vs[:,2].max())],
                x=[float(vs[:,0].min()), float(vs[:,0].max())], asym=float(abs(L-R)/max(area,1e-9)))

if __name__ == "__main__":
    body = G.open_body()
    rep = []
    parts = []
    # B1 袖片：手臂轴 x=±0.19，z 0.78..1.28
    for side, sx in (("L", 0.19), ("R", -0.19)):
        parts.append(("B1", "sleeve_%s" % side,
                      lambda sx=sx: build_shell(body, "B1_sleeve_%s" % ("L" if sx > 0 else "R"),
                                                (lambda th: 0.78, lambda th: 1.28),
                                                r_max=0.12, n_th=80, n_z=30, off=0.003, axis_x=sx)))
    # B1 膝套：腿轴 x=±0.09，z 0.28..0.56
    for side, sx in (("L", 0.09), ("R", -0.09)):
        parts.append(("B1", "knee_%s" % side,
                      lambda sx=sx: build_shell(body, "B1_knee_%s" % ("L" if sx > 0 else "R"),
                                                (lambda th: 0.28, lambda th: 0.56),
                                                r_max=0.14, n_th=80, n_z=24, off=0.003, axis_x=sx)))
    # B2：抹胸上装（1.06..1.22）、高腰短裤（0.72..0.96）、罩衫（开口长袍，参数化外扩）
    parts.append(("B2", "top", lambda: build_shell(body, "B2_top", (lambda th: 1.06, lambda th: 1.22), r_max=0.30)))
    parts.append(("B2", "shorts", lambda: build_shell(body, "B2_shorts", (lambda th: 0.72, lambda th: 0.96), r_max=0.30)))
    parts.append(("B2", "robe", lambda: cone("B2_robe", 1.36, 0.72, 0.22, 0.30,
                                             th0=math.radians(35), th1=math.radians(325))))
    for code, nm, fn in parts:
        try:
            ob = fn(); mt = metrics(ob)
            rep.append(dict(style=code, part=nm, **mt))
            print("%s %-10s faces=%5d area=%.4f m2  z=%.2f..%.2f  x=%.2f..%.2f 不对称=%.3f"
                  % (code, nm, mt["faces"], mt["area"], mt["z"][0], mt["z"][1], mt["x"][0], mt["x"][1], mt["asym"]))
        except Exception as e:
            print("%s %-10s 失败: %s" % (code, nm, e))
    json.dump(rep, open(os.path.join(OUT, "garment_metrics3.json"), "w"), indent=1)
    print("已写 garment_metrics3.json")
