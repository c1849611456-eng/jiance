import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""单步 Kontext 视角编辑：一张源图 + 一条指令 -> 一张新视角图（896x1152 -> 4x 放大）。"""
import json, os, shutil, sys, time
import urllib.request as U
from PIL import Image

COMFY = str(paths.COMFY)
COMFY_INPUT = os.path.join(COMFY, "input")
HOST = "http://127.0.0.1:8188"
UPSCALE_MODEL = "4x-UltraSharp.pth"

KEEP = (", keep everything else identical: the same woman with the same face and hair, "
        "the same body pose and the same limb positions, the same swimsuit with the same design "
        "details, seams and colour, the same studio background and lighting, the same framing, "
        "scale and image quality. Photorealistic high-end fashion catalogue photograph, 300 dpi.")

INSTR = {
  "tq45":  "Rotate the camera 45 degrees around the model only, so she is seen from a three-quarter angle: we now see one side of her body and her face is turned partly away from the camera",
  "tq45b": "Change the camera angle to a 45-degree three-quarter view (camera moved to her left side by 45 degrees, staying at the same height and distance)",
  "side90":"Rotate the camera 90 degrees to a strict full side profile view: her nose and chest point to the left edge of the frame, only one arm is visible, the legs overlap in profile",
  "back180":"Turn the model around 180 degrees so she is seen from behind: the back of her head and her back face the camera, the front of the garment is hidden",
  "bottom":"Move the camera down to a low angle about 40 degrees below her waist, looking up at the model from below: the camera sees the underside of her chin and the leg openings of the swimsuit from underneath",
  "low15": "Lower the camera to a low angle, about 20 degrees below eye level, looking slightly up at the model; keep the same distance and lens",
}

def api(path, payload=None):
    url = HOST + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = U.Request(url, data=data, method="POST" if data else "GET")
    if data: req.add_header("Content-Type", "application/json")
    with U.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())

def free_vram():
    try:
        api("/free", {"unload_models": True, "free_memory": True}); time.sleep(2)
    except Exception as e:
        print("  free_vram warn:", e)

def run(src, instr, out_png, seed=777, guidance=3.0, steps=20):
    im = Image.open(src).convert("RGB")
    im.thumbnail((1024, 1024))
    small_path = os.path.join(COMFY_INPUT, "kx_src.png")
    im.resize((896, 1152), Image.LANCZOS).save(small_path)
    wf = {
      "1": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": "flux1-kontext-dev-Q4_K_S.gguf"}},
      "2": {"class_type": "DualCLIPLoaderGGUF", "inputs": {"clip_name1": "t5-v1_1-xxl-encoder-Q5_K_M.gguf",
                                                           "clip_name2": "clip_l.safetensors", "type": "flux"}},
      "3": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
      "6": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": ""}},
      "7": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": instr}},
      "20": {"class_type": "LoadImage", "inputs": {"image": "kx_src.png", "upload": "image"}},
      "21": {"class_type": "VAEEncode", "inputs": {"pixels": ["20", 0], "vae": ["3", 0]}},
      "22": {"class_type": "ReferenceLatent", "inputs": {"conditioning": ["7", 0], "latent": ["21", 0]}},
      "9": {"class_type": "FluxGuidance", "inputs": {"conditioning": ["22", 0], "guidance": guidance}},
      "10": {"class_type": "KSampler", "inputs": {"model": ["1", 0], "seed": seed, "steps": steps, "cfg": 1.0,
              "sampler_name": "euler", "scheduler": "simple", "positive": ["9", 0], "negative": ["6", 0],
              "latent_image": ["21", 0], "denoise": 1.0}},
      "11": {"class_type": "VAEDecode", "inputs": {"samples": ["10", 0], "vae": ["3", 0]}},
      "12": {"class_type": "UpscaleModelLoader", "inputs": {"model_name": UPSCALE_MODEL}},
      "13": {"class_type": "ImageUpscaleWithModel", "inputs": {"upscale_model": ["12", 0], "image": ["11", 0]}},
      "14": {"class_type": "SaveImage", "inputs": {"images": ["13", 0], "filename_prefix": "kx/out"}},
    }
    pid = api("/prompt", {"prompt": wf, "client_id": "kx"}).get("prompt_id")
    if not pid: return False, "submit failed"
    t0 = time.time()
    while time.time() - t0 < 1800:
        h = api("/history/" + pid)
        if pid in h:
            e = h[pid]
            st = e.get("status", {})
            if st.get("status_str") == "error":
                msg = ""
                for it in st.get("messages", []):
                    if isinstance(it, (list, tuple)) and len(it) > 1 and isinstance(it[1], dict):
                        msg = it[1].get("exception_message", "") or msg
                return False, "error: " + msg[:200]
            outs = e.get("outputs", {})
            for node in outs.values():
                for img in node.get("images", []):
                    p = os.path.join(COMFY, "output", img.get("subfolder", ""), img["filename"])
                    shutil.copy2(p, out_png)
                    return True, out_png
            return False, "no image"
        time.sleep(4)
    return False, "timeout"

def run2(src1, src2, instr, out_png, seed=777, guidance=3.0, steps=20):
    """双参考图 Kontext：src1 提供姿态/服装/背景，src2 提供人物身份。"""
    im1 = Image.open(src1).convert("RGB"); im1.thumbnail((1024, 1024))
    im2 = Image.open(src2).convert("RGB"); im2.thumbnail((1024, 1024))
    p1 = os.path.join(COMFY_INPUT, "kx_ref1.png"); p2 = os.path.join(COMFY_INPUT, "kx_ref2.png")
    im1.resize((896, 1152), Image.LANCZOS).save(p1)
    im2.resize((896, 1152), Image.LANCZOS).save(p2)
    wf = {
      "1": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": "flux1-kontext-dev-Q4_K_S.gguf"}},
      "2": {"class_type": "DualCLIPLoaderGGUF", "inputs": {"clip_name1": "t5-v1_1-xxl-encoder-Q5_K_M.gguf",
                                                           "clip_name2": "clip_l.safetensors", "type": "flux"}},
      "3": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
      "6": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": ""}},
      "7": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["2", 0], "text": instr}},
      "20": {"class_type": "LoadImage", "inputs": {"image": "kx_ref1.png", "upload": "image"}},
      "21": {"class_type": "VAEEncode", "inputs": {"pixels": ["20", 0], "vae": ["3", 0]}},
      "30": {"class_type": "LoadImage", "inputs": {"image": "kx_ref2.png", "upload": "image"}},
      "31": {"class_type": "VAEEncode", "inputs": {"pixels": ["30", 0], "vae": ["3", 0]}},
      "22": {"class_type": "ReferenceLatent", "inputs": {"conditioning": ["7", 0], "latent": ["21", 0]}},
      "23": {"class_type": "ReferenceLatent", "inputs": {"conditioning": ["22", 0], "latent": ["31", 0]}},
      "9": {"class_type": "FluxGuidance", "inputs": {"conditioning": ["23", 0], "guidance": guidance}},
      "10": {"class_type": "KSampler", "inputs": {"model": ["1", 0], "seed": seed, "steps": steps, "cfg": 1.0,
              "sampler_name": "euler", "scheduler": "simple", "positive": ["9", 0], "negative": ["6", 0],
              "latent_image": ["21", 0], "denoise": 1.0}},
      "11": {"class_type": "VAEDecode", "inputs": {"samples": ["10", 0], "vae": ["3", 0]}},
      "12": {"class_type": "UpscaleModelLoader", "inputs": {"model_name": UPSCALE_MODEL}},
      "13": {"class_type": "ImageUpscaleWithModel", "inputs": {"upscale_model": ["12", 0], "image": ["11", 0]}},
      "14": {"class_type": "SaveImage", "inputs": {"images": ["13", 0], "filename_prefix": "kx/out2"}},
    }
    pid = api("/prompt", {"prompt": wf, "client_id": "kx2"}).get("prompt_id")
    if not pid: return False, "submit failed"
    t0 = time.time()
    while time.time() - t0 < 1800:
        h = api("/history/" + pid)
        if pid in h:
            e = h[pid]
            st = e.get("status", {})
            if st.get("status_str") == "error":
                msg = ""
                for it in st.get("messages", []):
                    if isinstance(it, (list, tuple)) and len(it) > 1 and isinstance(it[1], dict):
                        msg = it[1].get("exception_message", "") or msg
                return False, "error: " + msg[:200]
            for node in e.get("outputs", {}).values():
                for img in node.get("images", []):
                    p = os.path.join(COMFY, "output", img.get("subfolder", ""), img["filename"])
                    shutil.copy2(p, out_png); return True, out_png
            return False, "no image"
        time.sleep(4)
    return False, "timeout"


if __name__ == "__main__":
    src, key, out = sys.argv[1], sys.argv[2], sys.argv[3]
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 777
    g = float(sys.argv[5]) if len(sys.argv) > 5 else 3.0
    instr = INSTR.get(key, key) + KEEP
    free_vram()
    t = time.time()
    ok, note = run(src, instr, out, seed=seed, guidance=g)
    print(("OK " if ok else "FAIL ") + note + "  %.0fs" % (time.time() - t))
