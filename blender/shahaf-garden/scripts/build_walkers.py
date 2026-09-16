"""Author articulated walking parts in a separate Blender scene and asset.

Run in a background copy of Shahaf_Garden_v001.blend. The garden file is never
overwritten. Faces, hair, clothing details and materials come from that scene.
"""
import bpy
import math
import json
from pathlib import Path
from mathutils import Vector,Matrix

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT.parents[1]/'garden'/'assets';DEST.mkdir(exist_ok=True,parents=True)
source_scene=bpy.context.scene;source_scene.frame_set(900);bpy.context.view_layer.update()
source=ROOT/'scripts'/'build_scene.py';ns={'__file__':str(source),'__name__':'walker_helpers'}
exec(compile(source.read_text(encoding='utf-8'),str(source),'exec'),ns)
ns['MATS']={m.name.removeprefix('SF3D_'):m for m in bpy.data.materials if m.name.startswith('SF3D_')}
originals={o.name:o for o in source_scene.objects}

# Evaluate copied geometry while the original scene and its dependencies are active.
def copy_geometry(objects,reference,offset=(0,0,0)):
    graph=bpy.context.evaluated_depsgraph_get();inverse=reference.matrix_world.inverted();result=[]
    for o in objects:
        if o.type not in ('MESH','CURVE','FONT') or o.hide_render:continue
        data=bpy.data.meshes.new_from_object(o.evaluated_get(graph),preserve_all_data_layers=True,depsgraph=graph)
        data.materials.clear()
        for slot in o.material_slots:data.materials.append(slot.material)
        data.transform(Matrix.Translation(-Vector(offset))@inverse@o.matrix_world);data.update();result.append(data)
    return result

pieces={}
for who in ('Neria','Shahaf'):
    root=originals['SF3D_'+who+'_pose'];head=originals['SF3D_'+who+'_head']
    upper=[o for o in root.children if o.name.startswith(tuple('SF3D_'+who+'_'+p for p in ('torso','neck','shirt_')))]
    pieces[who]={'head':copy_geometry(head.children_recursive,head),'torso':copy_geometry(upper,root,(0,0,.91)),
                 'hip':copy_geometry([originals['SF3D_'+who+'_hip']],root,(0,.05,.59))}

s=bpy.data.scenes.new('Shahaf_Walking_Characters');bpy.context.window.scene=s
s.render.engine='CYCLES';s.cycles.device='GPU';s.cycles.samples=64;s.render.resolution_x=1200;s.render.resolution_y=1000;s.render.resolution_percentage=100
s.render.fps=24;s.frame_start=1;s.frame_end=48
s.world=bpy.data.worlds.new('Walking_cast_world');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.025,.035,.065,1);s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.4
s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=.4
actors=[];export_objects=[]

def joined_part(actor,part,data_list,parent):
    objects=[]
    for i,data in enumerate(data_list):
        o=bpy.data.objects.new('Walking_piece',data);ns['COL'].objects.link(o);objects.append(o)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    if len(objects)>1:bpy.ops.object.join()
    o=objects[0];o.name='SF3D_Walk_'+actor+'_'+part;o.parent=parent;o['rtActor']=actor;o['rtPart']=part;export_objects.append(o)
    return o

def tag(o,actor,part):
    o['rtActor']=actor;o['rtPart']=part;export_objects.append(o);return o

def hand_data(skin):
    before=set(ns['COL'].objects)
    ns['ball']('Walk_palm',(0,0,0),(.035,.048,.021),skin)
    for finger in range(4):
        x=(finger-1.5)*.013;length=.038-.004*abs(finger-1.5)
        points=[(x,.026,0),(x,.026+length*.55,-.007),(x,.026+length,-.021),(x,.023+length*.80,-.037)]
        for j in range(3):ns['tube']('Walk_finger',points[j],points[j+1],.0058,skin)
        ns['ball']('Walk_knuckle',points[1],(.0064,)*3,skin)
    thumb=ns['ball']('Walk_thumb',(.032,.005,-.014),(.012,.028,.011),skin);thumb.rotation_euler.y=.45
    made=[o for o in ns['COL'].objects if o not in before];bpy.context.view_layer.update()
    graph=bpy.context.evaluated_depsgraph_get();data=[]
    for o in made:
        d=bpy.data.meshes.new_from_object(o.evaluated_get(graph),preserve_all_data_layers=True,depsgraph=graph)
        d.materials.clear()
        for slot in o.material_slots:d.materials.append(slot.material)
        d.transform(o.matrix_world);data.append(d)
    for o in made:bpy.data.objects.remove(o,do_unlink=True)
    return data

