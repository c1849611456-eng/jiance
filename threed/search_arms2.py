import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""手臂姿势网格搜索 v2（修正度量）：
度量 = 全身最大 |x| 的位置与高度 —— 自然下垂时手掌在髋旁 (|x|≈0.18~0.28, z≈0.45~0.75)；
抬起或外张时最大 |x| 会出现在肩高附近或数值过大。"""
import itertools, json, os, sys, time
import numpy as np, torch, trimesh, anny
sys.path.insert(0, str(paths.D3D + '/scripts'))
import anny_body as AB
OUT = str(paths.D3D + '/out')
m = anny.Anny(local_changes="default", facial_actions="none").to(dtype=torch.float32)
labels = list(m.bone_labels)
UP = [l for l in labels if "upperarm" in l]

def build(dx, dz):
    pose = torch.eye(4)[None, None].repeat(1, m.bone_count, 1, 1)
    for nm in UP:
        sg = 1 if nm.split(".")[-1].endswith("L") else -1
        pose[0, labels.index(nm)] = AB.rotmat("X", dx) @ AB.rotmat("Z", sg * dz)
    o = m(pose_parameters=pose, phenotype_kwargs=AB.PHENO, local_changes_kwargs=AB.LOCAL)
    v = o["vertices"].squeeze(0).detach().cpu().numpy().astype(np.float64)
    v[:, 2] -= v[:, 2].min()
    return v

def metric(v):
    ax = np.abs(v[:, 0])
    i = int(np.argmax(ax))
    xmax, z_at = float(ax[i]), float(v[i, 2])
    # 左右对称性：两侧最大 |x| 与对应高度
    L = v[:, 0] > 0; R = v[:, 0] < 0
    xl, zl = float(ax[L].max()), float(v[L][np.argmax(ax[L]), 2])
    xr, zr = float(ax[R].max()), float(v[R][np.argmax(ax[R]), 2])
    asym = abs(xl - xr) + abs(zl - zr)
    cost = abs(xmax - 0.24) * 3 + abs(z_at - 0.60) + 3 * asym
    return dict(xmax=xmax, z=x_at if False else z_at, xl=xl, xr=xr, zl=zl, zr=zr, asym=asym, cost=cost)

best = None; t0 = time.time(); n = 0
for dx, dz in itertools.product(range(-80, 81, 10), range(-80, 81, 10)):
    v = build(dx, dz); n += 1
    mt = metric(v)
    if best is None or mt["cost"] < best[0]:
        best = (mt["cost"], dx, dz, mt)
print("扫描 %d 组，用时 %.1fs" % (n, time.time() - t0))
print("最优 dx=%d dz=%d  |x|max=%.3f @z=%.3f  左(%.3f@%.3f) 右(%.3f@%.3f) 不对称=%.3f 代价=%.3f"
      % (best[1], best[2], best[3]["xmax"], best[3]["z"], best[3]["xl"], best[3]["zl"], best[3]["xr"], best[3]["zr"],
         best[3]["asym"], best[3]["cost"]))
v = build(best[1], best[2])
trimesh.Trimesh(vertices=v, faces=m.faces, process=False).export(os.path.join(OUT, "anny_body.obj"))
json.dump({"dx": best[1], "dz": best[2], "metrics": best[3]}, open(os.path.join(OUT, "arm_pose.json"), "w"), indent=1)
print("已导出 anny_body.obj")
