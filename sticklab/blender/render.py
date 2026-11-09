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
# Believable downtown avenue: a long road, raised pavements, street furniture
# and layered buildings that recede toward a clear vanishing point.
asphalt=mat("Sunlit medium grey asphalt",(.43,.45,.46)); sidewalk=mat("Light concrete pavement",(.68,.69,.66))
curbmat=mat("Pale stone curb",(.68,.68,.64)); tower_a=mat("Blue glass facade",(.19,.31,.39))
tower_b=mat("Warm concrete facade",(.43,.42,.39)); glass=mat("Reflective blue windows",(.10,.28,.39),.22)
glass_lit=mat("Warm office windows",(.78,.67,.43),.3); steel=mat("Street furniture metal",(.10,.12,.14))
whitepaint=mat("Road paint",(.84,.85,.81)); sky=mat("Daylight sky",(.39,.65,.82))
cube("CITY_ROAD",(0,6,-.23),(22,34,.42),asphalt)
cube("LEFT_PAVEMENT",(-5.2,6,-.02),(2.1,34,.18),sidewalk,.08)
cube("RIGHT_PAVEMENT",(5.2,6,-.02),(2.1,34,.18),sidewalk,.08)
cube("LEFT_KERB",(-4.12,6,.035),(.16,34,.18),curbmat,.025)
cube("RIGHT_KERB",(4.12,6,.035),(.16,34,.18),curbmat,.025)
# Perspective lane markings and a proper zebra crossing in the foreground.
for yy in [-2,2,6,10,14]:
 cube("LANE_DASH_LEFT",(-.72,yy,.002),(.09,1.7,.018),whitepaint,.01)
 cube("LANE_DASH_RIGHT",(.72,yy,.002),(.09,1.7,.018),whitepaint,.01)
for j in range(9):
 cube("ZEBRA_CROSSING",(-1.45+j*.36,-1.55,.015),(.20,1.05,.025),whitepaint,.01)
# Tall buildings sit along both sides and progressively narrow toward the horizon.
buildings=[
 (-6.6,1.0,3.0,3.2,16.0,tower_a),(-6.2,7.0,2.6,3.0,12.0,tower_b),
 (-7.3,13.0,2.4,2.8,9.0,tower_a),
 (6.6,1.0,3.0,3.2,19.0,tower_b),(6.2,7.0,2.6,3.0,13.0,tower_a),
 (7.3,13.0,2.4,2.8,10.0,tower_b),
 (-9.0,5.0,2.2,3.0,11.0,tower_b),(9.0,5.0,2.2,3.0,14.0,tower_a)]
for bi,(bx,by,bw,bd,bh,bmat) in enumerate(buildings):
 cube("CITY_BUILDING_%02d"%bi,(bx,by,bh/2),(bw,bd,bh),bmat,.045)
 # Recessed-looking vertical window grid on the street-facing wall.
 cols=max(2,int(bw/.43)); rows=max(5,int(bh/.68))
 for row in range(rows):
  z=.62+row*.64
  if z>bh-.25: continue
  for col in range(cols):
   wx=bx-bw/2+.28+col*((bw-.56)/max(1,cols-1))
   wm=glass_lit if (row*5+col*3+bi)%13==0 else glass
   cube("OFFICE_WINDOW",(wx,by-bd/2-.025,z),(.22,.045,.39),wm,.012)
 # Roofline ledge gives each building a finished architectural silhouette.
 cube("BUILDING_ROOFLINE",(bx,by,bh+.08),(bw+.12,bd+.12,.16),curbmat,.025)
# Sidewalk streetlights and trees add familiar city scale.
for side in [-1,1]:
 for yy in [0,6,12]:
  lx=side*4.65
  cube("LAMP_POST",(lx,yy,2.2),(.065,.065,4.4),steel,.02)
  cube("LAMP_ARM",(lx-side*.25,yy,4.28),(.55,.065,.065),steel,.02)
  ball("LAMP_HEAD",(lx-side*.50,yy,4.25),(.18,.12,.08),glass_lit)
