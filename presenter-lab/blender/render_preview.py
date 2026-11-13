import bpy, os, json, math, sys
from mathutils import Vector

def arg(name, default=None):
    args = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    return args[args.index(name)+1] if name in args else default

asset = os.path.abspath(arg("--asset", "presenter-lab/assets/Presenter.glb"))
output = os.path.abspath(arg("--output", "output/presenter-preview.mp4"))
report = os.path.abspath(arg("--report", "output/presenter-report.json"))
if not os.path.isfile(asset):
    raise SystemExit("Missing character asset: " + asset + ". Upload Presenter.glb to presenter-lab/assets/Presenter.glb.")

# Clean factory scene, then import the supplied GLB.
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=asset)
imported = list(bpy.context.scene.objects)
meshes = [o for o in imported if o.type == "MESH"]
armatures = [o for o in imported if o.type == "ARMATURE"]
if not meshes:
    raise SystemExit("The GLB imported, but Blender found no mesh objects.")

# Calculate bounds in world space, then parent imported objects to a turntable
# while preserving their imported transforms.
points = []
for obj in meshes:
    for corner in obj.bound_box:
        points.append(obj.matrix_world @ Vector(corner))
mins = [min(p[i] for p in points) for i in range(3)]
maxs = [max(p[i] for p in points) for i in range(3)]
center = Vector(tuple((mins[i]+maxs[i])*0.5 for i in range(3)))
height = max(maxs[2]-mins[2], 0.1)
width = max(maxs[0]-mins[0], 0.1)
depth = max(maxs[1]-mins[1], 0.1)

pivot = bpy.data.objects.new("PRESENTER_TURNTABLE_ROOT", None)
bpy.context.collection.objects.link(pivot)
pivot.location = center
for obj in imported:
    world = obj.matrix_world.copy()
    obj.parent = pivot
    obj.matrix_world = world
pivot.rotation_euler.z = 0.0
pivot.keyframe_insert(data_path="rotation_euler", frame=1)
pivot.rotation_euler.z = math.tau
pivot.keyframe_insert(data_path="rotation_euler", frame=145)
if pivot.animation_data and pivot.animation_data.action:
    for fc in pivot.animation_data.action.fcurves:
        for key in fc.keyframe_points:
            key.interpolation = "LINEAR"

# Neutral dark studio setup.
def principled(name, color, roughness=0.7, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat

floor_mat = principled("Studio floor", (0.025, 0.035, 0.055), 0.82)
bpy.ops.mesh.primitive_plane_add(size=max(height*8, 8), location=(center.x, center.y, mins[2]-0.035))
floor = bpy.context.object
floor.name = "STUDIO_FLOOR"
floor.data.materials.append(floor_mat)

world = bpy.context.scene.world or bpy.data.worlds.new("Presenter Studio")
bpy.context.scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.012, 0.018, 0.03, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.35

def area(name, loc, energy, size, target):
    bpy.ops.object.light_add(type="AREA", location=loc)
    light = bpy.context.object
    light.name = name
    light.data.energy = energy
    light.data.shape = "DISK"
    light.data.size = size
    light.rotation_euler = (Vector(target)-light.location).to_track_quat("-Z", "Y").to_euler()

target = (center.x, center.y, center.z)
area("KEY_SOFTBOX", (center.x-height*1.2, center.y-height*1.8, center.z+height*1.1), 1100, height*1.0, target)
area("FILL_SOFTBOX", (center.x+height*1.5, center.y-height*1.0, center.z+height*0.25), 700, height*1.2, target)
area("RIM_LIGHT", (center.x, center.y+height*1.2, center.z+height*0.9), 1250, height*0.8, target)

bpy.ops.object.camera_add(location=(center.x, center.y-height*2.8, center.z+height*0.06))
camera = bpy.context.object
camera.name = "PRESENTER_PREVIEW_CAMERA"
camera.rotation_euler = (Vector(target)-camera.location).to_track_quat("-Z", "Y").to_euler()
camera.data.lens = 50
bpy.context.scene.camera = camera

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 145
scene.render.fps = 24
scene.render.resolution_x = 720
scene.render.resolution_y = 1280
scene.render.resolution_percentage = 100
try:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
except Exception:
    scene.render.engine = "BLENDER_EEVEE"
if hasattr(scene, "eevee"):
    scene.eevee.taa_render_samples = 16
scene.render.image_settings.file_format = "FFMPEG"
scene.render.ffmpeg.format = "MPEG4"
scene.render.ffmpeg.codec = "H264"
scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
scene.render.ffmpeg.ffmpeg_preset = "REALTIME"
scene.render.filepath = output
scene.view_settings.view_transform = "Standard"
scene.render.image_settings.color_mode = "RGB"
scene.camera.data.dof.use_dof = False
os.makedirs(os.path.dirname(output), exist_ok=True)
os.makedirs(os.path.dirname(report), exist_ok=True)

summary = {
    "asset": os.path.basename(asset),
    "mesh_objects": len(meshes),
    "armature_objects": len(armatures),
    "mesh_dimensions_estimate": [round(width, 4), round(depth, 4), round(height, 4)],
    "materials": len({m.name for obj in meshes for m in obj.data.materials if m}),
    "frames": 145,
    "fps": 24,
    "resolution": [720, 1280],
    "note": "Turntable preview only; no body clips or facial morphs are generated by this test."
}
with open(report, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)
print("PRESENTER_MODEL_REPORT", json.dumps(summary), flush=True)
bpy.ops.render.render(animation=True)
print("PRESENTER_PREVIEW_COMPLETE", output, flush=True)
