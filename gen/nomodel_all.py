import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""六款泳衣的无模特平铺产品图：
设计（颜色/印花/结构）来自该款现有渲染 -> IPAdapter #1
观感（俯拍平铺、浅灰底、面料与褶皱）来自用户样图 -> IPAdapter #2
"""
import os, sys, time, shutil
sys.path.insert(0, str(paths.BR + '/gen'))
import kx
from PIL import Image

CKPT = "Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors"
PRESET = "PLUS (high strength)"
RAW = str(paths.RAW)
R2 = str(paths.R2)
CI = str(paths.COMFY + '/input')
OUTD = str(paths.BR + '/gen' + '/nomodel')

STYLE = ("flat lay product photograph, the garment laid flat and centred on a light grey seamless studio background, "
         "shot from directly above in a top-down view, matte swim fabric with a subtle sheen, crisp bound edges, "
         "natural soft folds, soft even studio lighting, subtle contact shadow under the garment, high-end e-commerce "
         "product photography, sharp focus. No people, no model, no mannequin, no body, no hands")
NEG = ("person, model, mannequin, body, skin, hands, legs, arms, hanger, stand, watermark, text, logo, clutter, "
       "low quality, blurry, deformed, extra garments, duplicate")

DESIGN = {
 "A1": "a cobalt blue one-piece swimsuit with a high halter neckline and a narrow collar band, cut-away shoulders with no sleeves, one single thin white bonded seam tape running diagonally from the left shoulder to the right waist, high-cut leg openings",
 "A2": "a cobalt blue asymmetric one-shoulder one-piece swimsuit with a wide strap over one shoulder and a bare other shoulder, three groups of thin white engineered horizontal stripes across the torso, a side waist cut-out",
 "B1": "a slate grey-green long-sleeve one-piece swimsuit with knee-length shorts, a high collar and a central front zip, matte technical fabric",
 "B2": "a sage green two-piece swim set: a soft top with wide straps and high-waisted shorts with a wide waistband, plus a long open-front robe laid beside it, small amber accents",
 "C1": "a swimsuit dress with thin shoulder straps, white to deep teal vertical gradient, white dotted print dense at the top and sparse at the hem, a flared translucent mesh skirt hem",
 "C2": "a two-piece bikini: a halter triangle top in deep navy with a teal under-bust band and teal binding, plus mid-rise briefs in deep navy with teal trim, small gold details",
}
SEED = {"A1": 30001, "A2": 30002, "B1": 30003, "B2": 30004, "C1": 30005, "C2": 30006}

def prep_design_img(code):
    for p in (os.path.join(R2, "%s_front.png" % code), os.path.join(RAW, "%s_front.png" % code)):
        if os.path.exists(p):
            im = Image.open(p).convert("RGB")
            im.thumbnail((1024, 1024))
            dst = os.path.join(CI, "design_%s.png" % code)
            im.resize((768, 1024), Image.LANCZOS).save(dst)
            return "design_%s.png" % code
    return None

def run(code, weight_design=0.72, weight_style=0.55, steps=34, cfg=6.5):
    dimg = prep_design_img(code)
    if not dimg: return False, "no design image"
    pos = DESIGN[code] + ", " + STYLE
    wf = {
      "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CKPT}},
      "2": {"class_type": "LoadImage", "inputs": {"image": dimg, "upload": "image"}},
      "3": {"class_type": "LoadImage", "inputs": {"image": "style_ref_flatlay.png", "upload": "image"}},
      "4": {"class_type": "IPAdapterUnifiedLoader", "inputs": {"model": ["1", 0], "preset": PRESET}},
      "5": {"class_type": "IPAdapterAdvanced",
            "inputs": {"model": ["4", 0], "ipadapter": ["4", 1], "image": ["2", 0], "weight": weight_design,
                       "weight_type": "linear", "combine_embeds": "concat", "start_at": 0.0, "end_at": 0.7,
                       "embeds_scaling": "V only"}},
      "6": {"class_type": "IPAdapterAdvanced",
            "inputs": {"model": ["5", 0], "ipadapter": ["4", 1], "image": ["3", 0], "weight": weight_style,
                       "weight_type": "linear", "combine_embeds": "concat", "start_at": 0.0, "end_at": 0.9,
                       "embeds_scaling": "V only"}},
      "12": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 1], "text": pos}},
      "13": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 1], "text": NEG}},
      "11": {"class_type": "EmptyLatentImage", "inputs": {"width": 896, "height": 1152, "batch_size": 1}},
      "14": {"class_type": "KSampler",
             "inputs": {"model": ["6", 0], "positive": ["12", 0], "negative": ["13", 0], "latent_image": ["11", 0],
                        "seed": SEED[code], "steps": steps, "cfg": cfg, "sampler_name": "dpmpp_2m",
                        "scheduler": "karras", "denoise": 1.0}},
      "15": {"class_type": "VAEDecode", "inputs": {"samples": ["14", 0], "vae": ["1", 2]}},
      "16": {"class_type": "UpscaleModelLoader", "inputs": {"model_name": "4x-UltraSharp.pth"}},
      "17": {"class_type": "ImageUpscaleWithModel", "inputs": {"upscale_model": ["16", 0], "image": ["15", 0]}},
      "18": {"class_type": "SaveImage", "inputs": {"images": ["17", 0], "filename_prefix": "nomodel/%s" % code}},
    }
    pid = kx.api("/prompt", {"prompt": wf, "client_id": "nomodel"}).get("prompt_id")
    if not pid: return False, "submit failed"
    t0 = time.time()
    while time.time() - t0 < 1200:
        h = kx.api("/history/" + pid)
        if pid in h:
            e = h[pid]; st = e.get("status", {})
            if st.get("status_str") == "error":
                msg = ""
                for it in st.get("messages", []):
                    if isinstance(it, (list, tuple)) and len(it) > 1 and isinstance(it[1], dict):
                        msg = it[1].get("exception_message", "") or msg
                return False, "error: " + msg[:220]
            for node in e.get("outputs", {}).values():
                for img in node.get("images", []):
                    p = os.path.join(str(paths.COMFY + '/output'), img.get("subfolder", ""), img["filename"])
                    dst = os.path.join(OUTD, "%s_nomodel.png" % code)
                    shutil.copy2(p, dst)
                    return True, dst
            return False, "no image"
        time.sleep(3)
    return False, "timeout"

if __name__ == "__main__":
    for c in ["A1", "A2", "B1", "B2", "C1", "C2"]:
        out = os.path.join(OUTD, "%s_nomodel.png" % c)
        if os.path.exists(out):
            print("skip", c, flush=True); continue
        kx.free_vram(); t = time.time()
        ok, note = run(c)
        print(("OK " if ok else "FAIL ") + c + " " + str(note) + " %.0fs" % (time.time() - t), flush=True)
    print("NOMODEL-ALL DONE")
