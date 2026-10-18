import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""照片级平铺产品图：形状来自 3D 展开纸样（ControlNet canny），观感来自用户给的参考照（IPAdapter）。"""
import os, sys, time, shutil
sys.path.insert(0, str(paths.BR + '/gen'))
import kx

CKPT = "Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors"
CN_CANNY = "controlnet-canny-sdxl.safetensors"
PRESET = "PLUS (high strength)"
POS = ("flat lay product photograph of a COBALT BLUE one-piece swimsuit laid flat on a light grey seamless studio "
       "background, shot from directly above, top-down view. Design: high halter neckline with a narrow collar band, "
       "cut-away shoulders (no sleeves), ONE single thin white bonded seam tape running diagonally from the left "
       "shoulder across the chest down to the right waist, high-cut leg openings with light binding, matte recycled "
       "nylon-lycra swim fabric with a subtle sheen, natural soft folds, soft even studio lighting, subtle contact "
       "shadow, high-end e-commerce product photography, sharp focus, no people")
NEG = ("person, model, mannequin, body, skin, hands, legs, hanger, stand, watermark, text, logo, clutter, low quality, "
       "blurry, deformed, extra garments")

def run(shape_img="shape_A1_front.png", style_img="style_ref_flatlay.png", seed=20250, out="A1_flatlay_ai2.png",
        weight=0.7, cn_strength=0.85):
    wf = {
      "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CKPT}},
      "2": {"class_type": "LoadImage", "inputs": {"image": shape_img, "upload": "image"}},
      "3": {"class_type": "LoadImage", "inputs": {"image": style_img, "upload": "image"}},
      "4": {"class_type": "IPAdapterUnifiedLoader", "inputs": {"model": ["1", 0], "preset": PRESET}},
      "5": {"class_type": "IPAdapterAdvanced",
            "inputs": {"model": ["4", 0], "ipadapter": ["4", 1], "image": ["3", 0], "weight": weight,
                       "weight_type": "linear", "combine_embeds": "concat", "start_at": 0.0, "end_at": 0.8,
                       "embeds_scaling": "V only"}},
      "6": {"class_type": "CannyEdgePreprocessor",
            "inputs": {"image": ["2", 0], "low_threshold": 80, "high_threshold": 200, "resolution": 1024}},
      "7": {"class_type": "ControlNetLoader", "inputs": {"control_net_name": CN_CANNY}},
      "10": {"class_type": "ControlNetApplyAdvanced",
             "inputs": {"positive": ["12", 0], "negative": ["13", 0], "control_net": ["7", 0],
                        "image": ["6", 0], "strength": cn_strength, "start_percent": 0.0, "end_percent": 1.0}},
      "12": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 1], "text": POS}},
      "13": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 1], "text": NEG}},
      "11": {"class_type": "EmptyLatentImage", "inputs": {"width": 896, "height": 1152, "batch_size": 1}},
      "14": {"class_type": "KSampler",
             "inputs": {"model": ["5", 0], "positive": ["10", 0], "negative": ["10", 1], "latent_image": ["11", 0],
                        "seed": seed, "steps": 34, "cfg": 7.0, "sampler_name": "dpmpp_2m", "scheduler": "karras",
                        "denoise": 1.0}},
      "15": {"class_type": "VAEDecode", "inputs": {"samples": ["14", 0], "vae": ["1", 2]}},
      "16": {"class_type": "UpscaleModelLoader", "inputs": {"model_name": "4x-UltraSharp.pth"}},
      "17": {"class_type": "ImageUpscaleWithModel", "inputs": {"upscale_model": ["16", 0], "image": ["15", 0]}},
      "18": {"class_type": "SaveImage", "inputs": {"images": ["17", 0], "filename_prefix": "flatlay/ai"}},
    }
    pid = kx.api("/prompt", {"prompt": wf, "client_id": "flatlay"}).get("prompt_id")
    if not pid: return False, "submit failed"
    t0 = time.time()
    while time.time() - t0 < 900:
        h = kx.api("/history/" + pid)
        if pid in h:
            e = h[pid]; st = e.get("status", {})
            if st.get("status_str") == "error":
                msg = ""
                for it in st.get("messages", []):
                    if isinstance(it, (list, tuple)) and len(it) > 1 and isinstance(it[1], dict):
                        msg = it[1].get("exception_message", "") or msg
                return False, "error: " + msg[:250]
            for node in e.get("outputs", {}).values():
                for img in node.get("images", []):
                    p = os.path.join(str(paths.COMFY + '/output'), img.get("subfolder", ""), img["filename"])
                    shutil.copy2(p, os.path.join(str(paths.BR + '/gen' + '/nomodel'), out))
                    return True, out
            return False, "no image"
        time.sleep(3)
    return False, "timeout"

if __name__ == "__main__":
    kx.free_vram()
    print(run())
