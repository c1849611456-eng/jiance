import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""作品说明 第 3 页（工作流示意图）与第 4 页（过程截图与 QA），并合成 4 页 PDF。"""
import os
from PIL import Image, ImageDraw, ImageFont
W, H = 2480, 3508
M = 170
FONT = r"C:\Windows\Fonts\msyh.ttc"; FONTB = r"C:\Windows\Fonts\msyhbd.ttc"
QA = str(paths.BR + '/qa')
OUT = str(paths.DELIVER + '/作品说明.pdf')
def f(sz, b=False): return ImageFont.truetype(FONTB if b else FONT, sz)

def header(d, title, sub=""):
    d.text((M, M), "Brand · Series", font=f(30), fill=(120,120,120))
    d.text((W-M-d.textlength("BRAND · SERIES", font=f(30)), M), "BRAND · SERIES", font=f(30), fill=(120,120,120))
    d.line([(M, M+60), (W-M, M+60)], fill=(210,210,210), width=2)
    d.text((M, M+120), title, font=f(76, True), fill=(20,20,20)); y = M+240
    if sub: d.text((M, y), sub, font=f(34), fill=(110,110,110)); y += 70
    return y

# ---------- 第 3 页：工作流示意图 ----------
p3, d3 = Image.new("RGB",(W,H),(255,255,255)), None
d3 = ImageDraw.Draw(p3)
y = header(d3, "AI 工作流示意", "从灵感与规格到成品 PDF 的完整闭环")
stages = [
    ("① 品牌色彩量化", "Python + NumPy\nalpha>0.98 取样 · 最小二乘拟合渐变\n→ 六套共用色域 (#3D8D90 / #1E4E65 / #1B3B8F / #5C7268 / #E8E4DC)"),
    ("② 规格单一真源", "styles.yaml\n款式结构 / 关键尺寸 / 配色角色 / 面料 / 功能指标 / 标准引用\n→ 页面表格与图注全部由它生成"),
    ("③ 款式可视化", "SDXL (Juggernaut-XL v9) + IPAdapter\n同款同种子 · 四视角批量渲染 (896×1152 → 4× 放大)"),
    ("④ 定点修正", "FLUX.1 Kontext dev\n去多余接缝 / 换模特 / 补齐线条与配件一致性\n（每次改动先做构图与合规自检，不合格自动丢弃）"),
    ("⑤ 技术校准与 QA", "Blender + Anny(CC0) 低机位与纸样 · insightface 人脸比对\nRMBG-1.4 抠图 · 有效分辨率与 ΔE 复检"),
    ("⑥ 排版输出", "Chrome Headless + 自研 HTML/CSS 排版器\nA3 300 dpi · 文字层嵌入 · 不缩放像素"),
]
bh, gap = 330, 55
for i, (t, desc) in enumerate(stages):
    top = y + i*(bh+gap)
    d3.rounded_rectangle([M, top, W-M, top+bh], radius=24, outline=(180,200,205), width=4, fill=(246,250,251))
    d3.text((M+50, top+40), t, font=f(48, True), fill=(20,60,70))
    yy = top+120
    for ln in desc.split("\n"):
        d3.text((M+50, yy), ln, font=f(34), fill=(50,60,65)); yy += 54
    if i < len(stages)-1:
        cx = W//2
        d3.line([(cx, top+bh), (cx, top+bh+gap)], fill=(150,175,180), width=6)
        d3.polygon([(cx-18, top+bh+gap-6), (cx+18, top+bh+gap-6), (cx, top+bh+gap+22)], fill=(150,175,180))
d3.text((M, H-M-40), "Example Company独家冠名 · 泳装产品设计赛道", font=f(28), fill=(140,140,140))
p3.save(os.path.join(QA, "stmt_p3.png"))

# ---------- 第 4 页：过程截图与 QA ----------
p4, d4 = Image.new("RGB",(W,H),(255,255,255)), None
d4 = ImageDraw.Draw(p4)
y = header(d4, "过程截图与质检记录", "生成、修正与一致性核查的实际产物（节选）")
shots = [
    (os.path.join(QA, "B1_face_check.jpg"), "跨视角一致性核查：同一模特、同一款式、同一背景"),
    (os.path.join(QA, "b1_rmbg.jpg"), "背景统一：RMBG-1.4 抠图后合成纯色影棚背景"),
    (os.path.join(QA, "bottom3d_six_v2.jpg"), "3D 几何校核（Blender + CC0 参数化人体）：低机位与比例复核"),
]
bw = W - 2*M
for path, cap in shots:
    if not os.path.exists(path): continue
    im = Image.open(path).convert("RGB")
    im.thumbnail((bw, 620))
    p4.paste(im, (M, y)); y += im.height + 16
    d4.text((M, y), cap, font=f(30), fill=(90,90,90)); y += 60
d4.text((M, y+10), "质检项：人脸相似度 · 背景亮度/方差 · 线条与配件同源 · 有效分辨率 ≥300 dpi · 跨视角色差 ΔE", font=f(32), fill=(40,40,40))
d4.text((M, H-M-40), "Example Company独家冠名 · 泳装产品设计赛道", font=f(28), fill=(140,140,140))
p4.save(os.path.join(QA, "stmt_p4.png"))

pages = [Image.open(os.path.join(QA, "stmt_p%d.png" % i)).convert("RGB") for i in (1,2,3,4)]
pages[0].save(OUT, save_all=True, append_images=pages[1:], resolution=300.0, quality=92)
print("saved", OUT, "%.2f MB" % (os.path.getsize(OUT)/1048576))
