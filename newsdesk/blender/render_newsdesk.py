import bpy, math, json, os, sys, argparse
from mathutils import Vector

av = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
p = argparse.ArgumentParser()
p.add_argument("--seed", required=True)
p.add_argument("--output", required=True)
A = p.parse_args(av)

seed = json.load(open(A.seed))
cfg = seed["project"]
FPS = int(cfg.get("fps", 24))
W = int(cfg.get("width", 1280))
H = int(cfg.get("height", 720))
LAST = int(FPS * float(cfg.get("duration_seconds", 12)))

def load_json(path):
    # paths relative to repo root when run from Actions checkout
    return json.load(open(path))

char = load_json(seed["character"])
env = load_json(seed["environment"])
headline = seed.get("headline", "9jaBeacon Desk")
ticker = seed.get("ticker", "9jaBeacon · www.9jabeacon.name.ng")
boards_cfg = seed.get("boards", [{"label": "A"}, {"label": "B"}, {"label": "C"}])

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

def mat(n, c, r=0.55):
    m = bpy.data.materials.new(n)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*c, 1)
    bsdf.inputs["Roughness"].default_value = r
    return m

def cube(n, loc, dim, m, b=0.04):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = n
    o.dimensions = dim
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    mod = o.modifiers.new("Bevel", "BEVEL")
    mod.width = b
    mod.segments = 2
    o.data.materials.append(m)
    return o

def ball(n, loc, sc, m):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, radius=1, location=loc)
    o = bpy.context.object
    o.name = n
    o.scale = sc
    o.data.materials.append(m)
    for f in o.data.polygons:
        f.use_smooth = True
    return o

def cyl(n, loc, r, depth, m):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=r, depth=depth, location=loc)
    o = bpy.context.object
    o.name = n
    o.data.materials.append(m)
    return o

def aim(o, t):
    o.rotation_euler = (Vector(t) - o.location).to_track_quat("-Z", "Y").to_euler()

# Materials from env / character
m_wall = mat("Wall", tuple(env["wall"]))
m_accent = mat("Accent", tuple(env["accent"]), 0.35)
m_desk = mat("Desk", tuple(env["desk"]), 0.4)
m_floor = mat("Floor", (0.08, 0.09, 0.11), 0.7)
m_skin = mat("Skin", tuple(char["skin"]), 0.45)
m_outfit = mat("Outfit", tuple(char["outfit"]), 0.5)
m_ticker = mat("Ticker", tuple(env["ticker"]["bg"]), 0.3)
m_board_frame = mat("BoardFrame", (0.15, 0.16, 0.18), 0.4)
m_screen = mat("Screen", (0.05, 0.12, 0.18), 0.2)

# Room
cube("FLOOR", (0, 0, -0.05), (12, 8, 0.1), m_floor)
cube("BACK_WALL", (0, 3.2, 2.2), (12, 0.2, 4.5), m_wall)
cube("LEFT_WALL", (-5.8, 0.5, 2.2), (0.2, 6, 4.5), m_wall)
cube("RIGHT_WALL", (5.8, 0.5, 2.2), (0.2, 6, 4.5), m_wall)
# Accent band behind presenter
cube("ACCENT_BAND", (0, 3.05, 2.6), (8, 0.08, 0.35), m_accent)

# Desk (covers lower body)
cube("DESK_TOP", (0, -0.35, 0.92), (3.6, 1.1, 0.08), m_desk, 0.03)
cube("DESK_FRONT", (0, -0.85, 0.45), (3.5, 0.08, 0.9), m_desk, 0.02)
# Logo plate on desk front
cube("DESK_LOGO_PLATE", (0, -0.90, 0.55), (1.4, 0.04, 0.28), m_accent, 0.02)

# Three boards behind presenter (left, center-back, right)
board_positions = [(-2.4, 2.7, 2.0), (0.0, 2.75, 2.15), (2.4, 2.7, 2.0)]
for i, (bx, by, bz) in enumerate(board_positions[: int(env.get("boards", 3))]):
    label = boards_cfg[i]["label"] if i < len(boards_cfg) else f"B{i+1}"
    col = boards_cfg[i].get("color", [0.1, 0.3, 0.4]) if i < len(boards_cfg) else [0.1, 0.3, 0.4]
    cube(f"BOARD_FRAME_{i}", (bx, by, bz), (1.7, 0.08, 1.15), m_board_frame, 0.02)
    m_panel = mat(f"Panel_{i}", tuple(col), 0.25)
    cube(f"BOARD_PANEL_{i}", (bx, by - 0.06, bz), (1.55, 0.04, 1.0), m_panel, 0.01)

