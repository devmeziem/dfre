import bpy, json, math, os, sys, random
from mathutils import Vector

def arg(flag, default):
    a = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    return a[a.index(flag)+1] if flag in a and a.index(flag)+1 < len(a) else default

seed_path = os.path.abspath(arg("--seed", "seeds/solar_eclipse.json"))
output_path = os.path.abspath(arg("--output", "output/solar-eclipse-test.mp4"))
with open(seed_path, encoding="utf-8") as f: data = json.load(f)
project, spec = data["project"], data["scene"]
fps = int(project.get("fps", 24)); duration = float(project.get("duration_seconds", 15))
width = int(project.get("resolution", {}).get("width", 720))
height = int(project.get("resolution", {}).get("height", 1280))
last = max(2, round(duration * fps))

bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x=width; scene.render.resolution_y=height; scene.render.resolution_percentage=100
scene.render.fps=fps; scene.frame_start=1; scene.frame_end=last
scene.render.image_settings.file_format="FFMPEG"
scene.render.ffmpeg.format="MPEG4"; scene.render.ffmpeg.codec="H264"
scene.render.ffmpeg.constant_rate_factor="MEDIUM"; scene.render.ffmpeg.ffmpeg_preset="GOOD"
scene.render.filepath=output_path; scene.render.film_transparent=False
scene.world.color=(0.002,0.003,0.015)
scene.view_settings.view_transform="Standard"; scene.view_settings.look="Medium High Contrast"

def mat(name, color, emission=None, strength=0, rough=0.5, metallic=0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    b=m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value=(*color,1); b.inputs["Roughness"].default_value=rough
    b.inputs["Metallic"].default_value=metallic
    if emission and "Emission Color" in b.inputs:
        b.inputs["Emission Color"].default_value=(*emission,1); b.inputs["Emission Strength"].default_value=strength
    return m

def ball(name, loc, radius, material, seg=48, rings=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, radius=radius, location=loc)
    o=bpy.context.object; o.name=name; bpy.ops.object.shade_smooth(); o.data.materials.append(material); return o

def aim(o, target):
    o.rotation_euler=(Vector(target)-o.location).to_track_quat("-Z","Y").to_euler()

def label(body, loc, size, material, name):
    c=bpy.data.curves.new(name,"FONT"); c.body=body; c.size=size; c.extrude=0.001
    o=bpy.data.objects.new(name,c); scene.collection.objects.link(o); o.location=loc
    o.rotation_euler=(math.radians(90),0,0); o.data.materials.append(material); return o

sunmat=mat("Solar gold",(1,.25,.015),(1,.22,.01),5,1)
earthmat=mat("Ocean blue",(.018,.12,.48),rough=.38,metallic=.08)
landmat=mat("Continents",(.06,.34,.16),rough=.8)
moonmat=mat("Moon stone",(.38,.4,.44),rough=.95)
whitemat=mat("Label white",(.8,.9,1),(.55,.72,1),1.1)
orbitmat=mat("Orbit blue",(.05,.16,.4),(.04,.12,.35),.5)
shadowmat=mat("Shadow cone",(.008,.012,.035),rough=1)
starmat=mat("Stars",(.55,.7,1),(.4,.6,1),1.5)
random.seed(17)
for i in range(110):
    ball("Star_%03d"%i,(random.uniform(-5,5),random.uniform(2,8),random.uniform(-11,11)),
         random.uniform(.012,.03),starmat,8,6)

sun=ball("SUN",(0,0,5),2,sunmat)
earth=ball("EARTH",(0,0,-5),1.35,earthmat)
for i,(loc,scale) in enumerate([
    ((-.45,-1.05,-4.55),(.42,.12,.28)),((.45,-1,-5.15),(.34,.1,.48)),((.05,-1.08,-4.15),(.25,.08,.18))
]):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,radius=1,location=loc)
    p=bpy.context.object; p.name="Land_%d"%i; p.scale=scale; p.data.materials.append(landmat)
moon=ball("MOON",(2.7,0,0),.48,moonmat)

