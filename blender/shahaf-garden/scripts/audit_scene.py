"""Inspect the authored scene and create reproducible review views."""
import bpy
import bmesh
import json
import math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT=Path(__file__).resolve().parents[1]
STATE={}


def write_json(name,data):
    (ROOT/name).write_text(json.dumps(data,indent=2),encoding='utf-8')


def bounds(o):
    points=[o.matrix_world@Vector(p) for p in o.bound_box]
    lo=[min(p[i] for p in points) for i in range(3)];hi=[max(p[i] for p in points) for i in range(3)]
    return {'min':lo,'max':hi,'dimensions':[hi[i]-lo[i] for i in range(3)]}


def audit():
    s=bpy.context.scene;s.camera=bpy.data.objects['SF3D_Production_camera'];s.frame_set(2688);bpy.context.view_layer.update()
    graph=bpy.context.evaluated_depsgraph_get();tris=0
    for o in s.objects:
        if o.type not in ('MESH','CURVE','FONT') or o.hide_render:continue
        evaluated=o.evaluated_get(graph);m=evaluated.to_mesh()
        if m:m.calc_loop_triangles();tris+=len(m.loop_triangles)
        evaluated.to_mesh_clear()
    facade=bpy.data.objects['SF3D_Facade_structure']
    openings=[]
    for id,x,z,w,h in [('door_center',0,.24,1.72,3.25),('window_left',-2.2,.72,1.62,2.64),('window_right',2.2,.72,1.62,2.64)]:
        origin=facade.matrix_world.inverted()@Vector((x,3.7,z+h*.4));hit=facade.ray_cast(origin,Vector((0,1,0)),distance=1.0)[0]
        openings.append({'id':id,'width':w,'height':h,'center_ray_clear':not hit})
    manifold={}
    for name in ('SF3D_Facade_structure','SF3D_Rear_structure','SF3D_Terrace_foundation'):
        o=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(o.data);manifold[name]={'non_manifold_edges':sum(not e.is_manifold for e in bm.edges),'faces':len(bm.faces)};bm.free()
    heads={}
    for who in ('Neria','Shahaf'):
        face=bpy.data.objects['SF3D_'+who+'_face'];points=[world_to_camera_view(s,s.camera,face.matrix_world@Vector(p)) for p in face.bound_box]
        center=face.matrix_world.translation;ray=center-s.camera.matrix_world.translation
        hit,loc,normal,index,obj,matrix=s.ray_cast(graph,s.camera.matrix_world.translation,ray.normalized(),distance=ray.length+.03)
        heads[who]={'inside_frame':all(0<p.x<1 and 0<p.y<1 and p.z>0 for p in points),'first_ray_hit':obj.name if hit else None,'self_visible':bool(hit and obj.name.startswith('SF3D_'+who))}
    contacts={}
    for name in ('SF3D_Chair_leg','SF3D_Chair_leg.001','SF3D_Neria_shoe','SF3D_Shahaf_shoe'):
        if name in bpy.data.objects:contacts[name]={'minimum_z':bounds(bpy.data.objects[name])['min'][2],'floor_z':.243}
    animation=[]
    for seconds in (0,3,6.5,16,28,32,41,44.4,50,84,100,112):
        s.frame_set(max(1,round(seconds*24)));bpy.context.view_layer.update()
        hero=bpy.data.objects['SF3D_Hero_first_bloom'];roses=[o for o in s.objects if o.name.startswith('SF3D_Path_rose_')]
        animation.append({'seconds':seconds,'hero_scale':list(hero.scale),'hero_bloom':hero.data.shape_keys.key_blocks['Bloom'].value,'visible_path_roses':sum(o.scale.z>.005 for o in roses),'cafe_scale':list(bpy.data.objects['SF3D_Conservatory_reveal'].scale)})
    s.frame_set(2688);bpy.context.view_layer.update()
    sound=[x for x in s.sequence_editor.strips if x.type=='SOUND']
    data={'scene':s.name,'objects':len(s.objects),'evaluated_triangles':tris,'duration_seconds':112,'fps':24,'path_roses':len([o for o in s.objects if o.name.startswith('SF3D_Path_rose_')]),'opening_checks':openings,'structural_manifold':manifold,'hero_visibility':heads,'floor_contacts':contacts,'animation_samples':animation,'packed_sound':all(x.sound.packed_file is not None for x in sound),'sound_tracks':len(sound),'render_engine':s.render.engine,'device':s.cycles.device,'production_camera':{'location':list(s.camera.matrix_world.translation),'lens_mm':s.camera.data.lens,'vertical_fov_degrees':42}}
    write_json('geometry-audit.json',data)
    write_json('lighting-manifest.json',{'schema':'shahaf.lighting.v1','fixtures':[{'id':o.name,'type':o.data.type,'location':list(o.matrix_world.translation),'energy':o.data.energy,'color':list(o.data.color)} for o in s.objects if o.type=='LIGHT'],'emissive_materials':[m.name for m in bpy.data.materials if m.name.startswith('SF3D_') and m.use_nodes and any(n.type=='BSDF_PRINCIPLED' and n.inputs['Emission Strength'].default_value>0 for n in m.node_tree.nodes)]})
    return data