for side,who in [(-1,'Neria'),(1,'Shahaf')]:
    female=side==1;actor=who.lower();ns['collection']('Walking_'+who)
    root=ns['empty']('Walk_'+who,(side*.37,0,0));root['rtActorRoot']=actor;export_objects.append(root)
    skin=ns['MATS']['SkinRose' if female else 'Skin'];cloth=ns['MATS']['Dress' if female else 'Shirt'];pants=skin if female else ns['MATS']['Trousers']
    parts={p:joined_part(actor,p,pieces[who][p],root) for p in ('head','torso','hip')}
    # Keep the seated anatomy available as a morph while fitting the standing
    # silhouette. This also closes the dress cleanly at its waistband.
    hip_mesh=parts['hip'];hip_seated=[v.co.copy() for v in hip_mesh.data.vertices]
    for v in hip_mesh.data.vertices:v.co.x*=.76 if female else .86;v.co.y*=.66 if female else .70;v.co.z*=.86 if female else .75
    hip_mesh.shape_key_add(name='Standing');hip_key=hip_mesh.shape_key_add(name='Seated');hip_key.data.foreach_set('co',[n for v in hip_seated for n in v])
    head_mesh=parts['head'];head_mesh.shape_key_add(name='Neutral');blink=head_mesh.shape_key_add(name='Blink');smile=head_mesh.shape_key_add(name='Smile')
    eye_vertices=set();lip_vertices=set()
    for poly in head_mesh.data.polygons:
        name=head_mesh.data.materials[poly.material_index].name
        if name in ('SF3D_Eye','SF3D_Porcelain'):eye_vertices.update(poly.vertices)
        if name=='SF3D_Lips':lip_vertices.update(poly.vertices)
    for index in eye_vertices:blink.data[index].co.z=.026+(blink.data[index].co.z-.026)*.04
    for index in lip_vertices:
        weight=min(1,abs(smile.data[index].co.x)/.04)**1.2;smile.data[index].co.z+=.012*weight;smile.data[index].co.y+=.008*weight
    smile.value=.45
    for part,mat,geo in [('waist',cloth,'cylinder')]:parts[part]=tag(ns['obj_mesh']('Walk_'+actor+'_'+part,ns['primitive_mesh'](geo),mat=mat,parent=root),actor,part)
    if female:
        vertices=[];seated=[];faces=[];n=64
        for j in range(9):
            v=j/8;r=.163+.137*v
            for i in range(n):
                a=i/n*math.tau;wave=.010*math.sin(a*14)*v
                vertices.append((math.cos(a)*(r+wave),math.sin(a)*(r+wave),.06-v*.47))
                seated.append((math.cos(a)*(.22+.10*v+wave),.07+math.sin(a)*(.22+.10*v+wave)*1.22,.15-v*.30))
        for j in range(8):
            for i in range(n):faces.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
        skirt=tag(ns['obj_mesh']('Walk_shahaf_skirt',ns['mesh_data']('Walk_skirt',vertices,faces),mat=cloth,parent=root),actor,'skirt')
        skirt.shape_key_add(name='Standing');key=skirt.shape_key_add(name='Seated');key.data.foreach_set('co',[p for v in seated for p in v]);parts['skirt']=skirt
    hand=hand_data(skin)
    for sign,label in [(-1,'left'),(1,'right')]:
        for part,mat,geo in [('upper_arm',skin if female else cloth,'cylinder'),('forearm',skin if female else cloth,'cylinder'),('elbow',skin if female else cloth,'sphere'),('shoulder',skin if female else cloth,'sphere'),('thigh',pants,'cylinder'),('shin',pants,'cylinder'),('knee',pants,'sphere'),('shoe',ns['MATS']['Shoe'],'sphere')]:
            key=label+'_'+part;parts[key]=tag(ns['obj_mesh']('Walk_'+actor+'_'+key,ns['primitive_mesh'](geo),mat=mat,parent=root),actor,key)
        hand_part=joined_part(actor,label+'_hand',[d.copy() for d in hand],root);parts[label+'_hand']=hand_part
        hand_part.shape_key_add(name='Holding');opened=hand_part.shape_key_add(name='Open')
        for point in opened.data:
            if point.co.y>.025:point.co.z*=.06
    actors.append({'actor':actor,'side':side,'root':root,'parts':parts,'female':female})

def joint(a,b,upper,lower,preferred):
    delta=b-a;distance=max(.01,min(delta.length,upper+lower-.001));direction=delta.normalized();along=(upper*upper-lower*lower+distance*distance)/(2*distance)
    bend=(preferred-direction*preferred.dot(direction)).normalized()
    return a+direction*along+bend*math.sqrt(max(0,upper*upper-along*along))

def rod(o,a,b,r):
    o.location=(a+b)*.5;o.rotation_mode='QUATERNION';o.rotation_quaternion=(b-a).to_track_quat('Z','Y');o.scale=(r,r,(b-a).length)

