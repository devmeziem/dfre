#!/usr/bin/env python3
"""Render a small, self-contained ice-density infographic in Blender."""
import json
import math
import os
import sys
from mathutils import Vector
import bpy


def cli_arg(flag, default=None):
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if flag in args and args.index(flag) + 1 < len(args):
        return args[args.index(flag) + 1]
    return default


seed_path = os.path.abspath(cli_arg("--seed", "learnlab/seeds/why_ice_floats.json"))
output_path = os.path.abspath(cli_arg("--output", "output/learnlab/scene-silent.mp4"))
duration = float(cli_arg("--duration", "24"))
if not 5 <= duration <= 180:
    raise SystemExit("Audio duration must be between 5 and 180 seconds")
with open(seed_path, encoding="utf-8") as seed_file:
    data = json.load(seed_file)
project = data["project"]
width = int(project.get("width", 720))
height = int(project.get("height", 1280))
fps = int(project.get("fps", 24))
if width < 360 or height < 640 or width > 1920 or height > 1920 or fps not in (24, 25, 30):
    raise SystemExit("Unsupported dimensions or frame rate in seed")
last_frame = max(2, math.ceil(duration * fps))

# Start from a clean file and use the Eevee engine available in this Blender build.
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
engine_keys = scene.render.bl_rna.properties["engine"].enum_items.keys()
for candidate in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    if candidate in engine_keys:
        scene.render.engine = candidate
        break
scene.render.resolution_x = width
scene.render.resolution_y = height
scene.render.resolution_percentage = 100
eevee_settings = getattr(scene, "eevee", None)
if eevee_settings is not None and hasattr(eevee_settings, "taa_render_samples"):
    eevee_settings.taa_render_samples = 8
scene.render.fps = fps
scene.frame_start = 1
scene.frame_end = last_frame
scene.render.image_settings.file_format = "FFMPEG"
scene.render.ffmpeg.format = "MPEG4"
scene.render.ffmpeg.codec = "H264"
scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
scene.render.ffmpeg.ffmpeg_preset = "REALTIME"
scene.render.filepath = output_path
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "Medium High Contrast"
scene.world.color = (0.008, 0.016, 0.045)


