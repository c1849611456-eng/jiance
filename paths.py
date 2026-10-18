# -*- coding: utf-8 -*-
"""Central path config. Override any of these for your machine."""
import os

ROOT    = os.environ.get("ASP_ROOT", r".")
BR      = os.environ.get("ASP_BRIDGE", os.path.join(ROOT, "_bridge"))       # working bridge dir
DELIVER = os.environ.get("ASP_DELIVER", os.path.join(ROOT, "delivery"))    # delivery folder
RAW     = os.environ.get("ASP_RAW", os.path.join(DELIVER, "renders_raw"))  # raw renders
R2      = os.environ.get("ASP_R2", os.path.join(BR, "renders_v2"))         # promoted sources
OUT     = os.environ.get("ASP_OUT", os.path.join(BR, "out"))               # build output
COMFY   = os.environ.get("ASP_COMFY", r"D:\ComfyUI")                      # ComfyUI install
PY      = os.environ.get("ASP_PY", os.path.join(COMFY, "venv", "Scripts", "python.exe"))
D3D     = os.environ.get("ASP_D3D", os.path.join(ROOT, "threed_work"))     # Blender workspace
API     = "http://127.0.0.1:8188"                                          # ComfyUI HTTP API
