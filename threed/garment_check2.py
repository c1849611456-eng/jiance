import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""补齐衣片定义（第二版，不出图）：C2 拆成三角杯+三角裤；C1 加外扩裙摆（参数化锥面）。
纯几何自检：面数/面积/z 范围/左右不对称。"""
import math, os, sys, json
import numpy as np
import bpy, bmesh
from mathutils import Vector
sys.path.insert(0, str(paths.D3D))
import ghost as G
OUT = str(paths.D3D)

def build_shell(body, name, fns, r_max=0.30, n_th=140, n_z=48, off=0.004):
    ob = G.shell(body, name, fns[0], fns[1], n_th=n_th, n_z=n_z, r_max=r_max, offset=off)
    G.drop_islands(ob, min_faces=80); G.solidify(ob); return ob

def build_cone(name, z0, z1, r0, r1, n_th=140, n_z=24, off=0.0):
    """参数化外扩面（裙摆）：圆形锥面，随高度线性外扩。"""
    bm = bmesh.new(); grid = []
    for i in range(n_z + 1):
        k = i / n_z; z = z0 + (z1 - z0) * k; r = r0 + (r1 - r0) * k
        row = [bm.verts.new(Vector((r*math.sin(t), -r*math.cos(t), z)))
               for t in [2*math.pi*j/n_th for j in range(n_th)]]
        grid.append(row)
    for i in range(n_z):
        for j in range(n_th):
            jn = (j+1) % n_th
            try: bm.faces.new((grid[i][j], grid[i+1][j], grid[i+1][jn], grid[i][jn]))
            except ValueError: pass
    bm.normal_update(); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    G.solidify(ob)
    return ob

def metrics(ob):
    me = ob.data
    vs = np.array([[v.co.x, v.co.y, v.co.z] for v in me.vertices])
    area = sum(p.area for p in me.polygons)
    L = sum(p.area for p in me.polygons if p.center.x > 0); R = sum(p.area for p in me.polygons if p.center.x < 0)
    return dict(faces=len(me.polygons), area=float(area), z=[float(vs[:,2].min()), float(vs[:,2].max())],
                x=[float(vs[:,0].min()), float(vs[:,0].max())], asym=float(abs(L-R)/max(area,1e-9)))

# ---- C2：三角杯（上装）+ 三角裤 ----
def c2_top():
    def z_lo(th): return 1.05
    def z_hi(th): return 1.24
    return z_lo, z_hi
def c2_brief():
    zc, zh = 0.72, 0.90
    def z_lo(th): return zc + (zh - zc) * math.sin(th) ** 2
    def z_hi(th): return 0.94 if abs(((th+math.pi)%(2*math.pi))-math.pi) < math.radians(90) else 0.98
    return z_lo, z_hi

# ---- C1：底身 + 网纱裙摆 ----
def c1_body():
    zc, zh, zn = 0.74, 0.88, 1.24
    def z_lo(th): return zc + (zh - zc) * math.sin(th) ** 2
    def z_hi(th):
        a = abs(((th+math.pi) % (2*math.pi)) - math.pi)
        return zn if a < math.radians(60) else zn - 0.06
    return z_lo, z_hi

if __name__ == "__main__":
    body = G.open_body()
    rep = {}
    parts = [("C2", "top", lambda: build_shell(body, "C2_top", c2_top())),
             ("C2", "brief", lambda: build_shell(body, "C2_brief", c2_brief())),
             ("C1", "body", lambda: build_shell(body, "C1_body", c1_body())),
             ("C1", "skirt", lambda: build_cone("C1_skirt", 0.86, 0.56, 0.185, 0.265, off=0.02))]
    for code, nm, fn in parts:
        ob = fn(); mt = metrics(ob)
        rep.setdefault(code, []).append(dict(part=nm, **mt))
        print("%s %-5s faces=%5d area=%.4f m2  z=%.2f..%.2f  x=%.2f..%.2f 不对称=%.3f"
              % (code, nm, mt["faces"], mt["area"], mt["z"][0], mt["z"][1], mt["x"][0], mt["x"][1], mt["asym"]))
    json.dump(rep, open(os.path.join(OUT, "garment_metrics2.json"), "w"), indent=1)
    print("已写 garment_metrics2.json")
