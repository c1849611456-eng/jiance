import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""B1 正视分辨率补齐：896x1152 -> 4x-UltraSharp -> 3584x4608（与其余款一致）。"""
import os, sys, time, shutil
sys.path.insert(0, str(paths.BR + '/gen'))
import kx
R2 = str(paths.R2)
src = os.path.join(R2, "B1_front.png")
shutil.copy2(src, str(paths.COMFY + '/input' + '/b1_front_lowres.png'))
wf = {
  "2": {"class_type": "LoadImage", "inputs": {"image": "b1_front_lowres.png", "upload": "image"}},
  "16": {"class_type": "UpscaleModelLoader", "inputs": {"model_name": "4x-UltraSharp.pth"}},
  "17": {"class_type": "ImageUpscaleWithModel", "inputs": {"upscale_model": ["16", 0], "image": ["2", 0]}},
  "18": {"class_type": "SaveImage", "inputs": {"images": ["17", 0], "filename_prefix": "b1up/front"}},
}
pid = kx.api("/prompt", {"prompt": wf, "client_id": "b1up"}).get("prompt_id")
t0 = time.time(); out = None
while time.time() - t0 < 600:
    h = kx.api("/history/" + pid)
    if pid in h:
        for node in h[pid].get("outputs", {}).values():
            for img in node.get("images", []):
                out = os.path.join(str(paths.COMFY + '/output'), img.get("subfolder", ""), img["filename"])
        break
    time.sleep(3)
print("upscaled:", out, flush=True)
if out:
    shutil.copy2(out, os.path.join(R2, "B1_front.png"))
    print("promoted 4x front", flush=True)
