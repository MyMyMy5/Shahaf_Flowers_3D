"""Export a browser candidate from a background copy of the authoring scene.

The .blend is never saved here. Flowers use three morph-capable prototypes and
an instance manifest. Procedural material bumps remain an explicit runtime task.
"""
import bpy
import json
import math
import re
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT.parents[1]/'garden'/'assets';DEST.mkdir(parents=True,exist_ok=True)
source=ROOT/'scripts'/'build_scene.py'
ns={'__file__':str(source),'__name__':'web_export_helpers'}
exec(compile(source.read_text(encoding='utf-8'),str(source),'exec'),ns)
ns['MATS']={m.name.removeprefix('SF3D_'):m for m in bpy.data.materials if m.name.startswith('SF3D_')}
s=bpy.context.scene;s.frame_set(2688);bpy.context.view_layer.update()
flower_roles={'path red rose':'rose','fantasy garden blossom':'garden','opening hero flower with animated petal shape key':'hero'}
instances=[];fireflies=[];lights=[];pivots={}
selected=[]

def runtime_group(o,collection):
    chain=[];ancestor=o
    while ancestor:
        chain.append(ancestor);ancestor=ancestor.parent
    for ancestor in chain:
        if re.fullmatch(r'SF3D_(Butterfly_\d\d|Floating_paper_lantern_\d\d)',ancestor.name):
            return 'dynamic:'+ancestor.name
        if ancestor.name in ('SF3D_Chair_Neria','SF3D_Chair_Shahaf'):
            key='chair_'+('left' if ancestor.name.endswith('Neria') else 'right');p=ancestor.matrix_world.translation;pivots[key]=[p.x,p.z,-p.y];return key
    for who in ('Neria','Shahaf'):
        if any(a.name.startswith('SF3D_'+who) for a in chain):
            head=next((a for a in chain if a.name=='SF3D_'+who+'_head'),None)
            pivot=head or bpy.data.objects['SF3D_'+who+'_pose']
            key=who.lower()+('_head' if head else '_body');p=pivot.matrix_world.translation
            pivots[key]=[p.x,p.z,-p.y]
            return key
    if o.name.startswith('SF3D_Path_stone_'):return 'path'
    if o.name.startswith(('SF3D_Terrace_','SF3D_Entrance_step_')):return 'terrace'
    if o.name=='SF3D_Garden_terrain':return 'terrain'
    if o.name=='SF3D_Meadow_blades':return 'grass'
    if collection=='SF3D_02_Conservatory':return 'conservatory'
    if collection=='SF3D_03_Table_for_two':return 'chairs' if 'Chair' in o.name else 'table'
    if collection=='SF3D_07_Climbing_flowers':return 'climbing'
    if collection=='SF3D_09_Lighting_and_lanterns':return 'lamps'
    return collection
for o in list(s.objects):
    role=o.get('role')
    if role in flower_roles:
        loc,rot,scale=o.matrix_world.decompose()
        mat=o.data.materials[0]
        instances.append({'name':o.name,'kind':flower_roles[role],'position':[loc.x,loc.z,-loc.y],
            'quaternion':[rot.x,rot.z,-rot.y,rot.w],'scale':list(scale),
            'color':list(mat.diffuse_color[:3]),'start':o.get('growth_start_seconds',0)})
        continue
    if o.type=='LIGHT':
        lights.append({'name':o.name,'type':o.data.type,'position':[o.matrix_world.translation.x,o.matrix_world.translation.z,-o.matrix_world.translation.y],'energy':o.data.energy,'color':list(o.data.color)})
        continue
    if o.name.startswith('SF3D_Garden_firefly'):
        p=o.matrix_world.translation;fireflies.append([p.x,p.z,-p.y]);continue
    collections=[c.name for c in o.users_collection]
    if any(c in ('SF3D_10_Stars_and_glints','SF3D_13_Atmosphere','SF3D_14_Cinematic_details','SF3D_12_Cameras') for c in collections):continue
    if o.type not in ('MESH','CURVE','FONT','EMPTY'):continue
    if o.hide_render:continue
    if o.name in ('SF3D_Neria_chin','SF3D_Shahaf_chin'):continue
    o['rtCollection']=collections[0] if collections else ''
    o['rtGroup']=runtime_group(o,o['rtCollection'])
    if o.type=='FONT':
        o.data.resolution_u=4;o.data.extrude=0;o.data.bevel_depth=0
    elif o.type=='CURVE':
        o.data.bevel_resolution=0 if o.data.bevel_depth<.018 else 1
    for mod in o.modifiers:
        if mod.type=='SUBSURF':mod.show_viewport=False;mod.show_render=False
        if mod.type=='BEVEL' and o.name.startswith('SF3D_Terrace_tile_'):mod.segments=1
    # These blossoms are only a few pixels tall in the browser; their authoring
    # tessellation otherwise costs more triangles than the entire conservatory.
    if o.type=='MESH' and o.name.startswith(('SF3D_Pillar_floret','SF3D_Arch_floret')) and len(o.data.polygons)>1000:
        decimate=o.modifiers.new('Browser climbing blossom LOD','DECIMATE');decimate.ratio=.10
    elif o.type=='MESH' and o.get('role')=='table vase rose':
        decimate=o.modifiers.new('Browser vase blossom LOD','DECIMATE');decimate.ratio=.15
    elif o.type=='MESH' and o.name.startswith('SF3D_Terrace_tile_'):
        decimate=o.modifiers.new('Browser tile bevel LOD','DECIMATE');decimate.ratio=.32
    elif o.type=='MESH' and o.name.startswith('SF3D_Shelf_ceramic'):
        decimate=o.modifiers.new('Browser distant crockery LOD','DECIMATE');decimate.ratio=.15
    elif o.type=='MESH' and o.name.startswith('SF3D_Stemmed_glass'):
        decimate=o.modifiers.new('Browser glass rim LOD','DECIMATE');decimate.ratio=.50
    elif o.type=='MESH' and max(o.dimensions)<.18 and len(o.data.polygons)>200:
        decimate=o.modifiers.new('Browser tiny prop LOD','DECIMATE');decimate.ratio=.20
    elif o.type=='MESH' and o['rtGroup'].endswith('_body') and any(part in o.name for part in ('_upper_arm','_forearm','_thigh','_lower_leg','_neck','_shoe')):
        decimate=o.modifiers.new('Browser seated limb LOD','DECIMATE');decimate.ratio=.50
    selected.append(o)

