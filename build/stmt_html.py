import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""第 9 轮：作品说明改为可选文字版（HTML -> Chrome headless -> PDF），4 页 A4。"""
import base64, os
QA = str(paths.BR + '/qa')
OUT_HTML = os.path.join(QA, "stmt_text.html")
def img_uri(p):
    if not os.path.exists(p): return ""
    return "data:image/jpeg;base64," + base64.b64encode(open(p, "rb").read()).decode()

P1 = """主题：穿在身上的生命力。本系列以「对生命力的渴望」为命题——渴望呼吸、伸展，被光与水接住。泳装离身体最近，不该束缚身体，而该让身体更自由地活着。三海域对应这种渴望的三种状态：爱琴海的钴蓝是觉醒，波罗的海的灰绿是韧性，亚得里亚海的青碧是舒展。
款式与功能。六套覆盖竞技、度假、社交、温泉四类场景，采用高领连体（支撑）、单肩不对称（拉长）、分体高腰（修饰）三类版型，实现 UPF50+、抗氯 200 小时、四向回弹 ≥180%。这三项即生命力的落点：身体能防晒、耐氯、回弹，才敢放心地动与反复地穿。
表达边界。本系列不靠暴露表达生命力，而落在支撑（高领、定型带、插角）、呼吸（激光网眼与双层透气）、延展（高回弹再生弹力）三件事上——标准是「允许身体做多少事」，而非「露出多少皮肤」。
面料。主体为再生尼龙与氨纶混纺（ECONYL® 同级），190–210 g/m²；透光层为激光切割网眼，以 0.3 mm 热压胶条复合，成「内层不透 + 外层半透」结构，既有宝石透光感，又保证不透。面料由回收渔网再生，即是生命力回到身上。
图案与色彩。母题取自品牌 logo 的美人鱼剪影，抽离为连续波纹，让波动密度承担叙事：爱琴海段生长刻线，波罗的海段渐密松针线，亚得里亚海段递减镂空。主色取品牌实测值——青碧 #3D8D90、深蓝 #1E4E65，延伸钴蓝 #1B3B8F、灰绿 #5C7268，以品牌白 #E8E4DC 统一。"""
P2 = """一、所用 AI 工具
· ComfyUI 0.38（生成与批处理平台，本地 GPU 推理）
· FLUX.1 Kontext dev（图像定点编辑：去除多余接缝、更换模特、修正线条与配件一致性）
· Stable Diffusion XL / Juggernaut-XL v9（款式可视化与四视角批量渲染）
· ControlNet（深度/边缘锁定版型）+ IPAdapter（外观与配色一致性参考）
· Blender 5 + Anny 参数化人体模型（CC0；低机位几何校核与纸样展开）
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
核心判断：AI 的角色是把设计意图精确放大，而非替代设计决策。全部可量产性约束与合规边界（不透、不暴露）均由人工设定，再交 AI 执行可视化。"""
STAGES = [("① 品牌色彩量化", "Python + NumPy｜alpha>0.98 取样 · 最小二乘拟合渐变 → 六套共用色域"),
          ("② 规格单一真源", "styles.yaml｜款式结构 / 关键尺寸 / 配色角色 / 面料 / 功能指标 / 标准引用"),
          ("③ 款式可视化", "SDXL (Juggernaut-XL v9) + IPAdapter｜同款同种子 · 四视角批量渲染"),
          ("④ 定点修正", "FLUX.1 Kontext dev｜去接缝 / 换模特 / 补线条；每次改动先过构图与合规自检"),
          ("⑤ 技术校准与 QA", "Blender + Anny(CC0)｜insightface 人脸比对 · RMBG-1.4 抠图 · 分辨率与 ΔE 复检"),
          ("⑥ 排版输出", "Chrome Headless + 自研排版器｜A3 300 dpi · 文字层嵌入 · 不缩放像素")]
shots = [(os.path.join(QA, "B1_face_check.jpg"), "跨视角一致性核查：同一模特 · 同一款式 · 同一背景"),
         (os.path.join(QA, "b1_rmbg.jpg"), "背景统一：RMBG-1.4 抠图后合成纯色影棚背景"),
         (os.path.join(QA, "bottom3d_six_v2.jpg"), "3D 几何校核（Blender + CC0 参数化人体）：低机位与比例复核")]
