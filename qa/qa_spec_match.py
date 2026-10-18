import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""第 10 轮：规格真源 <-> 页面文字/表格 一致性核对 + 页眉页脚/文件命名检查。"""
import os, re, yaml
BR = str(paths.BR)
SPEC = yaml.safe_load(open(os.path.join(BR, "spec", "styles.yaml"), encoding="utf-8"))
PG = os.path.join(BR, "build", "pages")
miss_total = 0
for st in SPEC["styles"]:
    c = st["code"]; p = os.path.join(PG, "%s.html" % c)
    if not os.path.exists(p): print("%s: 缺页面文件" % c); continue
    html = open(p, encoding="utf-8").read()
    checks = []
    checks.append(("中文名", st["name_cn"]))
    checks.append(("英文名", st["name_en"]))
    checks.append(("系列", st["series"].split()[0]))
    for col in st["colors"]:
        checks.append(("色 %s" % col["hex"], col["hex"].upper()))
    for kd in st.get("key_dims", []):
        checks.append(("尺寸 %s" % kd[0], str(kd[1]).split("（")[0][:12]))
    for cl in st.get("claims", []):
        checks.append(("指标 %s" % cl[0], str(cl[1])[:14]))
    miss = [n for n, v in checks if str(v) not in html]
    miss_total += len(miss)
    print("%s: 检查 %d 项, 缺失 %d %s" % (c, len(checks), len(miss), ("-> " + "; ".join(miss)) if miss else "✅"))
print("合计缺失:", miss_total)
# 页眉页脚与命名
print()
for c in ["A1","A2","B1","B2","C1","C2"]:
    html = open(os.path.join(PG, "%s.html" % c), encoding="utf-8").read()
    foot = "CityBrand" in html or "SERIES" in html
    print("%s 页脚品牌/系列: %s ; 页脚标准与检测: %s" % (c, "✅" if foot else "❌", "✅" if "标准与检测" in html else "❌"))
DEL = str(paths.DELIVER)
print()
print("交付目录文件:", ", ".join(sorted(f for f in os.listdir(DEL) if os.path.isfile(os.path.join(DEL, f)))))
