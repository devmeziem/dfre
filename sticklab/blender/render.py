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
# Modern downtown street with tall skyscrapers on both sides.
asphalt=mat("Dark city asphalt",(.105,.12,.14)); sidewalk=mat("Pale concrete sidewalk",(.48,.50,.50))
curbmat=mat("Concrete curb",(.68,.68,.64)); tower_a=mat("Blue glass tower",(.18,.30,.39)); tower_b=mat("Warm stone tower",(.43,.43,.40))
glass=mat("Blue reflective windows",(.12,.34,.48),.24); glass_lit=mat("Lit office windows",(.78,.68,.40),.3)
steel=mat("Street metal",(.10,.13,.16)); whitepaint=mat("Road markings",(.88,.88,.82))
sky=mat("Bright city sky",(.38,.64,.82))
cube("CITY_STREET_GROUND",(0,0,-.22),(34,22,.38),asphalt)
cube("LEFT_SIDEWALK",(0,-2.35,-.005),(34,1.45,.12),sidewalk,.06)
cube("RIGHT_SIDEWALK",(0,2.35,-.005),(34,1.45,.12),sidewalk,.06)
cube("LEFT_CURB",(0,-1.58,.04),(34,.13,.20),curbmat,.025)
cube("RIGHT_CURB",(0,1.58,.04),(34,.13,.20),curbmat,.025)
# Broken lane divider and a pedestrian crossing add clear street context.
for xx in [-12,-8,-4,0,4,8,12]:
 cube("ROAD_LANE_DASH",(xx,0,.005),(2.0,.10,.018),whitepaint,.01)
for j in range(7):
 cube("CROSSWALK_STRIPE",(-1.1+j*.36,-1.0,.012),(.19,.95,.02),whitepaint,.01)
cube("CITY_SKY_BACKDROP",(0,8,8),(38,.25,22),sky)
# Skyscraper facades frame the street while leaving the character visible.
buildings=[
 (-11.0,5.0,5.0,3.8,12.5,tower_a),(-7.0,6.0,3.4,3.6,9.0,tower_b),
 (7.0,6.0,3.5,3.8,10.5,tower_a),(11.0,5.0,5.0,3.8,14.5,tower_b),
 (-15.5,8.0,3.4,3.4,8.0,tower_b),(15.5,8.0,3.4,3.4,9.0,tower_a)]
for bi,(bx,by,bw,bd,bh,bmat) in enumerate(buildings):
 cube("SKYSCRAPER_%02d"%bi,(bx,by,bh/2),(bw,bd,bh),bmat,.10)
 # Repeated rows of reflective windows on the street-facing facade.
 cols=max(2,int(bw/.58)); rows=max(4,int(bh/.78))
 for row in range(rows):
  z=.65+row*.72
  if z>bh-.25: continue
  for col in range(cols):
   wx=bx-bw/2+.38+col*((bw-.76)/max(1,cols-1))
   wm=glass_lit if (row*3+col+bi)%9==0 else glass
   cube("SKYSCRAPER_WINDOW",(wx,by-bd/2-.018,z),(.27,.035,.40),wm,.018)
# Streetlights on the sidewalks.
for lx in [-9,-3,3,9]:
 cube("STREETLIGHT_POLE",(lx,-2.05,2.15),(.075,.075,4.3),steel,.025)
 cube("STREETLIGHT_ARM",(lx+.30,-2.05,4.22),(.65,.075,.075),steel,.025)
 ball("STREETLIGHT_LAMP",(lx+.60,-2.05,4.18),(.18,.13,.09),glass_lit)
# A few traffic signals at the far crossing.
cube("TRAFFIC_SIGNAL_POLE",(2.5,-1.45,2.0),(.09,.09,4.0),steel,.025)
cube("TRAFFIC_SIGNAL_BOX",(2.5,-1.48,3.45),(.30,.20,.72),steel,.04)
for zz,lightmat in [(3.66,mat("Signal red",(.8,.08,.05))),(3.45,mat("Signal amber",(.95,.55,.06))),(3.24,mat("Signal green",(.08,.65,.20)))]:
 ball("TRAFFIC_SIGNAL_LAMP",(2.5,-1.60,zz),(.075,.035,.075),lightmat)
