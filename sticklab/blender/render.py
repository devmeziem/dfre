import bpy, math, json, os, sys, argparse
from mathutils import Vector
av=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
p=argparse.ArgumentParser(); p.add_argument("--seed",required=True); p.add_argument("--output",required=True); A=p.parse_args(av)
data=json.load(open(A.seed)); cfg=data["project"]; FPS=int(cfg.get("fps",24)); W=int(cfg.get("width",720)); H=int(cfg.get("height",1280)); LAST=int(FPS*float(cfg.get("duration_seconds",14)))
bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
def mat(n,c,r=.7):
 m=bpy.data.materials.new(n); m.diffuse_color=(*c,1); m.use_nodes=True; m.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value=(*c,1); m.node_tree.nodes.get("Principled BSDF").inputs["Roughness"].default_value=r; return m
def cube(n,loc,dim,m,b=.06):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=bpy.context.object; o.name=n; o.dimensions=dim; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); mod=o.modifiers.new("Soft edges","BEVEL"); mod.width=b; mod.segments=3; o.data.materials.append(m); o.modifiers.new("Weighted normals","WEIGHTED_NORMAL"); return o
def ball(n,loc,sc,m):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,radius=1,location=loc); o=bpy.context.object; o.name=n; o.scale=sc; o.data.materials.append(m)
 for f in o.data.polygons:f.use_smooth=True
 return o
def seg(n,m,r):
 bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=r,depth=1); o=bpy.context.object; o.name=n; o.data.materials.append(m); be=o.modifiers.new("Rounded ends","BEVEL"); be.width=r*.65; be.segments=3; return o
def aim(o,t): o.rotation_euler=(Vector(t)-o.location).to_track_quat("-Z","Y").to_euler()
def putseg(o,a,b,f):
 va=Vector(a); vb=Vector(b); d=vb-va; o.location=(va+vb)/2; o.rotation_euler=d.to_track_quat("Z","Y").to_euler(); o.scale.z=d.length
 o.keyframe_insert(data_path="location",frame=f); o.keyframe_insert(data_path="rotation_euler",frame=f); o.keyframe_insert(data_path="scale",frame=f)
def keyball(o,loc,f): o.location=loc; o.keyframe_insert(data_path="location",frame=f)
# Furnished living room environment
floor=mat("Oak floor",(.30,.18,.12)); wall=mat("Sage walls",(.36,.48,.41)); cream=mat("Cream trim",(.84,.77,.64)); teal=mat("Deep teal sofa",(.035,.12,.15)); orange=mat("Terracotta",(.72,.27,.15)); wood=mat("Walnut",(.22,.12,.07)); blue=mat("Window glass",(.19,.42,.55),.2); green=mat("Plant green",(.12,.34,.18)); white=mat("Porcelain white",(.92,.93,.90),.38); black=mat("Charcoal joints",(.025,.035,.04),.4)
cube("FLOOR",(0,0,-.13),(12,9,.25),floor); cube("BACK_WALL",(0,3.8,3),(12,.2,6),wall); cube("LEFT_WALL",(-5.9,0,3),(.2,8,6),wall); cube("BASEBOARD",(0,3.66,.15),(11.7,.1,.22),cream)
cube("WINDOW_FRAME",(-3.4,3.61,3.5),(2.1,.12,2),cream); cube("WINDOW_GLASS",(-3.4,3.53,3.5),(1.8,.04,1.7),blue); cube("WINDOW_SILL",(-3.4,3.4,2.48),(2.3,.3,.12),wood)
cube("DOOR_FRAME",(3.9,3.58,1.55),(1.55,.18,3.1),cream); door=cube("DOOR",(3.9,3.43,1.55),(1.32,.12,2.9),wood)
ball("DOOR_HANDLE",(4.38,3.32,1.5),(.07,.07,.07),orange)
cube("SOFA_BASE",(-1.8,1.15,.48),(2.4,.95,.55),teal,.15); cube("SOFA_BACK",(-1.8,1.55,1.05),(2.4,.28,1),teal,.15)
for x in [-2.55,-1.8,-1.05]: cube("SOFA_CUSHION",(x,.95,.83),(.68,.65,.2),orange,.1)
cube("COFFEE_TABLE",(0,.45,.48),(1.55,.85,.13),wood)
for x in [-.62,.62]:
 for y in [.15,.75]: cube("TABLE_LEG",(x,y,.23),(.09,.09,.48),wood,.02)