def paras(t): return "".join("<p>%s</p>" % x.strip() for x in t.split("\n") if x.strip())
flow = "".join('<div class="box"><h4>%s</h4><p>%s</p></div>%s' % (t, d, '<div class="arrow">▼</div>' if i < len(STAGES)-1 else '') for i, (t, d) in enumerate(STAGES))
shot_html = "".join('<figure><img src="%s"><figcaption>%s</figcaption></figure>' % (img_uri(p), c) for p, c in shots if img_uri(p))
html = """<!doctype html><html><head><meta charset="utf-8"><style>
@page { size: A4; margin: 16mm 15mm 14mm 15mm; }
body { font-family: "Microsoft YaHei","Segoe UI",sans-serif; color:#222; font-size:10.5pt; line-height:1.75; }
.hd { display:flex; justify-content:space-between; color:#888; font-size:9pt; border-bottom:1px solid #d8d8d8; padding-bottom:4px; margin-bottom:14px; }
h1 { font-size:22pt; margin:6px 0 4px; letter-spacing:.5px; }
h2 { font-size:12pt; margin:16px 0 6px; color:#1f5b63; }
.sub { color:#777; font-size:9.5pt; margin-bottom:14px; }
p { margin:0 0 9px; text-align:justify; }
.box { border:1.2px solid #b9ced2; background:#f7fbfc; border-radius:8px; padding:10px 14px; }
.box h4 { margin:0 0 4px; font-size:11pt; color:#14454f; }
.box p { margin:0; color:#3b4a4e; font-size:9.5pt; }
.arrow { text-align:center; color:#9db8bd; font-size:11pt; line-height:1.4; }
figure { margin:0 0 7px; page-break-inside:avoid; }
figure img { width:86%; display:block; margin:0 auto; border:1px solid #e2e2e2; border-radius:4px; }
figcaption { color:#666; font-size:9pt; margin-top:3px; }
.page-break { page-break-before: always; }
section.page { height: 262mm; display: flex; flex-direction: column; }
section.page .body { flex: 1 1 auto; }
.pfoot { display: flex; justify-content: space-between; color: #999; font-size: 8.5pt;
         border-top: 1px solid #e2e2e2; padding-top: 5px; margin-top: 8px; }
.pfoot .pn { letter-spacing: .08em; }
.grp { color:#888; font-size:9pt; letter-spacing:.1em; margin:10px 0 0; }
</style></head><body>
<section class="page"><div class="hd"><span>Brand · Series</span><span>BRAND · SERIES</span></div>
<div class="body"><h1>作品说明</h1><div class="sub">Series · Azure Stroke ｜ 女装 6 套（三海域 × 各 2 套）</div>@@P1@@
<div class="pfoot"><span>Example Company独家冠名 · 泳装产品设计赛道</span><span class="pn">第 1 页 / 共 4 页</span></div></section>
<section class="page"><div class="hd"><span>Brand · Series</span><span>BRAND · SERIES</span></div>
<div class="body"><h1>AI 运用过程说明</h1><div class="sub">所用 AI 工具名称、使用环节与操作流程</div>@@P2@@
<div class="pfoot"><span>Example Company独家冠名 · 泳装产品设计赛道</span><span class="pn">第 2 页 / 共 4 页</span></div></section>
<section class="page"><div class="hd"><span>Brand · Series</span><span>BRAND · SERIES</span></div>
<div class="body"><h1>AI 工作流示意</h1><div class="sub">从灵感与规格到成品 PDF 的完整闭环</div>@@FLOW@@
<div class="pfoot"><span>Example Company独家冠名 · 泳装产品设计赛道</span><span class="pn">第 3 页 / 共 4 页</span></div></section>
<section class="page"><div class="hd"><span>Brand · Series</span><span>BRAND · SERIES</span></div>
<div class="body"><h1>过程截图与质检记录</h1><div class="sub">生成、修正与一致性核查的实际产物（节选）</div>@@SHOTS@@
<p class="grp">质检项：人脸相似度 · 背景亮度/方差 · 线条与配件同源 · 有效分辨率 ≥300 dpi · 跨视角色差 ΔE</p></div>
<div class="pfoot"><span>Example Company独家冠名 · 泳装产品设计赛道</span><span class="pn">第 4 页 / 共 4 页</span></div></section>
</body></html>"""
html = html.replace("@@P1@@", paras(P1)).replace("@@P2@@", paras(P2)).replace("@@FLOW@@", flow).replace("@@SHOTS@@", shot_html)
open(OUT_HTML, "w", encoding="utf-8").write(html)
print("html:", OUT_HTML, "%.2f MB" % (os.path.getsize(OUT_HTML)/1048576))
