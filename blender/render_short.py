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
    # Multi-shot anatomical animation. The canal is a curved, open cutaway,
    # wax is attached to the side wall, and the swab has a soft cotton head.
    skin=mat("Pinna warm skin",(0.58,.22,.20),rough=.72)
    canalmat=mat("Living canal tissue",(.48,.12,.12),rough=.58)
    ridge=mat("Raised canal folds",(.78,.31,.27),rough=.64)
    waxmat=mat("Amber earwax",(.36,.13,.018),rough=.24)
    waxlight=mat("Wax sheen",(.78,.43,.10),rough=.19)
    cotton=mat("Cotton fibers",(.94,.91,.83),rough=.92)
    stemmat=mat("Swab shaft",(.83,.83,.79),rough=.42)
    drumat=mat("Eardrum membrane",(.55,.28,.27),rough=.55)
    dark=mat("Deep canal shadow",(.035,.008,.012),rough=1)
    white=mat("Caption white",(.98,.98,.95),(.8,.8,.8),.25,rough=.6)

    # Outer ear: sculpted, softly irregular pinna silhouette and inner helix.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=40,radius=1,location=(0,-4.0,0))
    pinna=bpy.context.object; pinna.name="OUTER_EAR_PAVILION"; pinna.scale=(1.55,.34,2.05); pinna.data.materials.append(skin); bpy.ops.object.shade_smooth()
    def tube_curve(name, points, bevel, material):
        c=bpy.data.curves.new(name,"CURVE"); c.dimensions="3D"; c.resolution_u=24; c.bevel_depth=bevel; c.bevel_resolution=4
        s=c.splines.new("BEZIER"); s.bezier_points.add(len(points)-1)
        for bp,pt in zip(s.bezier_points,points):
            bp.co=pt; bp.handle_left_type="AUTO"; bp.handle_right_type="AUTO"
        o=bpy.data.objects.new(name,c); scene.collection.objects.link(o); o.data.materials.append(material); return o
    tube_curve("Outer_Helix",[(.85,-4.30,-1.5),(1.25,-4.32,-.5),(1.15,-4.32,.8),(.55,-4.30,1.65),(-.25,-4.3,1.4),(-.7,-4.3,.55)],.16,ridge)
    tube_curve("Antihelix",[(.82,-4.34,-.9),(.48,-4.34,-.1),(.65,-4.34,.75),(.12,-4.34,1.18)],.105,skin)
    # A real tunnel-like canal, open at the near end, with a broad cutaway
    # window facing camera so viewers can see wax and the instrument.
    verts=[]; faces=[]; rings=56; sides=64
    for j in range(rings):
        t=j/(rings-1); y=-2.9+t*7.6
        radius=1.05+.12*math.sin(t*math.pi*2)+.045*math.sin(t*math.pi*7)
        for i in range(sides):
            a=2*math.pi*i/sides
            r=radius*(1+.025*math.sin(5*a+8*t))
            verts.append((math.cos(a)*r,y,math.sin(a)*r))
    for j in range(rings-1):
        for i in range(sides):
            a=j*sides+i; b=j*sides+(i+1)%sides
            faces.append((a,a+sides,b+sides,b))
    mesh=bpy.data.meshes.new("CanalSurface"); mesh.from_pydata(verts,[],faces); mesh.materials.append(canalmat)
    wall=bpy.data.objects.new("EAR_CANAL_WALL",mesh); scene.collection.objects.link(wall)
    for p in mesh.polygons:p.use_smooth=True
    # Inner folds are attached to the side wall, not laid on a flat floor.
    for k in range(7):
        a=-1.15+k*.34
        x=math.cos(a)*.98; z=math.sin(a)*.98
        bpy.ops.mesh.primitive_torus_add(major_radius=.22,minor_radius=.055,major_segments=32,minor_segments=10,location=(x,-1.7+k*.82,z),rotation=(math.pi/2,0,a))
        o=bpy.context.object; o.name="Canal_Ridge_%02d"%k; o.scale=(1,.55,1); o.data.materials.append(ridge)
    # Eardrum at the far end.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=32,radius=1,location=(0,4.65,0))
    drum=bpy.context.object; drum.name="TYMPANIC_MEMBRANE"; drum.scale=(.96,.11,.96); drum.data.materials.append(drumat); bpy.ops.object.shade_smooth()
    # Earwax: irregular deposits adhered to the upper-side canal wall.
    wax=[]
    for n,(loc,sc) in enumerate([
        ((.77,-.45,.45),(.31,.42,.23)),
        ((.79,.02,.50),(.25,.35,.19)),
        ((.72,.43,.48),(.20,.28,.16))
    ]):
        o=ball("WAX_DEPOSIT_%02d"%n,loc,1,waxmat,40,28); o.scale=sc; wax.append(o)
    for n,loc in enumerate([(.67,-.30,.61),(.64,.10,.62),(.62,.42,.58)]):
        ball("Wax_specular_%02d"%n,loc,.045,waxlight,16,10)
    # Cotton swab with an elongated, soft cotton tip and fine visible fibers.
    def rod(name,a,b,r,material):
        va=Vector(a); vb=Vector(b); d=vb-va
        bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=r,depth=d.length,location=(va+vb)/2)
        o=bpy.context.object; o.name=name; o.rotation_euler=d.to_track_quat("Z","Y").to_euler(); o.data.materials.append(material); return o
    shaft=rod("COTTON_SWAB_SHAFT",(-2.35,-2.3,-1.45),(.36,.10,.42),.055,stemmat)
    tip=ball("COTTON_TIP",(.36,.10,.42),.19,cotton,40,28); tip.scale=(.19,.34,.19)
    # Fibrous cotton surface: short tapered strands around the tip.
    random.seed(22)
    for i in range(34):
        a=random.random()*math.tau; z=random.uniform(-.25,.25)
        p1=Vector((.36+math.cos(a)*.14,.10+z,.42+math.sin(a)*.14))
        p2=p1+Vector((math.cos(a)*.07,random.uniform(-.045,.045),math.sin(a)*.07))
        rod("Cotton_Fiber_%02d"%i,p1,p2,.009,cotton)
    # Camera animation is split into distinct beats, not one continuous zoom.
    bpy.ops.object.camera_add(location=(0,-8.5,.15)); cam=bpy.context.object; cam.name="EarJourneyCamera"; cam.data.lens=48; scene.camera=cam
    def camera_shot(frame, loc, target, lens):
        cam.location=loc; aim(cam,target); cam.data.lens=lens
        cam.keyframe_insert(data_path="location",frame=frame)
        cam.keyframe_insert(data_path="rotation_euler",frame=frame)
        cam.data.keyframe_insert(data_path="lens",frame=frame)
    f1=1; f2=int(last*.18); f3=int(last*.40); f4=int(last*.64); f5=int(last*.82); f6=last
    camera_shot(f1,(0,-8.5,.1),(0,-3.5,0),48)
    camera_shot(f2,(0,-5.7,.05),(0,-.2,0),52)
    camera_shot(f3,(-.15,-4.3,.0),(.1,1.0,0),58)
    camera_shot(f4,(-1.35,-3.0,-.15),(.35,.0,.3),54)
    camera_shot(f5,(-.15,-2.7,.05),(.1,3.8,0),62)
    camera_shot(f6,(0,-3.2,.0),(0,4.5,0),54)
    # Swab advances into the canal, contacts the wax, and visibly pushes it inward.
    for obj in (shaft,tip):
        base=obj.location.copy()
        obj.keyframe_insert(data_path="location",frame=f1)
        obj.location=base+Vector((.0,.9,.0)); obj.keyframe_insert(data_path="location",frame=f3)
        obj.location=base+Vector((.12,1.35,.03)); obj.keyframe_insert(data_path="location",frame=f4)
    # Wax shifts deeper along the canal after contact; the change is visible.
    for obj in wax:
        base=obj.location.copy()
        obj.keyframe_insert(data_path="location",frame=f1)
        obj.location=base+Vector((-.06,1.0,-.03)); obj.keyframe_insert(data_path="location",frame=f5)
    # Small animated particles illustrate dust being caught by wax.
    dustmat=mat("Dust particles",(.55,.43,.28),rough=.9)
    for i in range(13):
        x=random.uniform(-.65,.65); z=random.uniform(-.6,.6); y=random.uniform(-1.8,1.3)
        d=ball("TRAPPED_DUST_%02d"%i,(x,y,z),.035,dustmat,12,8)
        d.keyframe_insert(data_path="location",frame=f1)
        d.location.y-=.75; d.keyframe_insert(data_path="location",frame=f3)
    # Lighting, depth and restrained cinematic contrast.
    scene.world.color=(.025,.006,.009)
    for typ,loc,power,size,target in [
        ("AREA",(-4,-4,5),950,4,(0,0,0)),
        ("AREA",(3,1,2),700,3,(0,1,0)),
        ("AREA",(0,4,-3),450,2,(0,3,0))
    ]:
        bpy.ops.object.light_add(type=typ,location=loc); l=bpy.context.object; l.data.energy=power; l.data.shape="DISK"; l.data.size=size; aim(l,target)
    # Render settings optimized for motion quality and speed.
    scene.render.engine="BLENDER_EEVEE"
    scene.eevee.taa_render_samples=16
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="FFMPEG"; scene.render.ffmpeg.format="MPEG4"; scene.render.ffmpeg.codec="H264"
    scene.render.ffmpeg.constant_rate_factor="MEDIUM"; scene.render.ffmpeg.ffmpeg_preset="REALTIME"
    scene.render.filepath=output_path
    scene.render.resolution_x=width; scene.render.resolution_y=height; scene.render.fps=fps
    os.makedirs(os.path.dirname(output_path),exist_ok=True); scene.frame_set(1)
    print("EDUFORGE_EAR_RENDER_START",json.dumps({"frames":last,"resolution":[width,height],"shots":6}),flush=True)
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