# Evaluate non-botanical modifiers in this unsaved export process so bevels and
# real Boolean holes survive. Original meshes and the authoring file stay intact.
bpy.context.view_layer.update();graph=bpy.context.evaluated_depsgraph_get()
for o in selected:
    if o.type in ('MESH','CURVE','FONT'):
        evaluated=o.evaluated_get(graph)
        data=bpy.data.meshes.new_from_object(evaluated,preserve_all_data_layers=True,depsgraph=graph)
        if o.type=='MESH':
            o.data=data;o.modifiers.clear()
        else:
            replacement=bpy.data.objects.new(o.name+'_web',data);s.collection.objects.link(replacement)
            replacement.parent=o.parent;bpy.context.view_layer.update()
            replacement.matrix_world=o.matrix_world.copy();replacement['rtCollection']=o['rtCollection']
            replacement['rtGroup']=o['rtGroup']
            replacement['sourceName']=o.name;selected.append(replacement)

selected=[o for o in selected if o.type in ('MESH','EMPTY')]
ns['collection']('Web_prototypes')
white=ns['material']('Web_petal_base','#ffffff',.45,subsurface=.13)
prototypes={};ao_report={}
def bake_petal_ao(o,samples):
    bpy.context.view_layer.update();graph=bpy.context.evaluated_depsgraph_get()
    opened=bpy.data.meshes.new_from_object(o.evaluated_get(graph),preserve_all_data_layers=True,depsgraph=graph)
    points=[v.co.copy() for v in opened.vertices];tree=BVHTree.FromPolygons(points,[tuple(p.vertices) for p in opened.polygons])
    petal_vertices={i for p in o.data.polygons if p.material_index==0 for i in p.vertices}
    rgba=[1.0]*(len(o.data.vertices)*4);shades=[]
    for index in petal_vertices:
        n=opened.vertices[index].normal.normalized();reference=Vector((0,0,1)) if abs(n.z)<.95 else Vector((0,1,0));tangent=n.cross(reference).normalized();bitangent=n.cross(tangent);origin=points[index]+n*.0017;hits=0
        for j in range(samples):
            r=math.sqrt((j+.5)/samples);a=j*2.399963+index*.618
            direction=tangent*(r*math.cos(a))+bitangent*(r*math.sin(a))+n*math.sqrt(1-r*r)
            if tree.ray_cast(origin,direction,.55)[0] is not None:hits+=1
        shade=.30+.70*math.sqrt(1-hits/samples);rgba[index*4:index*4+4]=[shade,shade,shade,1];shades.append(shade)
    layer=o.data.color_attributes.new(name='AmbientOcclusion',type='FLOAT_COLOR',domain='POINT');layer.data.foreach_set('color',rgba)
    o.data.color_attributes.active_color_index=0;o.data.color_attributes.render_color_index=0
    bpy.data.meshes.remove(opened)
    return {'samples':samples,'vertices':len(shades),'min':min(shades),'mean':sum(shades)/len(shades),'max':max(shades)}
for kind,rose,detail in [('garden',False,0),('hero',False,2),('rose',True,0)]:
    o=ns['flower']('Web_'+kind,(0,0,0),1,white,0,rose,detail,0,True)
    o.animation_data_clear();o.data.shape_keys.animation_data_clear();o.scale=(1,1,1);o.data.shape_keys.key_blocks['Bloom'].value=1
    o['rtPrototype']=kind;o['rtCollection']='prototype';prototypes[kind]=o.name;selected.append(o)
    ao_report[kind]=bake_petal_ao(o,48 if kind=='hero' else 24)

bpy.ops.object.select_all(action='DESELECT')
for o in selected:o.select_set(True)
bpy.context.view_layer.update()
target=DEST/'garden.glb'
bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_selection=True,
    export_animations=False,export_current_frame=True,export_apply=False,
    export_yup=True,export_morph=True,export_morph_normal=True,export_materials='EXPORT',
    export_extras=True,export_cameras=False,export_lights=False,export_vertex_color='ACTIVE',export_meshopt_compression_enable=True)
manifest={'schema':'shahaf.browser-scene.v1','source':'blender/shahaf-garden/Shahaf_Garden_v001.blend',
    'authoringUnchanged':True,'prototypes':prototypes,'flowers':instances,'fireflies':fireflies,'lights':lights,'pivots':pivots,
    'coordinateSystem':'Y up; Blender (x,y,z) maps to (x,z,-y)',
    'materialLimitations':['Procedural noise/bump nodes need runtime equivalents.','Volume haze is recreated in the renderer.'],
    'staticAssetBytes':target.stat().st_size,'selectedObjects':len(selected),'petalAmbientOcclusion':ao_report}
(DEST/'garden-scene.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('SHAHAF_EXPORT '+json.dumps({'file':str(target),'bytes':target.stat().st_size,'objects':len(selected),'flowerInstances':len(instances)}),flush=True)
