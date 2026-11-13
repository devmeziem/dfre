import bpy, os, math, json, sys
from mathutils import Vector

def arg(name, default):
    args = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    return args[args.index(name)+1] if name in args else default

asset=os.path.abspath(arg("--asset","presenter-lab/assets/Presenter.glb"))
out=os.path.abspath(arg("--output","output/presenter/presenter-motion-test.mp4"))
os.makedirs(os.path.dirname(out),exist_ok=True)
bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=asset)
scene=bpy.context.scene
arm=next((o for o in scene.objects if o.type=="ARMATURE"),None)
mesh=next((o for o in scene.objects if o.type=="MESH" and o.find_armature()),None)
if not arm or not mesh: raise RuntimeError("Expected skinned character mesh and armature were not found.")
# Remove the unweighted 42-vertex Icosphere helper; keep the actual skinned character.
for o in list(scene.objects):
    if o.type=="MESH" and o != mesh and not o.find_armature():
        bpy.data.objects.remove(o,do_unlink=True)
# Normalize the character to ground level using skinned mesh bounds.
deps=bpy.context.evaluated_depsgraph_get()
corners=[mesh.matrix_world @ Vector(c) for c in mesh.bound_box]
minz=min(v.z for v in corners); maxz=max(v.z for v in corners)
height=maxz-minz
for o in [arm,mesh]:
    o.location.z -= minz
# Animate the actual Mixamo rig.
pb=arm.pose.bones
def bone(name):
    return pb.get("mixamorig:"+name)
def key(name, frame, rot=None, loc=None):
    b=bone(name)
    if not b: return
    b.rotation_mode="XYZ"
    if rot is not None:
        b.rotation_euler=rot; b.keyframe_insert(data_path="rotation_euler",frame=frame,group=name)
    if loc is not None:
        b.location=loc; b.keyframe_insert(data_path="location",frame=frame,group=name)
# Base neutral pose and gentle breathing/head motion throughout 6 seconds.
frames=[1,24,48,72,96,120,145]
for f in frames:
    t=(f-1)/144*math.tau
    key("Spine2",f,rot=(0,0,0.018*math.sin(t)),loc=(0,0,0.006*math.sin(t)))
    key("Neck",f,rot=(0.025*math.sin(t*0.7),0.018*math.sin(t),0))
    key("Head",f,rot=(0.035*math.sin(t*0.7+0.4),0.025*math.sin(t),0))
# Presenter gestures: right hand opens outward, returns, then a small wave.
for f,armrot,fore in [(1,(0.05,0.0,0.10),(0,0,0)),(32,(-0.25,0.0,-0.35),(0.0,0.0,-0.22)),(58,(-0.38,0.0,-0.62),(0.0,0.0,-0.42)),(78,(-0.24,0.0,-0.35),(0.0,0.0,-0.18)),(100,(0.05,0.0,0.10),(0,0,0)),(120,(-0.30,0.0,-0.45),(0.0,0.0,-0.35)),(133,(-0.30,0.0,-0.45),(0.0,0.0,0.20)),(145,(0.05,0.0,0.10),(0,0,0))]:
    key("RightArm",f,rot=armrot); key("RightForeArm",f,rot=fore)
# Left arm gives a restrained explanatory gesture.
for f,r in [(1,(0.05,0,0.05)),(42,(-0.18,0,0.28)),(68,(-0.28,0,0.38)),(92,(-0.12,0,0.18)),(120,(0.05,0,0.05)),(145,(0.05,0,0.05))]:
    key("LeftArm",f,rot=r)
for f,r in [(1,(0,0,0)),(42,(0,0,0.18)),(68,(0,0,0.25)),(92,(0,0,0.12)),(120,(0,0,0)),(145,(0,0,0))]:
    key("LeftForeArm",f,rot=r)
if arm.animation_data and arm.animation_data.action:
    for fc in arm.animation_data.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation="BEZIER"
# Studio and portrait camera, framed to show head through upper legs.
world=scene.world or bpy.data.worlds.new("Presenter Studio"); scene.world=world; world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Color"].default_value=(0.006,0.009,0.016,1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value=0.12
mat=bpy.data.materials.new("Presenter Studio Floor"); mat.diffuse_color=(0.018,0.024,0.038,1)
mat.use_nodes=True; mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(0.018,0.024,0.038,1)
bpy.ops.mesh.primitive_plane_add(size=8,location=(0,0,-0.015)); bpy.context.object.data.materials.append(mat)
target=Vector((0,0,height*0.60))
def light(name,loc,power,size):
    bpy.ops.object.light_add(type="AREA",location=loc); l=bpy.context.object; l.name=name
    l.data.energy=power; l.data.shape="DISK"; l.data.size=size
    l.rotation_euler=(target-l.location).to_track_quat("-Z","Y").to_euler()
light("Soft_Key",(-1.8,-2.5,2.0),260,2.2); light("Soft_Fill",(1.8,-1.5,1.4),90,2.8); light("Rim",(0,1.5,1.8),180,2.0)
bpy.ops.object.camera_add(location=(0,-3.4,height*0.62)); cam=bpy.context.object
cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler(); cam.data.lens=52; scene.camera=cam
scene.render.engine="BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items.keys() else "BLENDER_EEVEE"
scene.render.resolution_x=720; scene.render.resolution_y=1280; scene.render.resolution_percentage=100
scene.render.fps=24; scene.frame_start=1; scene.frame_end=145
scene.view_settings.view_transform="AgX"; scene.view_settings.exposure=-0.5
scene.render.image_settings.file_format="FFMPEG"; scene.render.ffmpeg.format="MPEG4"; scene.render.ffmpeg.codec="H264"; scene.render.ffmpeg.constant_rate_factor="MEDIUM"; scene.render.ffmpeg.ffmpeg_preset="REALTIME"; scene.render.filepath=out
scene.camera.data.dof.use_dof=False
scene.render.image_settings.color_mode="RGB"
scene.frame_set(1)
with open("output/presenter/presenter-animation-report.json","w") as f:
 json.dump({"duration_seconds":round(145/24,2),"fps":24,"animated_bones":[b.name for b in arm.data.bones if b.name in ["mixamorig:Spine2","mixamorig:Neck","mixamorig:Head","mixamorig:RightArm","mixamorig:RightForeArm","mixamorig:LeftArm","mixamorig:LeftForeArm"]],"facial_controls":"Not present in source GLB; blinking, expressions and lip-sync are not fabricated. Requires facial mesh controls or reconstruction."},f,indent=2)
print("PRESENTER_MOTION_TEST_START",flush=True)
bpy.ops.render.render(animation=True)
print("PRESENTER_MOTION_TEST_COMPLETE",out,flush=True)