VIEWS={
    'corner_front_left':((-9,-9,3.0),(0,1.2,2.5),120),
    'corner_front_right':((9,-9,3.0),(0,1.2,2.5),120),
    'corner_rear_left':((-8,10,3.0),(0,1.2,2.5),120),
    'corner_rear_right':((8,10,3.0),(0,1.2,2.5),120),
    'ceiling_center_up':((0,3.5,1.0),(0,3.5,5.2),100),
    'ceiling_oblique_front':((0,.8,1.0),(0,3.8,4.8),85),
    'ceiling_oblique_rear':((0,5.3,1.9),(0,2.4,4.8),85),
    'floor_plan':((0,0,35),(0,0,0),42),
    'reflected_ceiling':((0,3.6,.7),(0,3.6,5.2),42),
    'facade_elevation':((0,-4,2.8),(0,4.2,2.8),42),
}


def prepare_view(name):
    s=bpy.context.scene
    if not STATE:
        STATE.update({'camera':s.camera,'engine':s.render.engine,'resolution':(s.render.resolution_x,s.render.resolution_y),'samples':s.cycles.samples,'compositor':s.compositing_node_group,'hide':{o.name:o.hide_render for o in s.objects}})
    restore_visibility()
    s.frame_set(2688)
    eye,target,fov=VIEWS[name]
    camera=bpy.data.objects.get('SF3D_Review_'+name)
    if camera is None:
        d=bpy.data.cameras.new('SF3D_Review_'+name);camera=bpy.data.objects.new('SF3D_Review_'+name,d);bpy.data.collections['SF3D_12_Cameras'].objects.link(camera)
    camera.location=eye;camera.rotation_euler=(Vector(target)-Vector(eye)).to_track_quat('-Z','Y').to_euler();camera.data.type='PERSP';camera.data.sensor_fit='VERTICAL';camera.data.sensor_height=24;camera.data.lens=24/(2*math.tan(math.radians(fov)/2));camera.data.dof.use_dof=False
    s.camera=camera;s.render.resolution_x=800;s.render.resolution_y=600;s.cycles.samples=24
    plan=name in ('floor_plan','reflected_ceiling','facade_elevation')
    if plan:
        s.render.engine='BLENDER_WORKBENCH';s.compositing_node_group=None;camera.data.type='ORTHO';camera.data.ortho_scale=31 if name=='floor_plan' else 8.0;s.render.resolution_x=1000;s.render.resolution_y=1000
        sh=s.display.shading;sh.light='FLAT';sh.color_type='SINGLE';sh.single_color=(.84,.84,.84);sh.background_type='WORLD';s.world.color=(1,1,1);sh.show_shadows=False;sh.show_cavity=True;sh.cavity_type='BOTH';sh.show_object_outline=True;sh.object_outline_color=(0,0,0)
        for o in s.objects:
            if any(c.name in ('SF3D_09_Lighting_and_lanterns','SF3D_10_Stars_and_glints','SF3D_11_Butterflies','SF3D_13_Atmosphere') for c in o.users_collection):o.hide_render=True
            if name=='floor_plan' and o.name.startswith(('SF3D_Barrel_glass','SF3D_Canopy_rib','SF3D_Roof_longitudinal','SF3D_Hanging_sign','SF3D_Sign_','SF3D_Arch_floret','SF3D_Arch_vine')):o.hide_render=True
            if name=='reflected_ceiling':
                allowed=o.name.startswith(('SF3D_Barrel_glass','SF3D_Canopy_rib','SF3D_Roof_longitudinal','SF3D_Canopy_post','SF3D_Hanging_sign','SF3D_Sign_','SF3D_Arch_'))
                if o.type in ('MESH','CURVE','FONT'):o.hide_render=not allowed
            if name=='facade_elevation' and o.type in ('MESH','CURVE','FONT'):
                o.hide_render=not o.name.startswith(('SF3D_Facade_structure','SF3D_door_center','SF3D_window_','SF3D_Door_threshold'))
                if o.name.endswith('_glass'):o.hide_render=True
    else:
        s.render.engine='CYCLES';s.compositing_node_group=STATE['compositor']
    bpy.context.view_layer.update()
    return {'review_view':name,'engine':s.render.engine,'resolution':[s.render.resolution_x,s.render.resolution_y]}


def restore_visibility():
    for name,value in STATE.get('hide',{}).items():
        if name in bpy.data.objects:bpy.data.objects[name].hide_render=value


def restore():
    s=bpy.context.scene;restore_visibility()
    if STATE:
        s.camera=STATE['camera'];s.render.engine=STATE['engine'];s.render.resolution_x,s.render.resolution_y=STATE['resolution'];s.cycles.samples=STATE['samples'];s.compositing_node_group=STATE['compositor']
    s.camera=bpy.data.objects['SF3D_Production_camera'];s.frame_set(2688);bpy.context.view_layer.update()
    STATE.clear()
    return {'restored':True,'camera':s.camera.name}
