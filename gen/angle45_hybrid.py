import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""45° 再试（双 ControlNet）：深度(姿态/朝向, 弱) + 边缘(该款自身的轮廓, 中) + IPAdapter(强)，
目标：拿到 45° 朝向的同时保住拖尾部件（罩衫/裙摆/短裤）。"""
import os, sys, time, shutil
sys.path.insert(0, str(paths.BR + '/gen'))
import kx
CKPT = "Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors"
R2 = str(paths.R2)
RAW = str(paths.RAW)
NEW = str(paths.BR + '/gen' + '/angle45h'); os.makedirs(NEW, exist_ok=True)
POSE = os.path.join(R2, "A2_three_quarter.png")
if not os.path.exists(POSE): POSE = os.path.join(RAW, "A2_three_quarter.png")
shutil.copy2(POSE, str(paths.COMFY + '/input' + '/pose45_A2.png'))
DESIGNS = {
 "B1": "a deep sage green long-sleeve one-piece swimsuit with knee-length shorts, high collar, dark navy front zipper, thin bright white raglan shoulder lines and a white line down the side of the torso, bare lower legs without knee sleeves",
 "B2": "a sage green open-front long robe over a matching crop top with a band and high-waisted shorts with white piped seams",
 "C1": "a white-to-teal swimsuit dress with thin straps, a white dotted-print bodice and a flared teal mesh skirt with a dotted print",
}
def gen(code, out):
    if os.path.exists(out): return True
    ref = os.path.join(R2, "%s_front.png" % code)
    if not os.path.exists(ref): ref = os.path.join(RAW, "%s_front.png" % code)
    shutil.copy2(ref, str(paths.COMFY + '/input' + '/h45_%s.png') % code)
    pos = ("full body studio fashion photograph of a young woman standing in a three-quarter pose, wearing " + DESIGNS[code] +
           ". Plain seamless light grey studio backdrop, soft even lighting, sharp focus, photorealistic")
    neg = ("nudity, nude, topless, deformed, extra limbs, bad anatomy, blurry, low quality, watermark, text, logo")
    wf = {
      "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CKPT}},
      "20": {"class_type": "LoadImage", "inputs": {"image": "pose45_A2.png", "upload": "image"}},
      "21": {"class_type": "DepthAnythingV2Preprocessor", "inputs": {"image": ["20", 0], "ckpt_name": "depth_anything_v2_vits.pth", "resolution": 1024}},
      "22": {"class_type": "LoadImage", "inputs": {"image": "h45_%s.png" % code, "upload": "image"}},
      "23": {"class_type": "CannyEdgePreprocessor", "inputs": {"image": ["22", 0], "low_threshold": 60, "high_threshold": 180, "resolution": 1024}},
      "3": {"class_type": "LoadImage", "inputs": {"image": "h45_%s.png" % code, "upload": "image"}},
      "4": {"class_type": "IPAdapterUnifiedLoader", "inputs": {"model": ["1", 0], "preset": "PLUS (high strength)"}},
      "5": {"class_type": "IPAdapterAdvanced", "inputs": {"model": ["4", 0], "ipadapter": ["4", 1], "image": ["3", 0],
            "weight": 0.9, "weight_type": "linear", "combine_embeds": "concat", "start_at": 0.0, "end_at": 0.9,
            "embeds_scaling": "V only"}},
      "7": {"class_type": "ControlNetLoader", "inputs": {"control_net_name": "controlnet-depth-sdxl.safetensors"}},
      "8": {"class_type": "ControlNetLoader", "inputs": {"control_net_name": "controlnet-canny-sdxl.safetensors"}},
      "12": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 1], "text": pos}},
      "13": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 1], "text": neg}},
      "10": {"class_type": "ControlNetApplyAdvanced", "inputs": {"positive": ["12", 0], "negative": ["13", 0],
             "control_net": ["7", 0], "image": ["21", 0], "strength": 0.62, "start_percent": 0.0, "end_percent": 0.75}},
      "24": {"class_type": "ControlNetApplyAdvanced", "inputs": {"positive": ["10", 0], "negative": ["10", 1],
             "control_net": ["8", 0], "image": ["23", 0], "strength": 0.45, "start_percent": 0.0, "end_percent": 0.6}},
      "11": {"class_type": "EmptyLatentImage", "inputs": {"width": 896, "height": 1152, "batch_size": 1}},
      "14": {"class_type": "KSampler", "inputs": {"model": ["5", 0], "positive": ["24", 0], "negative": ["24", 1],
             "latent_image": ["11", 0], "seed": 83001, "steps": 36, "cfg": 7.0, "sampler_name": "dpmpp_2m",
             "scheduler": "karras", "denoise": 1.0}},
      "15": {"class_type": "VAEDecode", "inputs": {"samples": ["14", 0], "vae": ["1", 2]}},
      "16": {"class_type": "UpscaleModelLoader", "inputs": {"model_name": "4x-UltraSharp.pth"}},
      "17": {"class_type": "ImageUpscaleWithModel", "inputs": {"upscale_model": ["16", 0], "image": ["15", 0]}},
      "18": {"class_type": "SaveImage", "inputs": {"images": ["17", 0], "filename_prefix": "ang45h/%s" % code}},
    }
    pid = kx.api("/prompt", {"prompt": wf, "client_id": "a45h"}).get("prompt_id")
    t0 = time.time()
    while time.time() - t0 < 900:
        h = kx.api("/history/" + pid)
        if pid in h:
            st = h[pid].get("status", {})
            if st.get("status_str") == "error":
                for it in st.get("messages", []):
                    if isinstance(it, (list, tuple)) and len(it) > 1 and isinstance(it[1], dict):
                        print("  err:", str(it[1].get("exception_message", ""))[:160], flush=True)
                return False
            for node in h[pid].get("outputs", {}).values():
                for img in node.get("images", []):
                    shutil.copy2(os.path.join(str(paths.COMFY + '/output'), img.get("subfolder", ""), img["filename"]), out)
                    return True
            return False
        time.sleep(3)
    return False
for code in ["B1", "B2", "C1"]:
    print(code, "OK" if gen(code, os.path.join(NEW, "%s_45h.png" % code)) else "FAIL", flush=True)
print("HYBRID45 DONE")