def pose_cast(cast,phase):
    p=cast['parts'];female=cast['female'];side=cast['side'];height=-.05 if female else 0
    chest=1.285+height;hip=.94+height;bob=.012*math.sin(phase*math.tau*2)
    p['torso'].location=(0,0,chest+bob);p['head'].location=(0,-.01,chest+.50+bob);p['head'].rotation_euler.z=side*.95
    p['hip'].location=(0,0,hip+bob);p['waist'].location=(0,0,(hip+chest-.07)*.5+bob);p['waist'].scale=(.163,.127,chest-hip+.03)
    if female:p['skirt'].location=(0,0,hip+bob)
    for sign,label in [(-1,'left'),(1,'right')]:
        inner=sign==-side;sh=Vector((sign*.18,.015,chest+.16+bob));wrist=Vector((-side*.37+side*.014,.055,1.04)) if inner else Vector((sign*.275,.025+sign*math.sin(phase*math.tau)*.10,chest-.39+bob))
        elbow=joint(sh,wrist,.275,.265,Vector((sign*.1,.22,0)))
        rod(p[label+'_upper_arm'],sh,elbow,.050 if female else .057);rod(p[label+'_forearm'],elbow,wrist,.039 if female else .044)
        p[label+'_shoulder'].location=sh;p[label+'_shoulder'].scale=(.053 if female else .062,)*3
        p[label+'_elbow'].location=elbow;p[label+'_elbow'].scale=(.050 if female else .055,)*3
        p[label+'_hand'].location=wrist;p[label+'_hand'].rotation_euler.y=-side*math.pi/2 if inner else 0
        cycle=(phase+(0 if sign==1 else .5))%1
        if cycle<.6:forward=.21-cycle*.70;lift=0
        else:u=(cycle-.6)/.4;forward=-.21+.42*(u*u*(3-2*u));lift=.085*math.sin(u*math.pi)
        a=Vector((sign*.115,.02,hip-.025+bob));b=Vector((sign*.135,forward+.035,.090+lift));knee=joint(a,b,.415 if female else .445,.405 if female else .425,Vector((0,1,0)))
        rod(p[label+'_thigh'],a,knee,.065 if female else .083);rod(p[label+'_shin'],knee,b,.043 if female else .057)
        p[label+'_knee'].location=knee;p[label+'_knee'].scale=(.063 if female else .079,)*3
        p[label+'_shoe'].location=(sign*.135,forward+.095,.050+lift);p[label+'_shoe'].scale=(.066,.12,.05)

for frame in range(1,49,2):
    for cast in actors:
        pose_cast(cast,(frame-1)/48)
        for o in cast['parts'].values():
            for prop in ('location','scale','rotation_quaternion' if o.rotation_mode=='QUATERNION' else 'rotation_euler'):o.keyframe_insert(prop,frame=frame)
s.frame_set(1);bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT')
for o in export_objects:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(DEST/'walking-cast.glb'),export_format='GLB',use_selection=True,export_animations=False,export_current_frame=True,export_apply=False,export_yup=True,export_morph=True,export_morph_normal=True,export_extras=True,export_cameras=False,export_lights=False,export_meshopt_compression_enable=True)

# A lit portrait setup stays in the authoring file, outside the exported cast.
ns['collection']('Walking_portrait')
floor=ns['material']('Walking_floor','#27333d',.86)
ns['cylinder']('Walking_stage',(0,0,-.08),2.0,.15,floor)
ns['light']('Walking_key','AREA',(2,3,4),'#ffdfbd',450,3,(0,0,1.0))
ns['light']('Walking_rim','AREA',(-2,-2,3),'#b9c9ff',700,3,(0,0,1.0))
data=bpy.data.cameras.new('Walking_cast_camera');camera=bpy.data.objects.new('Walking_cast_camera',data);ns['COL'].objects.link(camera);camera.location=(2.9,5.7,2.4);camera.rotation_euler=(Vector((0,0,1))-camera.location).to_track_quat('-Z','Y').to_euler();data.lens=56;s.camera=camera
s['purpose']='Articulated parts for hand-holding walk; native 48-frame pose preview.'
script=bpy.data.texts.new('Walking_cast_source.py');script.write(Path(__file__).read_text(encoding='utf-8'))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Shahaf_Walking_Characters_v001.blend'),compress=True)
report={'actors':2,'partsPerActor':{a['actor']:len(a['parts']) for a in actors},'previewFrames':48,'gltfBytes':(DEST/'walking-cast.glb').stat().st_size,'sourceGardenUnchanged':True}
(DEST/'walking-cast.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print('SHAHAF_WALKING_CAST '+json.dumps(report),flush=True)