# A few street trees in square pavement planters.
for side in [-1,1]:
 for yy in [3,10]:
  tx=side*5.45
  cube("TREE_PLANTER",(tx,yy,.10),(.95,.95,.20),curbmat,.05)
  cube("STREET_TREE_TRUNK",(tx,yy,.95),(.16,.16,1.7),mat("Tree bark",(.25,.16,.10)),.035)
  ball("STREET_TREE_CROWN",(tx,yy,2.05),(.72,.65,.9),mat("Street tree foliage",(.15,.34,.19)))
# Traffic lights at the crossing.
for side in [-1,1]:
 tx=side*3.9
 cube("SIGNAL_POLE",(tx,-1.0,1.8),(.08,.08,3.6),steel,.02)
 cube("SIGNAL_BOX",(tx,-1.0,3.15),(.28,.20,.65),steel,.025)
 for z,clr in [(3.34,mat("Red signal",(.8,.07,.04))),(3.15,mat("Amber signal",(.9,.48,.04))),(2.96,mat("Green signal",(.08,.55,.17)))]:
  ball("SIGNAL_LENS",(tx,-1.12,z),(.065,.035,.065),clr)
# The hero is deliberately 2D ink strokes: no mesh body, spheres, rods or cylinders.
ink=mat("Bold black hand-drawn ink",(.003,.004,.006),.45)
def stroke(name, radius=.026, cyclic=False):
 cu=bpy.data.curves.new(name,"CURVE"); cu.dimensions="3D"; cu.resolution_u=1
 cu.bevel_depth=radius; cu.bevel_resolution=2
 sp=cu.splines.new("POLY"); sp.points.add(1); sp.use_cyclic_u=cyclic
 ob=bpy.data.objects.new(name,cu); bpy.context.collection.objects.link(ob); ob.data.materials.append(ink)
 return ob
def setstroke(ob,pts,frame):
 sp=ob.data.splines[0]
 while len(sp.points)<len(pts): sp.points.add(1)
 while len(sp.points)>len(pts): sp.points.remove(sp.points[-1])
 for i,pnt in enumerate(pts):
  sp.points[i].co=(pnt[0],pnt[1],pnt[2],1)
  sp.points[i].keyframe_insert(data_path="co",frame=frame)
