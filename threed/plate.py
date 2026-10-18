import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""底视图 plate：人体 + A1 衣片，低机位相机；输出彩色 plate 与 canny 线稿。"""
import math, os, sys
import bpy
from PIL import Image, ImageFilter
sys.path.insert(0, str(paths.D3D))
import ghost as G

OUT = str(paths.D3D)

def a1(body):
    z_crotch, z_hipside, z_neck, z_back, z_arm = 0.74, 0.88, 1.26, 1.22, 1.11
    def z_lo(th): return z_crotch + (z_hipside - z_crotch) * math.sin(th) ** 2
    def z_hi(th):
        a = abs(((th + math.pi) % (2 * math.pi)) - math.pi)
        if a < math.radians(26): return z_neck - 0.012 * (a / math.radians(26)) ** 2
        if a > math.pi - math.radians(34): return z_back - 0.05 * (1 - abs(a - math.pi) / math.radians(34))
        # 高领挂脖：前胸到肩前都保持高位（覆盖胸口），只在越过肩线（约 72°)后降到腋下
        if a < math.radians(72):
            return z_neck
        if a < math.radians(92):
            t = G.smoothstep((a - math.radians(72)) / math.radians(20)); return z_neck + (z_arm - z_neck) * t
        t = G.smoothstep((a - math.radians(92)) / (math.pi - math.radians(92) - math.radians(34)))
        return z_arm + (z_back - z_arm) * t
    ob = G.shell(body, "A1_body", z_lo, z_hi, n_th=140, n_z=48, r_max=0.30)
    G.drop_islands(ob, min_faces=80)
    G.solidify(ob)
    ob.data.materials.append(G.mat_cloth("A1", G.hex2rgb("#1B3B8F"), 0.9))
    # 皮肤材质（人体）
    skin = G.mat_cloth("skin", G.hex2rgb("#E8C4A8"), 0.85)
    body.data.materials.clear(); body.data.materials.append(skin)
    return [ob]

if __name__ == "__main__":
    body = G.open_body()
    a1(body)
    sc = G.setup_scene()
    sc.render.resolution_x, sc.render.resolution_y = 1024, 1280
    sc.cycles.samples = 64
    # 低机位：相机 0.25 m、对准髋部、上仰
    for tag, h, tgt, dist, lens in [("low", 0.15, (0, 0, 1.10), 2.2, 35.0),
                                    ("lowlegs", 0.15, (0, 0, 0.55), 1.5, 32.0)]:
        c = G.cam(0.0, 0.0, tgt, dist, lens, height=h)
        sc.camera = c
        sc.render.filepath = os.path.join(OUT, "A1_plate_%s.png" % tag)
        bpy.ops.render.render(write_still=True)
        print("  plate", tag)
        bpy.data.objects.remove(c, do_unlink=True)
    print("DONE")
