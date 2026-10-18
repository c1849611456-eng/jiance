import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""路线丙：3D 直出低机位底视图（不过 AI）。
用法: python render_bottom3d.py A1
"""
import math, os, sys
import bpy
import yaml
sys.path.insert(0, str(paths.D3D))
import ghost as G
import garments as GA

BR = str(paths.BR)
OUT = os.path.join(BR, "gen", "nomodel", "3d")
os.makedirs(OUT, exist_ok=True)
SPEC = yaml.safe_load(open(os.path.join(BR, "spec", "styles.yaml"), encoding="utf-8"))
BY_CODE = {s["code"]: s for s in SPEC["styles"]}

# 部件 -> spec 色（role 对齐 styles.yaml）
COLOR_MAP = {
    "A1": {"body": "#1B3B8F"},
    "A2": {"body": "#1B3B8F"},
    "B1": {"body": "#5C7268", "sleeve": "#5C7268", "knee": "#1E4E65"},
    "B2": {"top": "#5C7268", "shorts": "#5C7268", "robe": "#5C7268"},
    "C1": {"body": "#E8E4DC", "skirt": "#3D8D90"},
    "C2": {"top": "#1E4E65", "brief": "#1E4E65"},
}

def part_color(code, name):
    m = COLOR_MAP.get(code, {})
    for k, v in m.items():
        if k in name:
            return v
    return list(m.values())[0] if m else "#888888"

def render(code, res=(1100, 1467), samples=96, cam=(0.14, (0, 0, 1.02), 2.35, 32.0)):
    body = G.open_body()
    parts = GA.BUILDERS[code](body)
    # 材质
    skin = G.mat_cloth("skin_%s" % code, G.hex2rgb("#D9A98C"), 0.82)
    body.data.materials.clear(); body.data.materials.append(skin)
    for ob in parts:
        c = part_color(code, ob.name)
        ob.data.materials.clear(); ob.data.materials.append(G.mat_cloth("%s_%s" % (code, ob.name), G.hex2rgb(c), 0.55))
    sc = G.setup_scene()
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.cycles.samples = samples
    sc.view_settings.view_transform = 'Standard'
    h, tgt, dist, lens = cam
    c = G.cam(0.0, 0.0, tgt, dist, lens, height=h)
    sc.camera = c
    path = os.path.join(OUT, "%s_bottom3d.png" % code)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("rendered", path, "parts=%d" % len(parts))

if __name__ == "__main__":
    code = sys.argv[1] if len(sys.argv) > 1 else "A1"
    render(code)
