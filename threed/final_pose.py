import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""最终修姿：先用"左臂自然下垂"的解（mode=both，左手正确）生成网格，再把左半身镜像到右半身，
得到左右完全对称、双臂自然下垂的人体。附数值自检（对称性 + 手臂高度）。"""
import os, sys
import numpy as np, torch, trimesh, anny
sys.path.insert(0, str(paths.D3D + '/scripts'))
import anny_body as AB
OUT = str(paths.D3D + '/out')
m = anny.Anny(local_changes="default", facial_actions="none").to(dtype=torch.float32)
labels = list(m.bone_labels)
pose = torch.eye(4)[None, None].repeat(1, m.bone_count, 1, 1)
for nm in [l for l in labels if "upperarm" in l]:
    sg = 1 if nm.split(".")[-1].endswith("L") else -1
    R = AB.rotmat("X", sg * AB.ARM_DX) @ AB.rotmat("Z", sg * AB.ARM_DZ)
    pose[0, labels.index(nm)] = R
o = m(pose_parameters=pose, phenotype_kwargs=AB.PHENO, local_changes_kwargs=AB.LOCAL)
v = o["vertices"].squeeze(0).detach().cpu().numpy().astype(np.float64)
v[:, 2] -= v[:, 2].min()

# —— 镜像：把 x>0 半身按 (|x|, y, z) 最近邻映射到 x<0 ——
pos = v[v[:, 0] > 1e-6]
key = np.stack([pos[:, 0], pos[:, 1], pos[:, 2]], 1)
neg_idx = np.where(v[:, 0] < -1e-6)[0]
q = np.stack([-v[neg_idx, 0], v[neg_idx, 1], v[neg_idx, 2]], 1)
# 分块最近邻
out = np.empty_like(q)
B = 2000
for i in range(0, len(q), B):
    d = ((q[i:i+B, None, :] - key[None, :, :]) ** 2).sum(-1)
    j = d.argmin(1)
    out[i:i+B] = key[j]
v[neg_idx, 0] = -out[:, 0]
v[neg_idx, 1] = out[:, 1]
v[neg_idx, 2] = out[:, 2]
tm = trimesh.Trimesh(vertices=v, faces=m.faces, process=False)
h = v[:, 2].max()
arm = (v[:, 2] > 0.60 * h) & (np.abs(v[:, 0]) > 0.17)
L = arm & (v[:, 0] > 0); R = arm & (v[:, 0] < 0)
print("身高 %.3f  对称偏差 dz=%.5f dx=%.5f" % (h, abs(v[L,2].mean()-v[R,2].mean()), abs(np.abs(v[L,0]).mean()-np.abs(v[R,0]).mean())))
print("手臂高度：均值 z=%.3f（人体 1.43 m；下垂应 ~0.9，上举会 >1.1），最低 z=%.3f" % (v[arm,2].mean(), v[arm,2].min()))
tm.export(os.path.join(OUT, "anny_body.obj"))
print("导出 anny_body.obj（镜像对称、双臂下垂）")