bpy.ops.mesh.primitive_cone_add(vertices=40,radius1=.12,radius2=.78,depth=3.5,location=(0,.15,-2.5))
cone=bpy.context.object; cone.name="MOON_SHADOW_CONE";  cone.data.materials.append(shadowmat)

bpy.ops.object.light_add(type="AREA",location=(-5,-8,7))
key=bpy.context.object; key.data.energy=1800; key.data.shape="DISK"; key.data.size=8; aim(key,(0,0,0))
bpy.ops.object.light_add(type="AREA",location=(5,3,-3))
fill=bpy.context.object; fill.data.energy=900; fill.data.size=6; aim(fill,(0,0,-5))

cd=bpy.data.cameras.new("EducationalCamera"); cam=bpy.data.objects.new("EducationalCamera",cd)
scene.collection.objects.link(cam); cam.location=(0,-26,0); cd.lens=42; aim(cam,(0,0,0)); scene.camera=cam
cam.location=(-.5,-27,1.0); cam.keyframe_insert(data_path="location",frame=1)
cam.location=(.5,-25,0); cam.keyframe_insert(data_path="location",frame=last)

anim=spec.get("animation",{})
moon.location=Vector(anim.get("moon_start",[2.7,0,0])); moon.keyframe_insert(data_path="location",frame=1)
moon.location=Vector(anim.get("moon_alignment",[0,0,0])); moon.keyframe_insert(data_path="location",frame=int(anim.get("alignment_frame",last//2)))
moon.location=Vector(anim.get("moon_end",[-.25,0,0])); moon.keyframe_insert(data_path="location",frame=last)

curve=bpy.data.curves.new("MoonOrbit","CURVE"); curve.dimensions="3D"; curve.bevel_depth=.012; curve.bevel_resolution=2
sp=curve.splines.new("POLY"); sp.points.add(63)
for i,p in enumerate(sp.points):
    a=i/63*math.tau; p.co=(math.cos(a)*3.1,.1,math.sin(a)*2.7,1)
orbit=bpy.data.objects.new("MoonOrbit",curve); scene.collection.objects.link(orbit); orbit.data.materials.append(orbitmat)

label("HOW A SOLAR ECLIPSE HAPPENS",(-2.9,-2,9),.48,whitemat,"Title")
label("SUN",(-.8,-2,2.5),.4,whitemat,"SunLabel")
label("MOON",(-.9,-2,-1.8),.34,whitemat,"MoonLabel")
label("EARTH",(-.9,-2,-7.2),.4,whitemat,"EarthLabel")
for i,item in enumerate(spec.get("callouts",[])):
    o=label(item["text"],item["position"],.25,whitemat,"Callout_%02d"%i)
    start=max(1,int(item.get("start_frame",1))); end=min(last,int(item.get("end_frame",last)))
    o.hide_render=True; o.keyframe_insert(data_path="hide_render",frame=1)
    o.hide_render=False; o.keyframe_insert(data_path="hide_render",frame=start)
    o.hide_render=True; o.keyframe_insert(data_path="hide_render",frame=end+1)

scene.use_nodes=True; nodes=scene.node_tree.nodes; nodes.clear()
rl=nodes.new("CompositorNodeRLayers"); glow=nodes.new("CompositorNodeGlare")
glow.glare_type="FOG_GLOW"; glow.quality="MEDIUM"; glow.threshold=1.2
comp=nodes.new("CompositorNodeComposite")
scene.node_tree.links.new(rl.outputs["Image"],glow.inputs["Image"])
scene.node_tree.links.new(glow.outputs["Image"],comp.inputs["Image"])

os.makedirs(os.path.dirname(output_path),exist_ok=True); scene.frame_set(1)
print("EDUFORGE_RENDER_START",json.dumps({"title":project["title"],"frames":last,"resolution":[width,height]}),flush=True)
bpy.ops.render.render(animation=True)
print("EDUFORGE_RENDER_COMPLETE",output_path,flush=True)
