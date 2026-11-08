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
scene.render.engine = "BLENDER_EEVEE"
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


def render_earwax_test():
    # Stylized, clean medical cutaway: camera travels into the ear canal.
    skin = mat("Warm pink ear tissue",(0.62,0.19,0.17),rough=.82)
    inner = mat("Canal inner tissue",(0.83,0.37,0.33),rough=.78)
    fold = mat("Raised tissue folds",(0.92,0.49,0.43),rough=.72)
    waxmat = mat("Golden amber earwax",(0.48,0.24,0.035),rough=.32)
    waxhi = mat("Wax highlights",(0.72,0.43,0.08),rough=.28)
    cotton = mat("Cotton white",(0.92,0.91,0.85),rough=.88)
    stickmat = mat("Swab stem",(0.78,0.78,0.74),rough=.55)
    drum = mat("Eardrum",(0.48,0.25,0.25),rough=.5)
    labelmat = mat("Soft white text",(.95,.95,.92),(.5,.5,.5),.35,rough=.6)
    # Organic tunnel wall, running away from the viewer along +Y.
    verts=[]; faces=[]; rings=44; sides=64
    for j in range(rings):
        t=j/(rings-1); y=-4.8+t*9.1
        radius=1.42 + .18*math.sin(t*math.pi) + .10*math.sin(t*math.pi*3)
        for i in range(sides):
            a=2*math.pi*i/sides
            ripple=1+.035*math.sin(a*5+t*11)+.018*math.sin(a*9-t*7)
            verts.append((math.cos(a)*radius*ripple,y,math.sin(a)*radius*ripple))
    for j in range(rings-1):
        for i in range(sides):
            a=j*sides+i; b=j*sides+(i+1)%sides
            faces.append((a,b,b+sides,a+sides))
    mesh=bpy.data.meshes.new("EarCanalWallMesh"); mesh.from_pydata(verts,[],faces); mesh.materials.append(inner)
    wall=bpy.data.objects.new("EAR_CANAL_CROSS_SECTION",mesh); scene.collection.objects.link(wall)
    for p in mesh.polygons:p.use_smooth=True
    # Soft tissue folds along the canal wall, kept subtle and non-graphic.
    for k in range(9):
        angle=2*math.pi*k/9
        x=math.cos(angle)*1.34; z=math.sin(angle)*1.34
        bpy.ops.mesh.primitive_torus_add(major_radius=.26,minor_radius=.055,major_segments=32,minor_segments=10,location=(x,-1.6+(k%3)*1.35,z),rotation=(math.pi/2,0,angle))
        o=bpy.context.object; o.name="Canal_Fold_%02d"%k; o.scale=(1.0,.62,1.0); o.data.materials.append(fold)
    # Eardrum at the far end, a thin oval membrane facing the camera.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,radius=1,location=(0,4.25,0))
    membrane=bpy.context.object; membrane.name="EARDRUM"; membrane.scale=(1.12,.12,1.12); membrane.data.materials.append(drum); bpy.ops.object.shade_smooth()
    bpy.ops.mesh.primitive_torus_add(major_radius=1.17,minor_radius=.09,major_segments=64,minor_segments=12,location=(0,4.12,0),rotation=(math.pi/2,0,0))
    rim=bpy.context.object; rim.name="Eardrum_Rim"; rim.data.materials.append(fold)
    # Wax is a soft, irregular golden mass near the foreground of the canal.
    wax_parts=[]
    for idx,(loc,scale) in enumerate([
        ((-.12,-2.45,-.72),(.78,.48,.48)),
        ((.42,-2.55,-.48),(.52,.42,.40)),
        ((-.55,-2.35,-.55),(.43,.38,.34)),
        ((.03,-2.18,-.32),(.38,.32,.30))
    ]):
        o=ball("EARWAX_%02d"%idx,loc,1,waxmat,32,20); o.scale=scale; wax_parts.append(o)
    # Small glossy deposits make the wax read as moist amber, not a flat blob.
    for idx,loc in enumerate([(-.35,-2.0,-.18),(.35,-2.08,-.2),(.05,-1.92,-.48)]):
        o=ball("Wax_Glint_%02d"%idx,loc,.07,waxhi,16,10)
    # Cotton swab: stem and cotton tip enter diagonally from lower-left.
    def rod_between(name,a,b,radius,material,vertices=24):
        mid=(Vector(a)+Vector(b))/2; vec=Vector(b)-Vector(a)
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=vec.length,location=mid)
        o=bpy.context.object; o.name=name; o.rotation_euler=vec.to_track_quat("Z","Y").to_euler(); o.data.materials.append(material)
        return o
    stem=rod_between("COTTON_SWAB_STEM",(-2.9,-3.7,-2.25),(-.62,-1.9,-1.05),.075,stickmat)
    tip=ball("COTTON_SWAB_TIP",(-.62,-1.9,-1.05),.24,cotton,32,20); tip.scale=(.68,1.25,.68)
    # Camera moves forward through the tunnel; swab advances slightly, then pauses.
    bpy.ops.object.camera_add(location=(0,-12.5,.05)); cam=bpy.context.object; cam.name="EarJourneyCamera"; cam.data.lens=43; aim(cam,(0,1.0,0)); scene.camera=cam
    cam.location=(0,-12.5,.05); cam.keyframe_insert(data_path="location",frame=1)
    cam.location=(0,-9.0,.02); cam.keyframe_insert(data_path="location",frame=last)
    # Animate the swab tip gently deeper to illustrate why wax may be pushed inward.
    for obj in (stem,tip):
        original=obj.location.copy()
        obj.keyframe_insert(data_path="location",frame=1)
        obj.location=original+Vector((.16,1.0,.10))
        obj.keyframe_insert(data_path="location",frame=int(last*.62))
        obj.keyframe_insert(data_path="location",frame=last)
    # Soft studio lighting and warm background.
    scene.world.color=(.16,.045,.04)
    bpy.ops.object.light_add(type="AREA",location=(-4,-5,6)); key=bpy.context.object; key.data.energy=1150; key.data.size=5; aim(key,(0,0,0))
    bpy.ops.object.light_add(type="AREA",location=(4,1,-3)); fill=bpy.context.object; fill.data.energy=650; fill.data.size=4; aim(fill,(0,1,0))
    bpy.ops.object.light_add(type="AREA",location=(0,4,4)); rimlight=bpy.context.object; rimlight.data.energy=500; rimlight.data.size=3; aim(rimlight,(0,3,0))
    # Title/callouts face the camera and remain in the safe upper area.
    def overlay(body, frame, end, z=3.15):
        c=bpy.data.curves.new("OverlayText","FONT"); c.body=body; c.size=.22; c.extrude=0
        o=bpy.data.objects.new("Overlay_"+body,c); scene.collection.objects.link(o)
        o.location=(-1.48,-4.9,z); o.rotation_euler=(math.pi/2,0,0); o.data.materials.append(labelmat)
        o.hide_render=True; o.keyframe_insert(data_path="hide_render",frame=1)
        o.hide_render=False; o.keyframe_insert(data_path="hide_render",frame=frame)
        o.hide_render=True; o.keyframe_insert(data_path="hide_render",frame=end+1)
    overlay("WHY DOES EARWAX FORM?",1,int(last*.22))
    overlay("THE EAR CANAL MOVES WAX OUTWARD",int(last*.25),int(last*.58))
    overlay("COTTON SWABS CAN PUSH WAX DEEPER",int(last*.60),last)
    # Fast, clean EEVEE render settings; no expensive compositor glow or particle stars.
    scene.render.engine="BLENDER_EEVEE"
    scene.eevee.taa_render_samples=8
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="FFMPEG"
    scene.render.ffmpeg.format="MPEG4"; scene.render.ffmpeg.codec="H264"
    scene.render.ffmpeg.constant_rate_factor="MEDIUM"; scene.render.ffmpeg.ffmpeg_preset="REALTIME"
    scene.render.filepath=output_path
    os.makedirs(os.path.dirname(output_path),exist_ok=True); scene.frame_set(1)
    print("EDUFORGE_EAR_RENDER_START",json.dumps({"title":project["title"],"frames":last,"resolution":[width,height]}),flush=True)
    bpy.ops.render.render(animation=True)
    print("EDUFORGE_EAR_RENDER_COMPLETE",output_path,flush=True)

if data.get("scene_type")=="earwax":
    render_earwax_test()
    raise SystemExit(0)


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