# A classic line-stickman: oversized round head, single thin-line torso,
# simple line limbs. No torso volume, hip ball, bulky joints, hands or shoes.
white=mat("Porcelain stickman",(.96,.97,.93),.42); ink=mat("Face ink",(.025,.035,.045),.5)
parts={"head":ball("HERO_HEAD",(0,0,2),(.34,.31,.36),white),"torso":seg("HERO_TORSO",white,.027)}
# Hand-drawn stickman face, following the supplied reference:
# clean black ink strokes, expressive curved eyes and a clear open smile.
def face_stroke(name, points, radius=.012):
 curve=bpy.data.curves.new(name,"CURVE"); curve.dimensions="3D"; curve.resolution_u=12
 curve.bevel_depth=radius; curve.bevel_resolution=3
 spline=curve.splines.new("POLY"); spline.points.add(len(points)-1)
 for i,(xx,yy,zz) in enumerate(points): spline.points[i].co=(xx,yy,zz,1)
 obj=bpy.data.objects.new(name,curve); bpy.context.collection.objects.link(obj); obj.data.materials.append(ink)
 obj.parent=parts["head"]; obj.matrix_parent_inverse=parts["head"].matrix_world.inverted()
 return obj
# Happy, curved eyes (not bead-like robot eyes).
face_stroke("HERO_EYE_LEFT",[(-.205,-.292,2.045),(-.18,-.307,2.09),(-.145,-.31,2.105),(-.11,-.307,2.09),(-.09,-.292,2.045)],.013)
face_stroke("HERO_EYE_RIGHT",[(.09,-.292,2.045),(.115,-.307,2.09),(.15,-.31,2.105),(.185,-.307,2.09),(.205,-.292,2.045)],.013)
# Soft expressive brows add the hand-drawn cartoon character.
face_stroke("HERO_BROW_LEFT",[(-.205,-.286,2.15),(-.16,-.30,2.17),(-.11,-.286,2.15)],.009)
face_stroke("HERO_BROW_RIGHT",[(.11,-.286,2.15),(.16,-.30,2.17),(.205,-.286,2.15)],.009)
# Open cheerful mouth with a dark interior and a small white upper-teeth highlight.
mouth_inner=ball("HERO_MOUTH_OPEN",(0,-.302,1.91),(.125,.027,.075),ink)
mouth_inner.parent=parts["head"]; mouth_inner.matrix_parent_inverse=parts["head"].matrix_world.inverted()
teeth=ball("HERO_SMILE_TEETH",(0,-.326,1.944),(.078,.012,.018),white)
teeth.parent=parts["head"]; teeth.matrix_parent_inverse=parts["head"].matrix_world.inverted()
# Tiny cheek marks keep the face warm and illustrated, not mechanical.
face_stroke("HERO_CHEEK_LEFT",[(-.245,-.278,1.96),(-.225,-.29,1.945),(-.205,-.278,1.96)],.006)
face_stroke("HERO_CHEEK_RIGHT",[(.205,-.278,1.96),(.225,-.29,1.945),(.245,-.278,1.96)],.006)

for n in ["armL1","armL2","armR1","armR2","legL","legR"]:
 parts[n]=seg("HERO_"+n,white,.024)
def pose(f,x,phase,walking,raised=False):
 bob=.035*abs(math.sin(phase*2)) if walking else 0
 shoulder_z=1.43+bob; hip_z=.78+bob
 keyball(parts["head"],(x,0,2.02+bob),f)
 putseg(parts["torso"],(x,0,shoulder_z),(x,0,hip_z),f)
 for side,sign in [("L",-1),("R",1)]:
  legphase=phase if side=="L" else phase+math.pi
  swing=.43*math.sin(legphase) if walking else 0
  lift=.16*max(0,math.sin(legphase)) if walking else 0
  hip=(x+sign*.035,0,hip_z)
  ankle=(x+sign*.035+swing,0,.12+lift)
  putseg(parts["leg"+side],hip,ankle,f)
  arm_swing=-.32*math.sin(legphase) if walking else 0
  shoulder=(x+sign*.055,0,shoulder_z-.02)
  elbow=(x+sign*.18+arm_swing*.55,0,1.12+bob)
  hand=(x+sign*.23+arm_swing,0,.96+bob)
  if raised and side=="R":
   elbow=(x+.28,0,1.62); hand=(x+.45,-.01,1.82)
  putseg(parts["arm"+side+"1"],shoulder,elbow,f)
  putseg(parts["arm"+side+"2"],elbow,hand,f)
walkend=int(LAST*.60); stop=int(LAST*.72)
for f in range(1,LAST+1,2):
 if f<=walkend: pose(f,-3.8+3.2*f/walkend,(f-1)*math.tau/(FPS*.78),True)
 elif f<=stop: pose(f,-.6,0,False)
 else: pose(f,-.6,0,False,True)
pose(LAST,-.6,0,False,True)
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
print("STICKLAB_RENDER_START",json.dumps({"frames":LAST,"resolution":[W,H],"environment":"sunny neighborhood park","motion":"walk, stop, wave"}),flush=True)
bpy.ops.render.render(animation=True); print("STICKLAB_RENDER_COMPLETE",A.output,flush=True)
