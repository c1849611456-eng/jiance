import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""重排作品说明 PDF（4 页 A4 300dpi）：① 作品说明 ② AI 运用过程说明（含工具清单）③ 工作流示意图 ④ 过程截图与 QA。"""
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 2480, 3508            # A4 @300dpi
M = 170                       # 页边距
FONT = r"C:\Windows\Fonts\msyh.ttc"
FONTB = r"C:\Windows\Fonts\msyhbd.ttc"
OUT = str(paths.DELIVER + '/作品说明.pdf')
QA = str(paths.BR + '/qa')

def f(size, bold=False):
    return ImageFont.truetype(FONTB if bold else FONT, size)

def wrap(draw, text, font, max_w):
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur); cur = ""; continue
        if draw.textlength(cur + ch, font=font) > max_w:
            lines.append(cur); cur = ch
        else:
            cur += ch
    if cur: lines.append(cur)
    return lines

def page():
    im = Image.new("RGB", (W, H), (255, 255, 255))
    return im, ImageDraw.Draw(im)

def header(d, title, sub=""):
    d.text((M, M), "Brand · Series", font=f(30), fill=(120, 120, 120))
    d.text((W - M - d.textlength("BRAND · SERIES", font=f(30)), M), "BRAND · SERIES", font=f(30), fill=(120, 120, 120))
    d.line([(M, M + 60), (W - M, M + 60)], fill=(210, 210, 210), width=2)
    d.text((M, M + 120), title, font=f(76, True), fill=(20, 20, 20))
    y = M + 240
    if sub:
        d.text((M, y), sub, font=f(34), fill=(110, 110, 110)); y += 70
    return y

def body(d, y, text, size=36, lh=60, max_w=None):
    max_w = max_w or (W - 2 * M)
    for para in text.split("\n"):
        for ln in wrap(d, para, f(size), max_w):
            d.text((M, y), ln, font=f(size), fill=(35, 35, 35)); y += lh
        y += 14
    return y

# ---------- 第 1 页：作品说明 ----------
p1, d1 = page()
y = header(d1, "作品说明", "Series · Azure Stroke ｜ 女装 6 套（三海域 × 各 2 套）")
y = body(d1, y, """主题：穿在身上的生命力。本系列以「对生命力的渴望」为命题——渴望呼吸、伸展，被光与水接住。泳装离身体最近，不该束缚身体，而该让身体更自由地活着。三海域对应这种渴望的三种状态：爱琴海的钴蓝是觉醒，波罗的海的灰绿是韧性，亚得里亚海的青碧是舒展。

款式与功能。六套覆盖竞技、度假、社交、温泉四类场景，采用高领连体（支撑）、单肩不对称（拉长）、分体高腰（修饰）三类版型，实现 UPF50+、抗氯 200 小时、四向回弹 ≥180%。这三项即生命力的落点：身体能防晒、耐氯、回弹，才敢放心地动与反复地穿。

表达边界。本系列不靠暴露表达生命力，而落在支撑（高领、定型带、插角）、呼吸（激光网眼与双层透气）、延展（高回弹再生弹力）三件事上——标准是「允许身体做多少事」，而非「露出多少皮肤」。

面料。主体为再生尼龙与氨纶混纺（ECONYL® 同级），190–210 g/m²；透光层为激光切割网眼，以 0.3 mm 热压胶条复合，成「内层不透 + 外层半透」结构，既有宝石透光感，又保证不透。面料由回收渔网再生，即是生命力回到身上。

图案与色彩。母题取自品牌 logo 的美人鱼剪影，抽离为连续波纹，让波动密度承担叙事：爱琴海段生长刻线，波罗的海段渐密松针线，亚得里亚海段递减镂空。主色取品牌实测值——青碧 #3D8D90、深蓝 #1E4E65，延伸钴蓝 #1B3B8F、灰绿 #5C7268，以品牌白 #E8E4DC 统一。""")
d1.text((M, H - M - 40), "Example Company独家冠名 · 泳装产品设计赛道", font=f(28), fill=(140, 140, 140))
p1.save(os.path.join(QA, "stmt_p1.png"))

# ---------- 第 2 页：AI 运用过程说明 ----------
p2, d2 = page()
y = header(d2, "AI 运用过程说明", "所用 AI 工具名称、使用环节与操作流程")
y = body(d2, y, """一、所用 AI 工具

· ComfyUI 0.38（生成与批处理平台，本地 GPU 推理）
· FLUX.1 Kontext dev（图像定点编辑：去除多余接缝、更换模特、修正线条与配件一致性）
· Stable Diffusion XL / Juggernaut-XL v9（款式可视化与四视角批量渲染）
· ControlNet（深度/边缘锁定版型）+ IPAdapter（外观与配色一致性参考）
· Blender 5 + Anny 参数化人体模型（CC0，低机位几何校核与纸样展开）
· insightface（buffalo_l）人脸一致性比对 · RMBG-1.4（抠图与背景统一）
· Chrome Headless + 自研 HTML/CSS 排版器（A3 300 dpi 输出、文字层嵌入）

二、使用环节与操作流程

第 1 步 色彩定位（工具：Python + NumPy）。分离 logo 的 alpha 通道，只统计 alpha > 0.98 的实心像素，避开抗锯齿边缘污染，得到品牌真实色域：上端 #3D8D90、下端 #1E4E65、字标纯黑；再用最小二乘拟合渐变平面，确认色相锁定 191.5°（p5–p95 = 182.9–199.4°），据此扩展为六套共用色域。

第 2 步 方案与视觉生成（工具：SDXL / Juggernaut-XL v9 + ControlNet + IPAdapter，ComfyUI 编排）。设计侧先确定三海域款式分工、功能指标与生命力叙事链（人工决策），再用生成模型完成款式可视化。提示词固定为色彩值 + 版型结构 + 面料质感 + 图案 + 视角 + 光线 + 工艺细节 + 负面词；同一套四视角共用同一随机种子与人物描述，确保 24 张图色彩与质感一致。

第 3 步 技术校准与一致性 QA（工具：Blender + Anny 人体、insightface、RMBG-1.4、自研 QA 脚本）。生成图只作视觉呈现，版型尺寸以技术平面图为准；技术图由自研矢量光栅器绘制，不经过生成模型。跨视角一致性按四项核查：人脸相似度、背景亮度/方差、线条与配件是否同源、有效分辨率（≥300 dpi）。

第 4 步 成品输出（工具：Chrome Headless + 自研排版器）。图像统一 RGB、300 dpi，以 JPG 排入 PDF；导出时不缩放像素、不二次压缩，避免模糊与色偏。

三、人机分工

人工负责：目标人群、款式分工、生命力叙事链与表达边界、功能指标、可量产性判断、工艺取舍。
AI 负责：色彩量化提取、渐变建模、款式可视化、批量视角渲染、技术图绘制与排版。
核心判断：AI 的角色是把设计意图精确放大，而非替代设计决策。全部可量产性约束与合规边界（不透、不暴露）均由人工设定，再交 AI 执行可视化。""", size=32, lh=52)
d2.text((M, H - M - 40), "Example Company独家冠名 · 泳装产品设计赛道", font=f(28), fill=(140, 140, 140))
p2.save(os.path.join(QA, "stmt_p2.png"))
print("p1/p2 ok")
