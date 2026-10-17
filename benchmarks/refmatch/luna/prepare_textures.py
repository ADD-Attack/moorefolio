#!/usr/bin/env python3
"""Neutralize Exercise-2 blue albedo toward the reference steel palette."""
import bpy
import numpy as np
from pathlib import Path
root=Path(__file__).resolve().parent
src=root/'base-textures'/'snake_albedo.png'
out=root/'textures'/'snake_albedo.png'
img=bpy.data.images.load(str(src), check_existing=False)
img.colorspace_settings.name='Non-Color'
a=np.empty(len(img.pixels),dtype=np.float32); img.pixels.foreach_get(a); a=a.reshape((-1,4))
rgb=a[:,:3]; gray=rgb.mean(axis=1,keepdims=True)
rgb[:]=np.clip((0.25*rgb+0.75*gray)*1.70+0.08,0.0,1.0)
a[:,:3]=rgb; img.pixels.foreach_set(a.ravel()); img.filepath=str(out); img.file_format='PNG'; img.save()
print('TEXTURE_NEUTRALIZED',src,'->',out,img.size[:])
