import bpy, os, json, math
from mathutils import Vector

ASSET="presenter-lab/assets/Presenter.glb"
OUT="output/presenter"
os.makedirs(OUT,exist_ok=True)
bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=ASSET)
scene=bpy.context.scene
arm=next((o for o in scene.objects if o.type=="ARMATURE"),None)
mesh=next((o for o in scene.objects if o.type=="MESH" and o.find_armature()),None)
if arm is None or mesh is None: raise RuntimeError("Presenter skinned mesh/armature not found")
for o in list(scene.objects):
    if o.type=="MESH" and o!=mesh and not o.find_armature(): bpy.data.objects.remove(o,do_unlink=True)
# Face-space bounds from head-weighted vertices. Diagnostic render confirms the face looks toward -Y; front mask is measured from the frontmost head vertices.
head_group=mesh.vertex_groups.get("mixamorig:Head")
if head_group is None: raise RuntimeError("Head vertex group missing")
head_index=head_group.index
verts=mesh.data.vertices
world=[mesh.matrix_world @ v.co for v in verts]
face=[(i,p) for i,(v,p) in enumerate(zip(verts,world)) if any(g.group==head_index and g.weight>0.15 for g in v.groups)]
if not face: raise RuntimeError("No head-weighted vertices")
front_y=min(p.y for i,p in face)
# Existing face is sculpted/textured into the original mesh; create non-destructive morph controls on that mesh.
if mesh.data.shape_keys:
    bpy.ops.object.select_all(action="DESELECT"); mesh.select_set(True); bpy.context.view_layer.objects.active=mesh
    basis=mesh.data.shape_keys.key_blocks.get("Basis")
    if basis is None: raise RuntimeError("Existing shape keys lack Basis")
else:
    bpy.ops.object.select_all(action="DESELECT"); mesh.select_set(True); bpy.context.view_layer.objects.active=mesh
    mesh.shape_key_add(name="Basis",from_mix=False)
keys={}
for name in ("Blink_L","Blink_R","Smile","Mouth_Open","Brow_Raise"):
    keys[name]=mesh.shape_key_add(name=name,from_mix=False)
inv=mesh.matrix_world.inverted().to_3x3()
def gauss(x,z,cx,cz,sx,sz):
    return math.exp(-0.5*((x-cx)/sx)**2-0.5*((z-cz)/sz)**2)
# Coordinates are measured from the actual Presenter head bounds in the diagnostic render.
for i,(v,p) in enumerate(zip(verts,world)):
    if not any(g.group==head_index and g.weight>0.15 for g in v.groups): continue
    x,y,z=p.x,p.y,p.z
    front=max(0.0,min(1.0,(front_y+0.035-y)/0.035))
    if front<=0: continue
    # Eye patches: gently compress vertical eye geometry to create blink morphs.
    for side,cx,keyname in (("L",-0.025,"Blink_L"),("R",0.025,"Blink_R")):
        w=gauss(x,z,cx,0.907,0.015,0.010)*front
        if w>0.015:
            delta=Vector((0,0,(0.907-z)*0.88*w))
            keys[keyname].data[i].co += inv @ delta
    # Smile: lift the mouth corners and subtly raise the central upper lip.
    mouth=gauss(x,z,0.010,0.801,0.026,0.009)*front
    corner=abs(x-0.010)/0.026
    if mouth>0.015:
        dz=(0.003+0.009*corner)*mouth
        keys["Smile"].data[i].co += inv @ Vector((0,-0.001*mouth,dz))
    # Mouth-open morph: separate upper/lower lip regions vertically.
    mw=gauss(x,z,0.010,0.801,0.025,0.012)*front
    if mw>0.015:
        dz=(z-0.801)*1.35*mw
        keys["Mouth_Open"].data[i].co += inv @ Vector((0,-0.002*mw,dz))
    # Raise eyebrows without affecting the hairline.
    bw=(gauss(x,z,-0.016,0.897,0.020,0.007)+gauss(x,z,0.036,0.897,0.020,0.007))*front
    if bw>0.015:
        keys["Brow_Raise"].data[i].co += inv @ Vector((0,0,0.009*bw))