cube("BOOK",(0,.42,.59),(.48,.32,.055),orange,.01)
cube("SIDE_TABLE",(-4,1.5,.55),(.8,.7,.12),wood)
for x in [-4.28,-3.72]: cube("SIDE_TABLE_LEG",(x,1.5,.28),(.08,.08,.5),wood,.02)
ball("LAMP_SHADE",(-4,1.5,1.25),(.27,.27,.35),cream)
bpy.ops.mesh.primitive_cone_add(vertices=24,radius1=.24,radius2=.16,depth=.42,location=(4.8,2.7,.21)); bpy.context.object.name="PLANT_POT"; bpy.context.object.data.materials.append(orange)
for i in range(7):
 a=i*math.tau/7; leaf=ball("PLANT_LEAF",(4.8+math.cos(a)*.18,2.7,.75+math.sin(a)*.13),(.12,.07,.48),green); leaf.rotation_euler[1]=-math.cos(a)*.45
# Rounded white 3D stickman, individually animated limb segments
parts={"head":ball("HERO_HEAD",(0,0,2),(.34,.31,.36),white),"torso":seg("HERO_TORSO",white,.065),"neck":seg("HERO_NECK",white,.045),"hip":ball("HERO_HIP",(0,0,.93),(.23,.18,.18),black)}
ball("HERO_EYE_LEFT",(-.13,-.292,2.06),(.075,.035,.09),black)
ball("HERO_EYE_RIGHT",(.13,-.292,2.03),(.045,.03,.055),black)
ball("HERO_PUPIL_LEFT",(-.12,-.325,2.06),(.025,.012,.035),white)
ball("HERO_PUPIL_RIGHT",(.14,-.321,2.03),(.018,.012,.025),white)
ball("HERO_NOSE",(0,-.355,1.96),(.065,.075,.075),orange)
# Curved, expressive smile on the front of the face
mouth_curve=bpy.data.curves.new("HERO_FUNNY_SMILE","CURVE"); mouth_curve.dimensions="3D"; mouth_curve.bevel_depth=.018; mouth_curve.bevel_resolution=3
sp=mouth_curve.splines.new("POLY"); sp.points.add(8)
for i,pt in enumerate(sp.points):
 x=-.13+i*.0325; z=1.88+.055*(1-(x/.13)**2); pt.co=(x,-.322,z,1)
mouth=bpy.data.objects.new("HERO_SMILE",mouth_curve); bpy.context.collection.objects.link(mouth); mouth.data.materials.append(black)
for n in ["armL1","armL2","armR1","armR2","legL1","legL2","legR1","legR2"]: parts[n]=seg("HERO_"+n,white,.035 if "arm" in n else .045)
for n in ["handL","handR"]: parts[n]=ball("HERO_"+n,(0,0,0),(.12,.12,.12),black)
for n in ["footL","footR"]: parts[n]=ball("HERO_"+n,(0,0,0),(.18,.23,.09),black)
def pose(f,x,phase,walking,raised=False):
 bob=.025*abs(math.sin(phase*2)) if walking else 0
 hipz=.93+bob; tz=1.3+bob
 keyball(parts["head"],(x,0,1.99+bob),f)
 keyball(parts["hip"],(x,0,hipz),f)
 putseg(parts["torso"],(x,0,tz+.18),(x,0,hipz+.10),f)
 putseg(parts["neck"],(x,0,tz+.16),(x,0,1.68+bob),f)
 # Alternating gait: left and right legs are half a cycle apart.
 for side,sign in [("L",-1),("R",1)]:
  legphase=phase if side=="L" else phase+math.pi
  leg_swing=.34*math.sin(legphase) if walking else 0
  knee_lift=.24*max(0,math.sin(legphase)) if walking else 0
  hip=(x+sign*.09,0,hipz-.02)
  knee=(x+sign*.10+leg_swing*.48,0,.52+knee_lift*.45)
  ankle=(x+sign*.10+leg_swing,0,.13+knee_lift)
  putseg(parts["leg"+side+"1"],hip,knee,f)
  putseg(parts["leg"+side+"2"],knee,ankle,f)
  keyball(parts["foot"+side],(ankle[0]+.035,-.065,ankle[2]),f)
  # Arms counter-swing against the legs for a natural walk.
  arm_swing=-.25*math.sin(legphase) if walking else 0
  shoulder=(x+sign*.13,0,tz+.13)
  elbow=(x+sign*.22+arm_swing*.55,0,tz-.16)
  hand=(x+sign*.24+arm_swing,0,tz-.42)
  if raised and side=="R":
   elbow=(x+.30,0,tz+.34); hand=(x+.48,-.02,tz+.62)
  putseg(parts["arm"+side+"1"],shoulder,elbow,f)
  putseg(parts["arm"+side+"2"],elbow,hand,f)
  keyball(parts["hand"+side],hand,f)