def material(name, rgba, metallic=0.0, roughness=0.55, emission=None, strength=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*rgba, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*rgba, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission and "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1)
        bsdf.inputs["Emission Strength"].default_value = strength
    return mat


def cube(name, location, dimensions, mat, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        bevel_mod = obj.modifiers.new("Soft readable edges", "BEVEL")
        bevel_mod.width = bevel
        bevel_mod.segments = 3
        obj.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
    obj.data.materials.append(mat)
    return obj


def sphere(name, location, radius, mat, segments=20):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=12, radius=radius, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    for face in obj.data.polygons:
        face.use_smooth = True
    return obj


def label(text, location, size, mat, align="CENTER"):
    curve = bpy.data.curves.new("Label_" + text[:18], "FONT")
    curve.body = text
    curve.size = size
    curve.align_x = align
    curve.extrude = 0.001
    obj = bpy.data.objects.new("Label_" + text[:18], curve)
    scene.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (math.radians(90), 0, 0)
    obj.data.materials.append(mat)
    return obj


def rod(name, a, b, radius, mat):
    start, end = Vector(a), Vector(b)
    diff = end - start
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=radius, depth=diff.length, location=(start + end) / 2)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_euler = diff.to_track_quat("Z", "Y").to_euler()
    obj.data.materials.append(mat)
    return obj


navy = material("Deep ocean background", (0.012, 0.028, 0.075), roughness=0.9)
white = material("Warm white type", (0.92, 0.96, 1.0), emission=(0.82, 0.9, 1.0), strength=0.45)
cyan = material("Ice cyan", (0.32, 0.82, 1.0), metallic=0.08, roughness=0.22, emission=(0.08, 0.38, 0.65), strength=0.28)
water = material("Blue water", (0.035, 0.28, 0.66), metallic=0.05, roughness=0.32, emission=(0.01, 0.09, 0.32), strength=0.28)
waterline = material("Waterline", (0.12, 0.78, 1.0), emission=(0.08, 0.55, 1.0), strength=1.2)
red = material("Oxygen red", (0.96, 0.25, 0.22), roughness=0.38)
soft_white = material("Hydrogen white", (0.92, 0.96, 1.0), roughness=0.42)
bond = material("Hydrogen bonds", (0.35, 0.74, 0.96), emission=(0.12, 0.35, 0.7), strength=0.4)

# A large flat backdrop keeps every frame legible on mobile.
cube("BACKGROUND", (0, 4.8, 6.5), (15, 0.2, 18), navy)
label("WHY DOES ICE FLOAT?", (0, -0.35, 12.65), 0.54, white)
label("THE MOLECULES MAKE THE DIFFERENCE", (0, -0.35, 11.88), 0.22, cyan)

# Tank: its side rails, bottom and flat water slab make the floating relation visible.
cube("TANK_BOTTOM", (0, 0.4, 5.22), (4.8, 0.48, 0.18), cyan, 0.05)
cube("TANK_LEFT_WALL", (-2.31, 0.4, 6.85), (0.18, 0.48, 3.25), cyan, 0.05)
cube("TANK_RIGHT_WALL", (2.31, 0.4, 6.85), (0.18, 0.48, 3.25), cyan, 0.05)
cube("WATER", (0, 0.20, 6.14), (4.42, 0.32, 1.65), water, 0.04)
cube("WATER_SURFACE", (0, -0.12, 6.97), (4.34, 0.08, 0.045), waterline, 0.015)
label("LIQUID WATER", (0, -0.43, 5.48), 0.25, white)

ice = cube("FLOATING_ICE_CUBE", (0, -0.33, 7.42), (1.35, 0.92, 1.15), cyan, 0.13)
# Slight bobbing is an illustration, not a measured physical simulation.
for frame, z in ((1, 7.39), (last_frame // 2, 7.48), (last_frame, 7.39)):
    ice.location.z = z
    ice.keyframe_insert(data_path="location", frame=frame)

label("LESS DENSE = FLOATS", (0, -0.48, 8.42), 0.27, white)

# Lower panel compares crowded liquid molecules with an open ice lattice.
label("LIQUID", (-1.55, -0.45, 4.24), 0.29, cyan)
label("CLOSE + MOVING", (-1.55, -0.45, 3.82), 0.17, white)
label("ICE", (1.55, -0.45, 4.24), 0.29, cyan)
label("OPEN CRYSTAL", (1.55, -0.45, 3.82), 0.17, white)

liquid_positions = [(-2.45, 2.9), (-1.60, 2.9), (-0.78, 2.9), (-2.05, 3.35), (-1.18, 3.35), (-2.45, 3.78), (-1.60, 3.78), (-0.78, 3.78)]
for idx, (x, z) in enumerate(liquid_positions):
    o = sphere(f"LIQUID_O_{idx}", (x, -0.18, z), 0.14, red)
    sphere(f"LIQUID_HA_{idx}", (x - 0.16, -0.23, z + 0.13), 0.065, soft_white, 14)
    sphere(f"LIQUID_HB_{idx}", (x + 0.16, -0.23, z + 0.13), 0.065, soft_white, 14)
    if idx % 2 == 0:
        base = o.location.copy()
        o.location.x = base.x + 0.08
        o.keyframe_insert(data_path="location", frame=1)
        o.location.x = base.x - 0.08
        o.keyframe_insert(data_path="location", frame=max(2, last_frame // 2))
        o.location = base
        o.keyframe_insert(data_path="location", frame=last_frame)

ice_points = [
    (0.55, 3.12), (1.28, 3.56), (2.01, 3.12),
    (1.28, 2.68), (0.55, 2.24), (1.28, 1.80), (2.01, 2.24), (2.01, 4.00)
]
for idx, (x, z) in enumerate(ice_points):
    sphere(f"ICE_O_{idx}", (x, -0.2, z), 0.14, red)
    if idx % 2 == 0 and idx + 1 < len(ice_points):
        next_x, next_z = ice_points[idx + 1]
        rod(f"ICE_BOND_{idx}", (x, -0.18, z), (next_x, -0.18, next_z), 0.025, bond)
# Cross-links clarify that ice has an ordered, open arrangement.
for first, second in ((0, 3), (1, 3), (1, 6), (2, 6), (3, 4), (3, 6), (6, 7)):
    a, b = ice_points[first], ice_points[second]
    rod(f"LATTICE_{first}_{second}", (a[0], -0.18, a[1]), (b[0], -0.18, b[1]), 0.018, bond)

# Soft lighting, with no external assets or textures.
bpy.ops.object.light_add(type="AREA", location=(-5, -7, 12))
key = bpy.context.object
key.data.energy = 1250
key.data.shape = "DISK"
key.data.size = 7
key.rotation_euler = (Vector((0, 0, 6)) - key.location).to_track_quat("-Z", "Y").to_euler()
bpy.ops.object.light_add(type="AREA", location=(4, -3, 7))
fill = bpy.context.object
fill.data.energy = 650
fill.data.size = 5
fill.rotation_euler = (Vector((0, 0, 6)) - fill.location).to_track_quat("-Z", "Y").to_euler()

bpy.ops.object.camera_add(location=(0, -24, 6.5))
camera = bpy.context.object
camera.name = "LEARNLAB_CAMERA"
camera.rotation_euler = (Vector((0, 0, 6.5)) - camera.location).to_track_quat("-Z", "Y").to_euler()
camera.data.type = "ORTHO"
camera.data.sensor_fit = "VERTICAL"
camera.data.ortho_scale = 14
scene.camera = camera
scene.render.image_settings.color_mode = "RGB"
scene.render.ffmpeg.audio_codec = "AAC"
scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
scene.render.ffmpeg.ffmpeg_preset = "REALTIME"
os.makedirs(os.path.dirname(output_path), exist_ok=True)
scene.frame_set(1)
print("LEARNLAB_RENDER_START", json.dumps({"duration_seconds": duration, "frames": last_frame, "resolution": [width, height]}), flush=True)
bpy.ops.render.render(animation=True)
print("LEARNLAB_RENDER_COMPLETE", output_path, flush=True)
