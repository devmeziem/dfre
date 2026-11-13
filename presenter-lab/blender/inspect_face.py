import bpy, os, json, math
from mathutils import Vector

asset="presenter-lab/assets/Presenter.glb"
outdir="output/presenter/face-diagnostics"
os.makedirs(outdir,exist_ok=True)
bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=asset)
scene=bpy.context.scene
arm=next(o for o in scene.objects if o.type=="ARMATURE")
mesh=next(o for o in scene.objects if o.type=="MESH" and o.find_armature())
for o in list(scene.objects):
    if o.type=="MESH" and o!=mesh and not o.find_armature():
        bpy.data.objects.remove(o,do_unlink=True)
# Put feet on floor.
corners=[mesh.matrix_world @ Vector(c) for c in mesh.bound_box]
minz=min(v.z for v in corners)
for o in (arm,mesh): o.location.z-=minz
bpy.context.view_layer.update()
head=arm.data.bones.get("mixamorig:Head")
if not head: raise RuntimeError("Mixamo Head bone missing")
head_world=arm.matrix_world @ head.matrix_local
center=head_world.translation
# Compute the vertices influenced by the head/neck, in world coordinates.
groups={g.name:g.index for g in mesh.vertex_groups}
head_indices={groups[n] for n in ("mixamorig:Head","mixamorig:Neck") if n in groups}
weighted=[]
for v in mesh.data.vertices:
    if any(g.group in head_indices and g.weight>0.05 for g in v.groups):
        weighted.append(mesh.matrix_world @ v.co)
if weighted:
    bounds=[[min(p[i] for p in weighted),max(p[i] for p in weighted)] for i in range(3)]
else: bounds=[]
# Studio close-up, frontal view (the existing preview camera faces from -Y).
world=scene.world or bpy.data.worlds.new("Face Diagnostic World"); scene.world=world; world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Color"].default_value=(0.018,0.022,0.03,1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value=0.3
def make_light(name,loc,power,size):
    bpy.ops.object.light_add(type="AREA",location=loc)
    l=bpy.context.object; l.name=name; l.data.energy=power; l.data.shape="DISK"; l.data.size=size
    l.rotation_euler=(center-l.location).to_track_quat("-Z","Y").to_euler()
make_light("Face_Key",(-0.5,-1.0,center.z+0.5),120,1.0)
make_light("Face_Fill",(0.6,-0.8,center.z+0.1),70,0.8)
make_light("Face_Rim",(0.0,0.6,center.z+0.3),100,0.7)
bpy.ops.object.camera_add(location=(center.x,center.y-1.05,center.z+0.06))
cam=bpy.context.object; cam.rotation_euler=(center-cam.location).to_track_quat("-Z","Y").to_euler()
cam.data.lens=75; scene.camera=cam
scene.render.engine="BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items.keys() else "BLENDER_EEVEE"
scene.render.resolution_x=768; scene.render.resolution_y=768; scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"; scene.render.image_settings.color_mode="RGBA"
scene.view_settings.view_transform="AgX"; scene.render.filepath=os.path.join(outdir,"face-front.png")
scene.camera.data.dof.use_dof=False
bpy.ops.render.render(write_still=True)
# Side diagnostic.
cam.location=(center.x+1.05,center.y,center.z+0.06)
cam.rotation_euler=(center-cam.location).to_track_quat("-Z","Y").to_euler()
scene.render.filepath=os.path.join(outdir,"face-side.png")
bpy.ops.render.render(write_still=True)
report={"head_bone":"mixamorig:Head","head_bone_head_world":[round(v,5) for v in head_world.translation],"head_bone_tail_world":[round(v,5) for v in (arm.matrix_world @ head.tail_local)],"head_neck_weighted_world_bounds":bounds,"front_direction":"-Y","face_mesh_shape_keys":list(mesh.data.shape_keys.key_blocks.keys()) if mesh.data.shape_keys else [],"face_vertex_group_names":[g.name for g in mesh.vertex_groups if "Head" in g.name or "Neck" in g.name]}
with open(os.path.join(outdir,"face-report.json"),"w") as f: json.dump(report,f,indent=2)
print("PRESENTER_FACE_DIAGNOSTICS",json.dumps(report),flush=True)
