import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""六款衣片的参数化定义 + 纯几何自检（不出图）：
每个部件记录（面数、包围盒、在给定高度处的角度覆盖、左右面积对称性）。
"""
import math, os, sys, json
import numpy as np
import bpy, bmesh
from mathutils import Vector
sys.path.insert(0, str(paths.D3D))
import ghost as G

OUT = str(paths.D3D)
H = 1.429  # anny_posed 身高

def fns_A1():
    zc, zh, zn, zb, za = 0.72, 0.86, 1.26, 1.22, 1.11
    def z_lo(th): return zc + (zh - zc) * math.sin(th) ** 2
    def z_hi(th):
        a = abs(((th + math.pi) % (2*math.pi)) - math.pi)
        if a < math.radians(72): return zn
        if a < math.radians(92):
            return zn + (za - zn) * G.smoothstep((a - math.radians(72)) / math.radians(20))
        t = G.smoothstep((a - math.radians(92)) / (math.pi - math.radians(92) - math.radians(34)))
        return za + (zb - za) * t
    return z_lo, z_hi

def fns_A2():
    """单肩：右肩带高、左肩裸；顶边随 θ 一侧高一侧低。"""
    zc, zh, zshoulder, zchest, zb = 0.72, 0.88, 1.26, 1.10, 1.24
    def z_lo(th): return zc + (zh - zc) * math.sin(th) ** 2
    def z_hi(th):
        a = ((th + math.pi) % (2*math.pi)) - math.pi   # -pi..pi, 0=前
        # 右肩 = th>0 一侧
        if a > math.radians(30): return zshoulder
        if a > math.radians(-30):
            t = G.smoothstep((math.radians(30) - a) / math.radians(60))
            return zshoulder + (zchest - zshoulder) * t
        return zchest
    return z_lo, z_hi

def fns_B1():
    """高领长袖连体短裤：躯干到中腿，另加两只袖子与两只膝套。"""
    zc, zhem, zn = 0.50, 0.50, 1.28
    def z_lo(th): return zhem
    def z_hi(th): return zn
    return z_lo, z_hi

def fns_C1():
    """连体泳装裙：底身（胸到胯）+ 外扩裙摆（胯到中腿）。"""
    zc, zh, zn = 0.74, 0.88, 1.24
    def z_lo(th): return zc + (zh - zc) * math.sin(th) ** 2
    def z_hi(th):
        a = abs(((th + math.pi) % (2*math.pi)) - math.pi)
        return zn if a < math.radians(60) else zn - 0.06
    return z_lo, z_hi

def fns_C2():
    """比基尼：三角杯（胸）+ 三角裤（胯）。"""
    def z_lo(th): return 0.80
    def z_hi(th):
        a = abs(((th + math.pi) % (2*math.pi)) - math.pi)
        return 1.24 if a < math.radians(95) else 1.24
    return z_lo, z_hi

def build_part(body, name, fns, r_max=0.30, n_th=140, n_z=48, off=0.004):
    ob = G.shell(body, name, fns[0], fns[1], n_th=n_th, n_z=n_z, r_max=r_max, offset=off)
    G.drop_islands(ob, min_faces=80)
    G.solidify(ob)
    return ob

def metrics(ob):
    me = ob.data
    vs = np.array([[v.co.x, v.co.y, v.co.z] for v in me.vertices])
    area = sum(p.area for p in me.polygons)
    left = sum(p.area for p in me.polygons if p.center.x > 0)
    right = sum(p.area for p in me.polygons if p.center.x < 0)
    return dict(faces=len(me.polygons), area=float(area),
                z=[float(vs[:,2].min()), float(vs[:,2].max())],
                x=[float(vs[:,0].min()), float(vs[:,0].max())],
                asym=float(abs(left - right) / max(area, 1e-9)))

if __name__ == "__main__":
    body = G.open_body()
    specs = {"A1": [("body", fns_A1())], "A2": [("body", fns_A2())],
             "B1": [("body", fns_B1())], "C1": [("shell", fns_C1())],
             "C2": [("brief", fns_C2())]}
    rep = {}
    for code, parts in specs.items():
        rep[code] = []
        for nm, f in parts:
            ob = build_part(body, "%s_%s" % (code, nm), f)
            mt = metrics(ob)
            rep[code].append(dict(part=nm, **mt))
            print("%s %-5s faces=%5d area=%.4f m2  z=%.2f..%.2f  x=%.2f..%.2f 左右不对称=%.3f"
                  % (code, nm, mt["faces"], mt["area"], mt["z"][0], mt["z"][1], mt["x"][0], mt["x"][1], mt["asym"]))
    json.dump(rep, open(os.path.join(OUT, "garment_metrics.json"), "w"), indent=1)
    print("已写 garment_metrics.json")