# A slightly uneven head outline, drawn like a quick pen sketch.
head=stroke("INK_HEAD_OUTLINE",.027,True)
eyes_l=stroke("INK_EYE_LEFT",.021); eyes_r=stroke("INK_EYE_RIGHT",.021)
brow_l=stroke("INK_BROW_LEFT",.018); brow_r=stroke("INK_BROW_RIGHT",.018)
mouth=stroke("INK_SMILE",.024); cheek_l=stroke("INK_CHEEK_LEFT",.014); cheek_r=stroke("INK_CHEEK_RIGHT",.014)
torso=stroke("INK_BODY",.024); arm_l=stroke("INK_ARM_LEFT",.022); arm_r=stroke("INK_ARM_RIGHT",.022)
leg_l=stroke("INK_LEG_LEFT",.024); leg_r=stroke("INK_LEG_RIGHT",.024)
hand_l=stroke("INK_HAND_LOOP_LEFT",.019,True); hand_r=stroke("INK_HAND_LOOP_RIGHT",.019,True)
# Each line is redrawn at every keyframe, preserving the loose sketch aesthetic.
def pose(f,x,phase,walking,raised=False):
 bob=.035*abs(math.sin(phase*2)) if walking else 0
 headz=2.02+bob; shoulder=headz-.48; hip=headz-1.20
 def p(localx,z,y=-.18): return (x+localx,y,z)
 # An intentionally imperfect hand-drawn circle, slightly lopsided.
 outline=[]
 for i in range(32):
  t=math.tau*i/32
  wobble=1+.035*math.sin(3*t+.4)+.018*math.sin(7*t)
  outline.append(p(.34*math.cos(t)*wobble,headz+.36*math.sin(t)*wobble,-.20))
 setstroke(head,outline+[outline[0]],f)
 # Friendly cartoon face: curved eyes, uneven brows and a broad open smile.
 setstroke(eyes_l,[p(-.20,headz+.055,-.225),p(-.17,headz+.105,-.23),p(-.13,headz+.10,-.23),p(-.10,headz+.045,-.225)],f)
 setstroke(eyes_r,[p(.08,headz+.045,-.225),p(.115,headz+.105,-.23),p(.16,headz+.10,-.23),p(.195,headz+.035,-.225)],f)
 setstroke(brow_l,[p(-.22,headz+.19,-.22),p(-.16,headz+.215,-.23),p(-.10,headz+.18,-.22)],f)
 setstroke(brow_r,[p(.09,headz+.18,-.22),p(.15,headz+.21,-.23),p(.22,headz+.17,-.22)],f)
 setstroke(mouth,[p(-.14,headz-.10,-.23),p(-.09,headz-.18,-.24),p(0,headz-.205,-.24),p(.09,headz-.17,-.24),p(.14,headz-.09,-.23)],f)
 setstroke(cheek_l,[p(-.27,headz-.08,-.22),p(-.24,headz-.10,-.23),p(-.21,headz-.08,-.22)],f)
 setstroke(cheek_r,[p(.21,headz-.08,-.22),p(.24,headz-.10,-.23),p(.27,headz-.08,-.22)],f)
 setstroke(torso,[p(-.015,shoulder),p(.015,shoulder-.28),p(-.005,hip)],f)
 for side,sign in [("L",-1),("R",1)]:
  lp=phase if side=="L" else phase+math.pi
  swing=.42*math.sin(lp) if walking else 0
  lift=.15*max(0,math.sin(lp)) if walking else 0
  shoulder_pt=p(sign*.025,shoulder)
  elbow=p(sign*(.20+.16*math.sin(lp+math.pi/2) if walking else .20),shoulder-.22)
  hand=p(sign*(.24+swing),1.02+bob+lift)
  if raised and side=="R":
   elbow=p(.28,shoulder+.13); hand=p(.48,shoulder+.42)
  arm=arm_l if side=="L" else arm_r
  loop=hand_l if side=="L" else hand_r
  setstroke(arm,[shoulder_pt,elbow,hand],f)
  # Irregular little loop at the end of each arm, never a perfect ball.
  hx,hy,hz=hand
  looppts=[(hx+dx,hy-.012,hz+dz) for dx,dz in [(-.075,.00),(-.055,.055),(-.01,.072),(.045,.045),(.067,-.005),(.035,-.052),(-.025,-.06),(-.065,-.03)]]
  setstroke(loop,looppts,f)
  hippt=p(-.015,hip)
  ankle=p(sign*.02+swing,.10+lift)
  knee=p(sign*(.11+swing*.48),.46+lift*.45)
  leg=leg_l if side=="L" else leg_r
  setstroke(leg,[hippt,knee,ankle],f)
walkend=int(LAST*.60); stop=int(LAST*.72)
for f in range(1,LAST+1,2):
 if f<=walkend: pose(f,-1.35+1.0*f/walkend,(f-1)*math.tau/(FPS*.78),True)
 elif f<=stop: pose(f,-.6,0,False)
 else: pose(f,-.6,0,False,True)
pose(LAST,-.35,0,False,True)
# Camera changes composition over the timeline
bpy.ops.object.camera_add(location=(0,-12,4)); cam=bpy.context.object; cam.name="STICKLAB_CAMERA"; cam.data.lens=38; bpy.context.scene.camera=cam
def camkey(f,loc,target,lens):
 cam.location=loc; aim(cam,target); cam.data.lens=lens; cam.keyframe_insert(data_path="location",frame=f); cam.keyframe_insert(data_path="rotation_euler",frame=f); cam.data.keyframe_insert(data_path="lens",frame=f)
camkey(1,(0,-13,4.2),(0,1,1.35),38); camkey(int(LAST*.42),(0,-12,4.0),(0,1,1.3),38); camkey(int(LAST*.72),(0,-12,4.0),(0,1,1.3),38); camkey(LAST,(0,-12,4.0),(0,1,1.3),38)
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
print("STICKLAB_RENDER_START",json.dumps({"frames":LAST,"resolution":[W,H],"environment":"downtown avenue with skyscrapers","motion":"walk, stop, wave"}),flush=True)
bpy.ops.render.render(animation=True); print("STICKLAB_RENDER_COMPLETE",A.output,flush=True)
