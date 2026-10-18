import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""45° 视图（姿态受控）：用 A1 现有 45° 面板的 OpenPose 骨架 + ControlNet(openpose) 锁定身体朝向，
再用 IPAdapter 把目标款的外观贴上去。文字控制角度已证明无效，改用骨架控制。"""
import os, sys, time, shutil
sys.path.insert(0, str(paths.BR + '/gen'))
import kx
CKPT = "Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors"
CN_POSE = "controlnet-openpose-sdxl.safetensors"
R2 = str(paths.R2)
RAW = str(paths.RAW)
NEW = str(paths.BR + '/gen' + '/angle45p'); os.makedirs(NEW, exist_ok=True)
# 姿态参考：A1 的 45° 面板（已确认是标准三分之四侧）
POSE_SRC = os.path.join(R2, "A1_three_quarter.png")
if not os.path.exists(POSE_SRC): POSE_SRC = os.path.join(RAW, "A1_three_quarter.png")
shutil.copy2(POSE_SRC, str(paths.COMFY + '/input' + '/pose45_ref.png'))
DESIGNS = {
 "B1": "a deep sage green long-sleeve one-piece swimsuit with knee-length shorts, high collar, a dark navy front zipper, thin bright white raglan shoulder lines and a white line down the side of the torso, bare lower legs without knee sleeves",
 "B2": "a sage green open-front long robe over a matching crop top with a band and high-waisted shorts with white piped seams",
 "C1": "a white-to-teal swimsuit dress with thin straps, a white dotted-print bodice and a flared teal mesh skirt with a dotted print",
}
def gen(code, seed, out):
    if os.path.exists(out): return True
    ref = os.path.join(R2, "%s_front.png" % code)
    if not os.path.exists(ref): ref = os.path.join(RAW, "%s_front.png" % code)
    shutil.copy2(ref, str(paths.COMFY + '/input' + '/ref45p_%s.png') % code)
    pos = ("full body studio fashion photograph of a young woman standing in a three-quarter pose, wearing " + DESIGNS[code] +
           ". Plain seamless light grey studio backdrop, soft even lighting, sharp focus, photorealistic")
    neg = ("nudity, nude, topless, deformed, extra limbs, bad anatomy, blurry, low quality, watermark, text, logo")
    wf = {
      "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CKPT}},
      "20": {"class_type": "LoadImage", "inputs": {"image": "pose45_ref.png", "upload": "image"}},
      "21": {"class_type": "OpenposePreprocessor", "inputs": {"image": ["20", 0], "detect_hand": "enable", "detect_body": "enable",
             "detect_face": "enable", "resolution": 1024}},
      "3": {"class_type": "LoadImage", "inputs": {"image": "ref45p_%s.png" % code, "upload": "image"}},
      "4": {"class_type": "IPAdapterUnifiedLoader", "inputs": {"model": ["1", 0], "preset": "PLUS (high strength)"}},
      "5": {"class_type": "IPAdapterAdvanced", "inputs": {"model": ["4", 0], "ipadapter": ["4", 1], "image": ["3", 0],
            "weight": 0.75, "weight_type": "linear", "combine_embeds": "concat", "start_at": 0.0, "end_at": 0.85,
            "embeds_scaling": "V only"}},
      "7": {"class_type": "ControlNetLoader", "inputs": {"control_net_name": CN_POSE}},
      "12": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 1], "text": pos}},
      "13": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 1], "text": neg}},
      "10": {"class_type": "ControlNetApplyAdvanced", "inputs": {"positive": ["12", 0], "negative": ["13", 0],
             "control_net": ["7", 0], "image": ["21", 0], "strength": 1.05, "start_percent": 0.0, "end_percent": 0.9}},
      "11": {"class_type": "EmptyLatentImage", "inputs": {"width": 896, "height": 1152, "batch_size": 1}},
      "14": {"class_type": "KSampler", "inputs": {"model": ["5", 0], "positive": ["10", 0], "negative": ["10", 1],
             "latent_image": ["11", 0], "seed": seed, "steps": 36, "cfg": 7.0, "sampler_name": "dpmpp_2m",
             "scheduler": "karras", "denoise": 1.0}},
      "15": {"class_type": "VAEDecode", "inputs": {"samples": ["14", 0], "vae": ["1", 2]}},
      "16": {"class_type": "UpscaleModelLoader", "inputs": {"model_name": "4x-UltraSharp.pth"}},
      "17": {"class_type": "ImageUpscaleWithModel", "inputs": {"upscale_model": ["16", 0], "image": ["15", 0]}},
      "18": {"class_type": "SaveImage", "inputs": {"images": ["17", 0], "filename_prefix": "ang45p/%s" % code}},
    }
    pid = kx.api("/prompt", {"prompt": wf, "client_id": "a45p"}).get("prompt_id")
    t0 = time.time()
    while time.time() - t0 < 900:
        h = kx.api("/history/" + pid)
        if pid in h:
            st = h[pid].get("status", {})
            if st.get("status_str") == "error":
                for it in st.get("messages", []):
                    if isinstance(it, (list, tuple)) and len(it) > 1 and isinstance(it[1], dict):
                        print("  err:", str(it[1].get("exception_message", ""))[:180], flush=True)
                return False
            for node in h[pid].get("outputs", {}).values():
                for img in node.get("images", []):
                    shutil.copy2(os.path.join(str(paths.COMFY + '/output'), img.get("subfolder", ""), img["filename"]), out)
                    return True
            return False
        time.sleep(3)
    return False
for code in ["B1", "B2", "C1"]:
    out = os.path.join(NEW, "%s_45p.png" % code)
    print(code, "OK" if gen(code, 82001, out) else "FAIL", flush=True)
print("POSE45 DONE")
