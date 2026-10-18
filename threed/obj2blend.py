import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths
# -*- coding: utf-8 -*-
"""导入 anny_body.obj（Z-up，不做轴向换算）-> 保存 anny_posed.blend。"""
import bpy, os
OUT = str(paths.D3D + '/out')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=os.path.join(OUT, "anny_body.obj"), forward_axis='Y', up_axis='Z')
ob = [o for o in bpy.data.objects if o.type == 'MESH'][0]
bpy.context.view_layer.objects.active = ob
ob.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
from mathutils import Vector
bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
print("bbox z %.3f..%.3f  x %.3f..%.3f  rot %s" % (min(v.z for v in bb), max(v.z for v in bb),
      min(v.x for v in bb), max(v.x for v in bb), tuple(round(v,2) for v in ob.rotation_euler)))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "anny_posed.blend"))
print("saved anny_posed.blend")
