# Third-Party Notices

This repository ships **no model weights** and **no third-party source code**.
All third-party components are referenced as external dependencies that you
must install yourself.

| Component | What we use | License (verify before use) |
|---|---|---|
| ComfyUI | local workflow server, driven over its HTTP API | GPL-3.0 — do not vendor its source into this repo |
| FLUX.1 Kontext [dev] | targeted image editing | Non-commercial license — outputs may carry the same restriction |
| Stable Diffusion XL base + Juggernaut-XL v9 | stylization / view rendering | OpenRAIL++-M / model-card terms |
| ControlNet (canny/depth/openpose, SDXL) | shape/pose conditioning | verify per checkpoint |
| IP-Adapter (h94) | appearance/style reference | Apache-2.0 (verify) |
| DepthAnythingV2 | depth preprocessor | Apache-2.0 (verify) |
| 4x-UltraSharp | upscaling | verify (open-rail style, non-training) |
| RMBG-1.4 (BRIA) | background removal | CC BY-NC — non-commercial |
| insightface buffalo_l | face similarity QA | non-commercial research (weights) |
| Anny parametric body | 3D garment shells | Apache-2.0 (verify) |
| Blender (bpy) | 3D scene/rendering | GPL-2.0-or-later — used as external application, not vendored |

The pipeline code in this repository is original and licensed MIT.
Generated demo images are not redistributed here; generate your own with
models you are licensed to use.