walkend=int(LAST*.60); stop=int(LAST*.72)
for f in range(1,LAST+1,2):
 if f<=walkend: pose(f,-3.8+3.2*f/walkend,(f-1)*math.tau/(FPS*.78),True)
 elif f<=stop: pose(f,-.6,0,False)
 else: pose(f,-.6,0,False,True)
pose(LAST,-.6,0,False,True)
door.keyframe_insert(data_path="rotation_euler",frame=1); door.rotation_euler[2]=-.22; door.keyframe_insert(data_path="rotation_euler",frame=walkend)
# Camera changes composition over the timeline
bpy.ops.object.camera_add(location=(0,-12,4)); cam=bpy.context.object; cam.name="STICKLAB_CAMERA"; cam.data.lens=48; bpy.context.scene.camera=cam
def camkey(f,loc,target,lens):
 cam.location=loc; aim(cam,target); cam.data.lens=lens; cam.keyframe_insert(data_path="location",frame=f); cam.keyframe_insert(data_path="rotation_euler",frame=f); cam.data.keyframe_insert(data_path="lens",frame=f)
camkey(1,(0,-12,4),(-.4,1,1.15),48); camkey(int(LAST*.42),(-.4,-10.5,3.4),(-.8,.7,1.1),52); camkey(int(LAST*.72),(-1.2,-8.5,3),(-.6,.4,1.25),58); camkey(LAST,(-1.2,-8.5,3),(-.6,.4,1.25),58)
world=bpy.context.scene.world; world.color=(.16,.16,.16)
bpy.ops.object.light_add(type="AREA",location=(-4,-5,7)); l=bpy.context.object; l.data.energy=1050; l.data.size=6; aim(l,(0,1,1))
bpy.ops.object.light_add(type="AREA",location=(4,2,5)); l=bpy.context.object; l.data.energy=750; l.data.size=5; aim(l,(0,0,1))
scene=bpy.context.scene; scene.frame_start=1; scene.frame_end=LAST; scene.render.fps=FPS; scene.render.engine="BLENDER_EEVEE"; scene.eevee.taa_render_samples=16; scene.render.resolution_x=W; scene.render.resolution_y=H; scene.render.resolution_percentage=100
scene.render.image_settings.file_format="FFMPEG"; scene.render.ffmpeg.format="MPEG4"; scene.render.ffmpeg.codec="H264"; scene.render.ffmpeg.constant_rate_factor="MEDIUM"; scene.render.ffmpeg.ffmpeg_preset="REALTIME"; scene.render.filepath=os.path.abspath(A.output); scene.view_settings.view_transform="Standard"
for obj in scene.objects:
 if obj.animation_data and obj.animation_data.action:
  for fc in obj.animation_data.action.fcurves:
   for kp in fc.keyframe_points: kp.interpolation="BEZIER"
os.makedirs(os.path.dirname(os.path.abspath(A.output)),exist_ok=True)
print("STICKLAB_RENDER_START",json.dumps({"frames":LAST,"resolution":[W,H],"environment":"furnished living room","motion":"walk, stop, wave"}),flush=True)
bpy.ops.render.render(animation=True); print("STICKLAB_RENDER_COMPLETE",A.output,flush=True)