# Red ticker bar (lower third strip in 3D space, front of desk area)
cube("TICKER_BAR", (0, -1.35, 0.22), (7.5, 0.12, 0.28), m_ticker, 0.01)
# Headline bar (slightly above ticker)
m_head = mat("HeadlineBar", (0.12, 0.12, 0.14), 0.35)
cube("HEADLINE_BAR", (0, -1.25, 0.48), (5.5, 0.1, 0.22), m_head, 0.01)

# Presenter (line stickman seated behind desk)
head = ball("PRESENTER_HEAD", (0, 0.15, 1.95), (0.28, 0.26, 0.30), m_skin)
torso = cyl("PRESENTER_TORSO", (0, 0.15, 1.35), 0.045, 0.55, m_outfit)
# Simple arms on desk
cyl("ARM_L", (-0.35, -0.15, 1.05), 0.03, 0.55, m_skin)
bpy.context.object.rotation_euler = (1.2, 0, 0.4)
cyl("ARM_R", (0.35, -0.15, 1.05), 0.03, 0.55, m_skin)
bpy.context.object.rotation_euler = (1.2, 0, -0.4)
# Subtle head nod animation
for f in range(1, LAST + 1, 2):
    t = f / max(1, LAST)
    z = 1.95 + 0.02 * math.sin(t * math.pi * 4)
    head.location = (0, 0.15, z)
    head.keyframe_insert(data_path="location", frame=f)

# Camera — slow push-in (broadcast style)
bpy.ops.object.camera_add(location=(0, -4.8, 1.55))
cam = bpy.context.object
cam.name = "NEWSDESK_CAM"
cam.data.lens = 40
bpy.context.scene.camera = cam

def camkey(f, loc, target, lens):
    cam.location = loc
    aim(cam, target)
    cam.data.lens = lens
    cam.keyframe_insert(data_path="location", frame=f)
    cam.keyframe_insert(data_path="rotation_euler", frame=f)
    cam.data.keyframe_insert(data_path="lens", frame=f)

camkey(1, (0, -5.2, 1.65), (0, 0.2, 1.5), 38)
camkey(int(LAST * 0.45), (0.15, -4.4, 1.5), (0, 0.2, 1.55), 42)
camkey(LAST, (-0.1, -3.9, 1.45), (0, 0.15, 1.6), 48)

# Lights
bpy.ops.object.light_add(type="AREA", location=(-2.5, -2.5, 4))
L = bpy.context.object
L.data.energy = 900
L.data.size = 5
aim(L, (0, 0.2, 1.4))
bpy.ops.object.light_add(type="AREA", location=(3, 1, 3.5))
L2 = bpy.context.object
L2.data.energy = 500
L2.data.size = 4
aim(L2, (0, 0.2, 1.4))
bpy.ops.object.light_add(type="AREA", location=(0, 2.5, 3))
L3 = bpy.context.object
L3.data.energy = 350
L3.data.size = 3

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = LAST
scene.render.fps = FPS
scene.render.engine = "BLENDER_EEVEE"
scene.eevee.taa_render_samples = 16
scene.render.resolution_x = W
scene.render.resolution_y = H
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "FFMPEG"
scene.render.ffmpeg.format = "MPEG4"
scene.render.ffmpeg.codec = "H264"
scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
scene.render.ffmpeg.ffmpeg_preset = "REALTIME"
scene.render.filepath = os.path.abspath(A.output)
scene.view_settings.view_transform = "Standard"
scene.world.color = (0.04, 0.05, 0.07)

for obj in scene.objects:
    if obj.animation_data and obj.animation_data.action:
        for fc in obj.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "BEZIER"

os.makedirs(os.path.dirname(os.path.abspath(A.output)) or ".", exist_ok=True)
print("NEWSDESK_RENDER_START", json.dumps({"frames": LAST, "character": char["id"], "env": env["id"], "headline": headline[:80]}), flush=True)
bpy.ops.render.render(animation=True)
print("NEWSDESK_RENDER_COMPLETE", A.output, flush=True)
