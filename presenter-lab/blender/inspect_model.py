import bpy, json, os
asset = "presenter-lab/assets/Presenter.glb"
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=asset)
meshes = []
for o in bpy.context.scene.objects:
    if o.type == "MESH":
        meshes.append({
            "name": o.name,
            "vertices": len(o.data.vertices),
            "polygons": len(o.data.polygons),
            "materials": [m.name if m else None for m in o.data.materials],
            "shape_keys": list(o.data.shape_keys.key_blocks.keys()) if o.data.shape_keys else [],
            "vertex_groups": [g.name for g in o.vertex_groups],
            "dimensions": [round(v, 5) for v in o.dimensions],
            "local_bounds": [[round(min(v.co[i] for v in o.data.vertices),5), round(max(v.co[i] for v in o.data.vertices),5)] for i in range(3)] if o.data.vertices else []
        })
rigs = []
for a in bpy.context.scene.objects:
    if a.type == "ARMATURE":
        rigs.append({
            "name": a.name,
            "bone_count": len(a.data.bones),
            "bones": [{"name": b.name, "parent": b.parent.name if b.parent else None, "head": [round(x,5) for x in b.head_local], "tail": [round(x,5) for x in b.tail_local]} for b in a.data.bones]
        })
actions = [a.name for a in bpy.data.actions]
result = {
    "meshes": meshes,
    "rigs": rigs,
    "actions": actions,
    "objects": [{"name":o.name,"type":o.type} for o in bpy.context.scene.objects]
}
os.makedirs("output/presenter", exist_ok=True)
with open("output/presenter/presenter-deep-inspection.json","w") as f: json.dump(result,f,indent=2)
print("PRESENTER_DEEP_INSPECTION", json.dumps({"meshes":meshes,"rigs":[{"name":r["name"],"bone_count":r["bone_count"],"bone_names":[b["name"] for b in r["bones"]]} for r in rigs],"actions":actions}), flush=True)