# Animate a short test: blink, smile, talk/open-close, brow raise.
for frame,values in [
    (1,{"Blink_L":0,"Blink_R":0,"Smile":0,"Mouth_Open":0,"Brow_Raise":0}),
    (12,{"Blink_L":1,"Blink_R":1,"Smile":0,"Mouth_Open":0,"Brow_Raise":0}),
    (16,{"Blink_L":0,"Blink_R":0,"Smile":0,"Mouth_Open":0,"Brow_Raise":0}),
    (30,{"Blink_L":0,"Blink_R":0,"Smile":0.8,"Mouth_Open":0,"Brow_Raise":0.25}),
    (42,{"Blink_L":0,"Blink_R":0,"Smile":0.35,"Mouth_Open":0.8,"Brow_Raise":0}),
    (48,{"Blink_L":0,"Blink_R":0,"Smile":0.35,"Mouth_Open":0.15,"Brow_Raise":0}),
    (54,{"Blink_L":0,"Blink_R":0,"Smile":0.35,"Mouth_Open":0.75,"Brow_Raise":0}),
    (60,{"Blink_L":0,"Blink_R":0,"Smile":0,"Mouth_Open":0,"Brow_Raise":0})
]:
    for name,value in values.items():
        keys[name].value=value
        keys[name].keyframe_insert(data_path="value",frame=frame,group="Presenter Facial Controls")
scene.frame_start=1; scene.frame_end=60; scene.render.fps=24
if mesh.data.shape_keys.animation_data and mesh.data.shape_keys.animation_data.action:
    for fc in mesh.data.shape_keys.animation_data.action.fcurves:
        for kp in fc.keyframe_points: kp.interpolation="BEZIER"
# Render a frontal close-up to visually validate facial deformations.
bpy.context.view_layer.update()
head=arm.data.bones["mixamorig:Head"]
center=arm.matrix_world @ head.matrix_local
target=center.translation+Vector((0,-0.01,-0.015))
bpy.ops.object.camera_add(location=(target.x,target.y-1.05,target.z+0.04))
cam=bpy.context.object; cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler(); cam.data.lens=78; scene.camera=cam
worldmat=scene.world or bpy.data.worlds.new("Presenter Face Preview"); scene.world=worldmat; worldmat.use_nodes=True
worldmat.node_tree.nodes["Background"].inputs["Color"].default_value=(0.008,0.012,0.02,1)
worldmat.node_tree.nodes["Background"].inputs["Strength"].default_value=0.2
def light(name,loc,power,size):
    bpy.ops.object.light_add(type="AREA",location=loc); l=bpy.context.object; l.name=name
    l.data.energy=power; l.data.shape="DISK"; l.data.size=size
    l.rotation_euler=(target-l.location).to_track_quat("-Z","Y").to_euler()
light("Face_Key",(target.x-0.5,target.y-0.8,target.z+0.5),130,0.9)
light("Face_Fill",(target.x+0.5,target.y-0.7,target.z+0.1),75,0.8)
scene.render.engine="BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items.keys() else "BLENDER_EEVEE"
scene.render.resolution_x=768; scene.render.resolution_y=768; scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"; scene.render.image_settings.color_mode="RGBA"
scene.view_settings.view_transform="AgX"; scene.camera.data.dof.use_dof=False
frames=[1,12,42]
for frame in frames:
    scene.frame_set(frame)
    scene.render.filepath=os.path.join(OUT,"facial-frame-%02d.png"%frame)
    bpy.ops.render.render(write_still=True)
# Save editable Blender project and a GLB with morph targets.
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,"Presenter_Facial_Rig.blend"))
bpy.ops.object.select_all(action="DESELECT")
for o in (arm,mesh): o.select_set(True)
bpy.context.view_layer.objects.active=arm
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,"Presenter_Facial_Rig.glb"),export_format="GLB",use_selection=True,export_morph=True)
report={"asset":ASSET,"face_is_original_sculpted_mesh":True,"controls":list(keys.keys()),"animated_test_frames":frames,"head_vertex_count":len(face),"front_surface_y":front_y,"note":"Facial morph controls added to original head mesh; lip-sync viseme expansion is a later stage."}
with open(os.path.join(OUT,"facial-controls-report.json"),"w") as f: json.dump(report,f,indent=2)
print("PRESENTER_FACIAL_RIG_COMPLETE",json.dumps(report),flush=True)
