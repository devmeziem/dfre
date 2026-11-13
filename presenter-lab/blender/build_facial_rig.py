import bpy, os, json, math
from mathutils import Vector

ASSET="presenter-lab/assets/Presenter.glb"
OUT="output/presenter"
os.makedirs(OUT,exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=ASSET)
scene=bpy.context.scene
arm=next((o for o in scene.objects if o.type=="ARMATURE"),None)
mesh=next((o for o in scene.objects if o.type=="MESH" and o.find_armature()),None)
if arm is None or mesh is None:
    raise RuntimeError("Presenter skinned mesh/armature not found")
for obj in list(scene.objects):
    if obj.type=="MESH" and obj!=mesh and not obj.find_armature():
        bpy.data.objects.remove(obj,do_unlink=True)

head_group=mesh.vertex_groups.get("mixamorig:Head")
if head_group is None:
    raise RuntimeError("Head vertex group missing")
head_index=head_group.index
verts=mesh.data.vertices
world_points=[mesh.matrix_world @ v.co for v in verts]
head=[]
for i,(v,p) in enumerate(zip(verts,world_points)):
    weight=next((g.weight for g in v.groups if g.group==head_index),0.0)
    if weight>0.15:
        head.append((i,p))
if len(head)<100:
    raise RuntimeError("Insufficient head-weighted vertices")
xs=[p.x for _,p in head]; ys=[p.y for _,p in head]; zs=[p.z for _,p in head]
xmin,xmax=min(xs),max(xs); ymin,ymax=min(ys),max(ys); zmin,zmax=min(zs),max(zs)
width=xmax-xmin; height=zmax-zmin
if width<=0 or height<=0:
    raise RuntimeError("Invalid head bounds")
cx=(xmin+xmax)/2
# Estimate feature bands from the actual weighted head bounds, not hard-coded scene coordinates.
eye_z=zmin+height*0.59
mouth_z=zmin+height*0.27
brow_z=zmin+height*0.70
eye_offset=width*0.22
eye_sx=width*0.16; eye_sz=height*0.085
mouth_sx=width*0.25; mouth_sz=height*0.075
front_y=ymin
inv=mesh.matrix_world.inverted().to_3x3()
if mesh.data.shape_keys:
    basis=mesh.data.shape_keys.key_blocks.get("Basis")
    if basis is None:
        raise RuntimeError("Existing shape keys lack Basis")
else:
    bpy.context.view_layer.objects.active=mesh
    mesh.select_set(True)
    basis=mesh.shape_key_add(name="Basis",from_mix=False)
keys={}
for name in ("Blink_L","Blink_R","Smile","Mouth_Open","Brow_Raise"):
    if mesh.data.shape_keys.key_blocks.get(name):
        raise RuntimeError("Refusing to overwrite existing shape key: "+name)
    keys[name]=mesh.shape_key_add(name=name,from_mix=False)

def gaussian(x,z,fx,fz,sx,sz):
    return math.exp(-0.5*((x-fx)/sx)**2-0.5*((z-fz)/sz)**2)

affected={}
max_delta={}
for name,key in keys.items():
    changed=0; largest=0.0
    for i,p in head:
        x,y,z=p.x,p.y,p.z
        # The face points toward -Y. Fade the morph toward the sides/back of the head.
        front=max(0.0,min(1.0,(front_y+height*0.18-y)/(height*0.18)))
        if front<=0.02:
            continue
        delta=Vector((0,0,0))
        if name in ("Blink_L","Blink_R"):
            side=-1 if name=="Blink_L" else 1
            eye_x=cx+side*eye_offset
            w=gaussian(x,z,eye_x,eye_z,eye_sx,eye_sz)*front
            if w>0.025:
                delta.z=(eye_z-z)*0.96*w
        elif name=="Smile":
            w=gaussian(x,z,cx,mouth_z,mouth_sx,mouth_sz)*front
            if w>0.025:
                corner=min(1.0,abs(x-cx)/(width*0.25))
                delta=Vector((0,-height*0.008*w,height*(0.006+0.018*corner)*w))
        elif name=="Mouth_Open":
            w=gaussian(x,z,cx,mouth_z,mouth_sx,mouth_sz)*front
            if w>0.025:
                delta=Vector((0,-height*0.012*w,(z-mouth_z)*1.8*w))
        elif name=="Brow_Raise":
            w=(gaussian(x,z,cx-eye_offset,brow_z,eye_sx*1.1,eye_sz*0.65)+
               gaussian(x,z,cx+eye_offset,brow_z,eye_sx*1.1,eye_sz*0.65))*front
            w=min(1.0,w)
            if w>0.025:
                delta.z=height*0.025*w
        if delta.length>1e-8:
            key.data[i].co += inv @ delta
            changed+=1
            largest=max(largest,delta.length)
    affected[name]=changed
    max_delta[name]=round(largest,7)
    if changed<8 or largest<0.0001:
        raise RuntimeError("Facial control has no meaningful geometry deformation: %s (%s vertices, max %s)"%(name,changed,largest))

# Keep a reusable facial action in the editable Blender file.
animation=[
 (1,  {"Blink_L":0,"Blink_R":0,"Smile":0,"Mouth_Open":0,"Brow_Raise":0}),
 (8,  {"Blink_L":1,"Blink_R":1,"Smile":0,"Mouth_Open":0,"Brow_Raise":0}),
 (12, {"Blink_L":0,"Blink_R":0,"Smile":0,"Mouth_Open":0,"Brow_Raise":0}),
 (20, {"Blink_L":0,"Blink_R":0,"Smile":0.85,"Mouth_Open":0,"Brow_Raise":0.25}),
 (30, {"Blink_L":0,"Blink_R":0,"Smile":0.2,"Mouth_Open":0.9,"Brow_Raise":0}),
 (36, {"Blink_L":0,"Blink_R":0,"Smile":0.2,"Mouth_Open":0.15,"Brow_Raise":0}),
 (42, {"Blink_L":0,"Blink_R":0,"Smile":0,"Mouth_Open":0,"Brow_Raise":0})
]
for frame,values in animation:
    for name,value in values.items():
        keys[name].value=value
        keys[name].keyframe_insert(data_path="value",frame=frame,group="Presenter Facial Controls")
scene.frame_start=1
scene.frame_end=42
scene.render.fps=24

# Head-only preview camera: avoid the previous full-body framing.
target=Vector((cx,front_y+0.01,zmin+height*0.53))
distance=max(width*1.65,0.28)
bpy.ops.object.camera_add(location=(cx,front_y-distance,target.z))
cam=bpy.context.object
cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler()
cam.data.lens=85
scene.camera=cam
world=scene.world or bpy.data.worlds.new("Presenter Preview World")
scene.world=world
world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Color"].default_value=(0.006,0.008,0.012,1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value=0.08

def add_area(name,location,energy,size):
    bpy.ops.object.light_add(type="AREA",location=location)
    light=bpy.context.object
    light.name=name
    light.data.energy=energy
    light.data.shape="DISK"
    light.data.size=size
    light.rotation_euler=(target-light.location).to_track_quat("-Z","Y").to_euler()

# Low-power soft lighting prevents the washed-out look of the previous render.
add_area("Soft_Key",(cx-width*0.55,front_y-distance*0.72,target.z+height*0.35),18,width*0.9)
add_area("Soft_Fill",(cx+width*0.5,front_y-distance*0.65,target.z+height*0.05),6,width*0.8)
scene.render.engine="BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items.keys() else "BLENDER_EEVEE"
scene.render.resolution_x=768
scene.render.resolution_y=768
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.image_settings.color_mode="RGBA"
scene.view_settings.view_transform="AgX"
scene.view_settings.look="AgX - Medium High Contrast"
scene.view_settings.exposure=-0.7
scene.view_settings.gamma=1.0
scene.camera.data.dof.use_dof=False

# Set values directly after frame_set so each still proves the morph geometry visibly.
preview_values={
 "facial-frame-01.png":{"Blink_L":0,"Blink_R":0,"Smile":0,"Mouth_Open":0,"Brow_Raise":0},
 "facial-frame-12.png":{"Blink_L":1,"Blink_R":1,"Smile":0,"Mouth_Open":0,"Brow_Raise":0},
 "facial-frame-20.png":{"Blink_L":0,"Blink_R":0,"Smile":0.9,"Mouth_Open":0,"Brow_Raise":0.5},
 "facial-frame-30.png":{"Blink_L":0,"Blink_R":0,"Smile":0,"Mouth_Open":1,"Brow_Raise":0}
}
for filename,values in preview_values.items():
    scene.frame_set(1)
    for name,value in values.items():
        keys[name].value=value
    bpy.context.view_layer.update()
    scene.render.filepath=os.path.join(OUT,filename)
    bpy.ops.render.render(write_still=True)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,"Presenter_Facial_Rig.blend"))
bpy.ops.object.select_all(action="DESELECT")
arm.select_set(True)
mesh.select_set(True)
bpy.context.view_layer.objects.active=arm
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,"Presenter_Facial_Rig.glb"),export_format="GLB",use_selection=True,export_morph=True)
report={
 "asset":ASSET,
 "face_is_original_sculpted_mesh":True,
 "controls":list(keys.keys()),
 "head_vertex_count":len(head),
 "head_bounds":{"width":round(width,5),"height":round(height,5),"front_y":round(front_y,5)},
 "affected_vertices":affected,
 "max_world_delta":max_delta,
 "preview_frames":["facial-frame-01.png","facial-frame-12.png","facial-frame-20.png","facial-frame-30.png"],
 "preview_modes":["neutral","both_eyes_closed","smile_and_brows_raised","mouth_open"],
 "lighting":{"key_energy":18,"fill_energy":6,"world_strength":0.08,"exposure":-0.7},
 "note":"Morph geometry is checked for nonzero vertex changes. Preview images use manually assigned shape-key values. These controls are facial expressions, not phoneme-accurate lip sync."
}
with open(os.path.join(OUT,"facial-controls-report.json"),"w") as f:
    json.dump(report,f,indent=2)
print("PRESENTER_FACIAL_RIG_COMPLETE",json.dumps(report),flush=True)
